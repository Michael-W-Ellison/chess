"""
Engagement Tracker
Learns which kinds of replies each child engages with

After every bot reply, the choices that went into it are kept as "pending" features
(for example: was a follow-up question added, was an old memory mentioned, which
template variant, was a pun added). When the child's next message arrives it is scored
for engagement (0.0-1.0) and the score is credited to those choices. Totals are stored
per child in the engagement_stats table, so learning carries across sessions.

The response engine then makes those choices with Thompson sampling: each option's
engagement rate is modeled as a Beta distribution whose prior comes from the bot's
personality (e.g. curiosity for follow-up questions), a value is sampled per option and
the highest wins. Options that engage this child get chosen more often, while weaker
ones are still tried now and then. Until an option has MIN_SAMPLES scores, the engine
keeps its original personality-only behavior.

Slow replies count for less, and after a long time the child is treated as having left.
The thresholds start at the ENGAGEMENT_SLOW_REPLY_SECONDS / ENGAGEMENT_AWAY_SECONDS
settings. Each child's reply delays are recorded (the last DELAY_HISTORY), and once there
are DELAY_MIN_SAMPLES of them, a reply only counts as slow if it is slower than
SLOW_PERCENTILE of the child's own replies, so a child who types slowly is not treated as
less engaged. The settings stay the minimum.
"""

import logging
import math
import random
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from models.engagement import EngagementStat, ReplyDelay
from utils.config import settings
from utils.bounded import BoundedDict

logger = logging.getLogger("chatbot.engagement_tracker")

MIN_SAMPLES = 5  # scores per option before learning overrides personality defaults
PRIOR_STRENGTH = 2.0  # how many "virtual" scores the personality prior is worth
SIGNAL_MIN_SAMPLES = 8  # scores per option before engagement nudges personality traits
LEFT_SCORE = 0.1  # the child left after the reply (conversation ended, or came back much later)
SLOWEST_REPLY_FACTOR = 0.6  # score factor for a reply that took just under the away threshold
DELAY_MIN_SAMPLES = 20  # reply delays before a child's own timing replaces the defaults
DELAY_HISTORY = 200  # most recent reply delays kept per child
SLOW_PERCENTILE = 0.9  # a reply slower than 90% of the child's own replies counts as slow
SIGNAL_MIN_DIFFERENCE = 0.1  # mean score difference that counts as a clear preference

_WORD_RE = re.compile(r"[a-z']+")
_DISMISSIVE = {"ok", "okay", "k", "kk", "idk", "whatever", "meh", "boring", "stop", "nothing",
               "hmm", "fine", "sure", "nah", "dunno", "bye", "lol"}
_YES_NO = {"yes", "yeah", "yep", "no", "nope", "maybe"}
_FAREWELLS = {"bye", "goodbye", "goodnight", "cya", "later", "gtg", "g2g", "night", "ttyl"}
_SHARING = {"because", "cause", "feel", "felt", "think", "favorite", "love", "wish", "remember"}
_STOPWORDS = {"the", "a", "an", "and", "or", "but", "to", "of", "in", "on", "at", "for", "with", "is",
              "was", "are", "were", "be", "it", "that", "this", "i", "you", "me", "my", "your", "we",
              "so", "do", "did", "what", "how", "about", "really", "too", "very", "just", "that's",
              "it's", "i'm", "you're", "tell", "more", "sounds", "like", "oh", "wow", "nice"}


@dataclass
class PendingReply:
    """A reply waiting for the child's next message"""

    text: str
    features: Dict[str, str]
    sent_at: datetime = field(default_factory=datetime.now)
    closing: bool = False  # the child had said goodbye, so ending here is not disengagement


def score_engagement(reply_text: str, next_message: str) -> float:
    """
    Score how engaged the child's next message is (0.0 = brushed off, 1.0 = very engaged)

    Signals: message length, answering the bot's question, staying on the bot's topic,
    asking the bot something back, and sharing feelings or reasons.
    """
    words = _WORD_RE.findall(next_message.lower())
    if not words:
        return 0.0

    asked = reply_text.rstrip().endswith("?") or "?" in reply_text
    if len(words) <= 2 and all(w in _YES_NO for w in words):
        return 0.35 if asked else 0.2
    if len(words) <= 2 and all(w in _DISMISSIVE for w in words):
        return 0.05

    score = 0.6 * min(len(words), 15) / 15
    reply_words = {w for w in _WORD_RE.findall(reply_text.lower()) if w not in _STOPWORDS}
    message_words = {w for w in words if w not in _STOPWORDS}
    if reply_words & message_words:
        score += 0.2  # stayed on the bot's topic
    if asked and len(words) >= 3:
        score += 0.1  # answered the question with more than a word or two
    if "?" in next_message:
        score += 0.15  # asked the bot something back
    if any(w in _SHARING for w in words):
        score += 0.1  # shared feelings or reasons
    return round(min(score, 1.0), 3)


@dataclass
class TimingThresholds:
    """Seconds after which a reply counts as slow, and after which the child has left"""

    slow: float
    away: float
    personalized: bool = False  # from the child's own reply delays rather than the settings


def default_thresholds() -> TimingThresholds:
    return TimingThresholds(slow=float(settings.ENGAGEMENT_SLOW_REPLY_SECONDS),
                            away=float(settings.ENGAGEMENT_AWAY_SECONDS))


def percentile(values: List[float], fraction: float) -> float:
    """Nearest-rank percentile: the smallest value at least `fraction` of the values are at or below"""
    ordered = sorted(values)
    return ordered[max(0, math.ceil(fraction * len(ordered)) - 1)]


def timing_thresholds(delays: List[float]) -> TimingThresholds:
    """
    A child's thresholds from their recent reply delays: slow is the child's SLOW_PERCENTILE
    delay, and away keeps the default ratio of away to slow. Neither goes below the settings.
    """
    defaults = default_thresholds()
    if len(delays) < DELAY_MIN_SAMPLES:
        return defaults
    slow = max(defaults.slow, percentile(delays, SLOW_PERCENTILE))
    away = max(defaults.away, slow * defaults.away / defaults.slow)
    return TimingThresholds(slow=slow, away=away, personalized=True)


def adjust_for_timing(score: float, seconds: Optional[float],
                      thresholds: Optional[TimingThresholds] = None) -> float:
    """
    Lower the score for slow replies: unchanged up to the slow threshold, then scaled down
    to SLOWEST_REPLY_FACTOR at the away threshold; after that the child is treated as having
    left. Without thresholds, the settings' defaults are used.
    """
    thresholds = thresholds or default_thresholds()
    if seconds is None or seconds <= thresholds.slow:
        return score
    if seconds >= thresholds.away:
        return LEFT_SCORE
    fraction = (seconds - thresholds.slow) / (thresholds.away - thresholds.slow)
    return round(score * (1.0 - fraction * (1.0 - SLOWEST_REPLY_FACTOR)), 3)


def is_farewell(message: str) -> bool:
    """A short goodbye ("bye!", "gtg, see you later")"""
    words = _WORD_RE.findall(message.lower())
    return 0 < len(words) <= 6 and (bool(_FAREWELLS & set(words)) or "see you" in message.lower())


class EngagementPolicy:
    """Chooses between reply options for one child, using their engagement stats"""

    def __init__(self, stats: Dict[Tuple[str, str], List[float]], rng: random.Random):
        self.stats = stats
        self.rng = rng

    def count(self, feature: str, arm: str) -> int:
        return int(self.stats.get((feature, arm), (0.0, 0))[1])

    def has_data(self, feature: str, arms: List[str]) -> bool:
        """True if every option has at least MIN_SAMPLES scores"""
        return all(self.count(feature, arm) >= MIN_SAMPLES for arm in arms)

    def sample(self, feature: str, arm: str, prior_mean: float = 0.5) -> float:
        """Draw a plausible engagement rate for one option (Thompson sampling)"""
        score_sum, count = self.stats.get((feature, arm), (0.0, 0))
        alpha = 1.0 + PRIOR_STRENGTH * prior_mean + score_sum
        beta = 1.0 + PRIOR_STRENGTH * (1.0 - prior_mean) + (count - score_sum)
        return self.rng.betavariate(alpha, beta)

    def decide(self, feature: str, probability: float) -> bool:
        """
        Yes/no choice: the personality-based probability until both options have enough
        data, then Thompson sampling with that probability as the prior
        """
        if self.has_data(feature, ["yes", "no"]):
            return self.choose(feature, {"yes": probability, "no": 1.0 - probability}) == "yes"
        return self.rng.random() < probability

    def choose(self, feature: str, priors: Dict[str, float]) -> str:
        """Pick the option with the highest sampled engagement rate"""
        return max(priors, key=lambda arm: self.sample(feature, arm, priors[arm]))

    def rank(self, feature: str, arms: List[str]) -> List[str]:
        """Options ordered by sampled engagement rate (unseen options get a neutral prior)"""
        samples = {arm: self.sample(feature, arm) for arm in arms}
        return sorted(arms, key=lambda arm: samples[arm], reverse=True)


class EngagementTracker:
    """Scores the child's responses to bot replies and keeps per-child statistics"""

    def __init__(self, rng: Optional[random.Random] = None):
        self.rng = rng or random.Random()
        self._pending: Dict[int, PendingReply] = BoundedDict()
        self._cache: Dict[int, Dict[Tuple[str, str], List[float]]] = BoundedDict()
        self._delays: Dict[int, List[float]] = BoundedDict()  # recent reply delays, oldest first

    # ------------------------------------------------------------------
    # Turn handling
    # ------------------------------------------------------------------

    def set_pending(self, user_id: int, reply_text: str, features: Dict[str, str],
                    child_message: str = "") -> None:
        """Remember the reply just sent, the choices it contained, and whether it was a goodbye"""
        if features:
            closing = is_farewell(child_message) or features.get("rule") == "farewell"
            self._pending[user_id] = PendingReply(text=reply_text, features=dict(features), closing=closing)
        else:
            self._pending.pop(user_id, None)

    def discard_pending(self, user_id: int) -> None:
        """Drop the pending reply without scoring it (e.g. the next message was a crisis)"""
        self._pending.pop(user_id, None)

    def record_response(self, user_id: int, message: str, db: Session,
                        now: Optional[datetime] = None) -> Optional[float]:
        """
        Score the child's message against the pending reply and credit the reply's choices.
        The score is lowered if the child took long to reply (see adjust_for_timing), judged
        by this child's thresholds; the delay is then recorded unless the child had left.

        Returns:
            The engagement score, or None if there was no pending reply
        """
        pending = self._pending.pop(user_id, None)
        if pending is None:
            return None

        seconds = ((now or datetime.now()) - pending.sent_at).total_seconds()
        thresholds = self.thresholds(user_id, db)
        score = adjust_for_timing(score_engagement(pending.text, message), seconds, thresholds)
        if seconds < thresholds.away:
            # A return after the child had left says nothing about how fast they reply
            self._record_delay(user_id, seconds, db)
        self._credit(user_id, pending, score, db)
        return score

    def record_conversation_end(self, user_id: int, db: Session) -> Optional[float]:
        """
        The conversation ended after the bot's reply without an answer from the child.
        Unless the child had said goodbye, that reply gets LEFT_SCORE.

        Returns:
            The score credited, or None if nothing was credited
        """
        pending = self._pending.pop(user_id, None)
        if pending is None or pending.closing:
            return None
        self._credit(user_id, pending, LEFT_SCORE, db)
        return LEFT_SCORE

    def _credit(self, user_id: int, pending: PendingReply, score: float, db: Session) -> None:
        """Add a score to every choice the pending reply contained"""
        stats = self._stats(user_id, db)
        for feature, arm in pending.features.items():
            row = (
                db.query(EngagementStat)
                .filter(EngagementStat.user_id == user_id,
                        EngagementStat.feature == feature,
                        EngagementStat.arm == arm)
                .first()
            )
            if row is None:
                row = EngagementStat(user_id=user_id, feature=feature, arm=arm)
                db.add(row)
            row.score_sum += score
            row.count += 1
            entry = stats.setdefault((feature, arm), [0.0, 0])
            entry[0] += score
            entry[1] += 1
        db.commit()
        logger.debug(f"Engagement {score:.2f} for user {user_id}: {pending.features}")

    # ------------------------------------------------------------------
    # Reply timing
    # ------------------------------------------------------------------

    def _recent_delays(self, user_id: int, db: Optional[Session]) -> List[float]:
        if user_id not in self._delays:
            delays: List[float] = []
            if db is not None:
                rows = (db.query(ReplyDelay.seconds).filter(ReplyDelay.user_id == user_id)
                        .order_by(ReplyDelay.id.desc()).limit(DELAY_HISTORY).all())
                delays = [row.seconds for row in reversed(rows)]
            self._delays[user_id] = delays
        return self._delays[user_id]

    def _record_delay(self, user_id: int, seconds: float, db: Session) -> None:
        """Store a reply delay and drop the child's delays beyond the last DELAY_HISTORY"""
        delays = self._recent_delays(user_id, db)
        db.add(ReplyDelay(user_id=user_id, seconds=seconds))
        delays.append(seconds)
        del delays[:-DELAY_HISTORY]
        db.flush()
        stale = [row.id for row in db.query(ReplyDelay.id).filter(ReplyDelay.user_id == user_id)
                 .order_by(ReplyDelay.id.desc()).offset(DELAY_HISTORY).all()]
        if stale:
            db.query(ReplyDelay).filter(ReplyDelay.id.in_(stale)).delete(synchronize_session=False)
        # Committed together with the engagement scores in _credit

    def thresholds(self, user_id: int, db: Optional[Session]) -> TimingThresholds:
        """This child's slow and away thresholds"""
        return timing_thresholds(self._recent_delays(user_id, db))

    def timing_summary(self, user_id: int, db: Session) -> Dict:
        """The child's recent reply delays and thresholds, for display or tuning the defaults"""
        delays = self._recent_delays(user_id, db)
        thresholds = self.thresholds(user_id, db)
        return {
            "samples": len(delays),
            "median_seconds": round(percentile(delays, 0.5), 1) if delays else None,
            "p90_seconds": round(percentile(delays, 0.9), 1) if delays else None,
            "slow_after_seconds": round(thresholds.slow, 1),
            "away_after_seconds": round(thresholds.away, 1),
            "personalized": thresholds.personalized,
        }

    # ------------------------------------------------------------------
    # Stats and policy
    # ------------------------------------------------------------------

    def _stats(self, user_id: int, db: Optional[Session]) -> Dict[Tuple[str, str], List[float]]:
        if user_id not in self._cache:
            stats: Dict[Tuple[str, str], List[float]] = {}
            if db is not None:
                for row in db.query(EngagementStat).filter(EngagementStat.user_id == user_id):
                    stats[(row.feature, row.arm)] = [row.score_sum, row.count]
            self._cache[user_id] = stats
        return self._cache[user_id]

    def policy(self, user_id: int, db: Optional[Session]) -> EngagementPolicy:
        return EngagementPolicy(self._stats(user_id, db), self.rng)

    def forget_cache(self, user_id: Optional[int] = None) -> None:
        """Drop cached stats and delays so they are reloaded from the database"""
        if user_id is None:
            self._cache.clear()
            self._delays.clear()
        else:
            self._cache.pop(user_id, None)
            self._delays.pop(user_id, None)

    def trait_signals(self, user_id: int, db: Session) -> Dict[str, Tuple[int, str]]:
        """
        Clear engagement preferences that should nudge personality traits

        Returns:
            {trait: (direction, reason)} with direction +1 or -1, e.g.
            {"curiosity": (1, "Child engages more after follow-up questions (0.62 vs 0.41)")}
        """
        stats = self._stats(user_id, db)
        signals = {}
        comparisons = [
            # trait, (feature, arms counted as "with"), (feature, arm counted as "without")
            ("curiosity", ("follow_up", ["yes"]), ("follow_up", "no"), "after follow-up questions"),
            ("humor", ("humor", ["pun", "fact"]), ("humor", "none"), "after jokes and fun facts"),
        ]
        for trait, (feature, with_arms), without_key, description in comparisons:
            with_stats = _combine(*(stats.get((feature, arm)) for arm in with_arms))
            without_stats = stats.get(without_key)
            if not with_stats or not without_stats:
                continue
            if with_stats[1] < SIGNAL_MIN_SAMPLES or without_stats[1] < SIGNAL_MIN_SAMPLES:
                continue
            with_mean = with_stats[0] / with_stats[1]
            without_mean = without_stats[0] / without_stats[1]
            difference = with_mean - without_mean
            if abs(difference) < SIGNAL_MIN_DIFFERENCE:
                continue
            direction = 1 if difference > 0 else -1
            comparison = "more" if direction > 0 else "less"
            signals[trait] = (
                direction,
                f"Child engages {comparison} {description} ({with_mean:.2f} vs {without_mean:.2f})",
            )
        return signals

    def summary(self, user_id: int, db: Session) -> List[Dict]:
        """All engagement stats for a child, for display or debugging"""
        rows = db.query(EngagementStat).filter(EngagementStat.user_id == user_id).all()
        return [row.to_dict() for row in sorted(rows, key=lambda r: (r.feature, r.arm))]


def _combine(*entries) -> Optional[List[float]]:
    present = [e for e in entries if e]
    if not present:
        return None
    return [sum(e[0] for e in present), sum(e[1] for e in present)]


# Global instance
engagement_tracker = EngagementTracker()
