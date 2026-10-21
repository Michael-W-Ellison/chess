"""
Tests for engagement learning (services/engagement_tracker.py) and its use in replies
and personality drift
"""

import random
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from models.engagement import EngagementStat
from models.personality import BotPersonality
from models.conversation import Conversation
from models.user import User
from services.engagement_tracker import (
    MIN_SAMPLES,
    SIGNAL_MIN_SAMPLES,
    EngagementPolicy,
    EngagementTracker,
    score_engagement,
)
from services.utterance_parser import UtteranceParser

needs_parser = pytest.mark.skipif(
    not UtteranceParser().is_available(), reason="spaCy model en_core_web_sm not installed"
)


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add(User(id=1, name="Sam"))
    session.commit()
    yield session
    session.close()


@pytest.fixture
def tracker():
    return EngagementTracker(rng=random.Random(0))


def policy_with(stats):
    """Policy from {(feature, arm): (mean score, count)}"""
    return EngagementPolicy({key: [mean * count, count] for key, (mean, count) in stats.items()},
                            random.Random(0))


class TestScoring:
    def test_brush_off_scores_low(self):
        for message in ["ok", "idk", "whatever", "k", "meh"]:
            assert score_engagement("What was the best part?", message) <= 0.05

    def test_long_on_topic_answer_scores_high(self):
        score = score_engagement(
            "You went to the zoo? What was the best part?",
            "The giraffes at the zoo were the best because they ate leaves right out of my hand",
        )
        assert score >= 0.8

    def test_yes_to_a_question_scores_more_than_unprompted_yes(self):
        assert score_engagement("Do you like it?", "yes") > score_engagement("That's cool.", "yes")

    def test_staying_on_topic_adds_to_score(self):
        on_topic = score_engagement("Tell me about soccer!", "soccer practice was long")
        off_topic = score_engagement("Tell me about soccer!", "my cat sleeps a lot")
        assert on_topic > off_topic

    def test_asking_back_adds_to_score(self):
        assert score_engagement("I like pizza!", "what toppings do you like?") > \
            score_engagement("I like pizza!", "what toppings do you like")

    def test_scores_are_between_0_and_1(self):
        long_message = " ".join(["because I feel"] * 30) + "?"
        assert 0.0 <= score_engagement("Why?", long_message) <= 1.0
        assert score_engagement("Hi!", "") == 0.0


class TestRecording:
    def test_no_pending_reply_records_nothing(self, tracker, db):
        assert tracker.record_response(1, "hello there", db) is None
        assert db.query(EngagementStat).count() == 0

    def test_score_is_credited_to_each_choice(self, tracker, db):
        tracker.set_pending(1, "Cool! What was the best part?", {"follow_up": "yes", "rule": "evaluation"})
        score = tracker.record_response(1, "the best part was the slide at the water park", db)

        rows = {(r.feature, r.arm): r for r in db.query(EngagementStat).all()}
        assert set(rows) == {("follow_up", "yes"), ("rule", "evaluation")}
        assert rows[("follow_up", "yes")].count == 1
        assert rows[("follow_up", "yes")].score_sum == pytest.approx(score)

    def test_totals_accumulate(self, tracker, db):
        for message in ["ok", "it was really fun and I want to go again"]:
            tracker.set_pending(1, "How was it?", {"follow_up": "yes"})
            tracker.record_response(1, message, db)
        row = db.query(EngagementStat).one()
        assert row.count == 2

    def test_pending_is_used_once(self, tracker, db):
        tracker.set_pending(1, "How was it?", {"follow_up": "yes"})
        tracker.record_response(1, "good", db)
        assert tracker.record_response(1, "good", db) is None

    def test_discarded_reply_is_not_scored(self, tracker, db):
        tracker.set_pending(1, "How was it?", {"follow_up": "yes"})
        tracker.discard_pending(1)
        assert tracker.record_response(1, "good", db) is None

    def test_stats_are_loaded_from_the_database(self, tracker, db):
        db.add(EngagementStat(user_id=1, feature="follow_up", arm="yes", score_sum=4.0, count=8))
        db.commit()
        fresh = EngagementTracker()
        assert fresh.policy(1, db).count("follow_up", "yes") == 8


class TestPolicy:
    def test_needs_minimum_samples_for_every_option(self):
        policy = policy_with({("follow_up", "yes"): (0.8, MIN_SAMPLES), ("follow_up", "no"): (0.2, MIN_SAMPLES - 1)})
        assert not policy.has_data("follow_up", ["yes", "no"])

    def test_choose_prefers_the_more_engaging_option(self):
        policy = policy_with({("follow_up", "yes"): (0.8, 30), ("follow_up", "no"): (0.2, 30)})
        choices = [policy.choose("follow_up", {"yes": 0.5, "no": 0.5}) for _ in range(200)]
        assert choices.count("yes") > 180

    def test_weaker_option_is_still_tried_with_little_data(self):
        policy = policy_with({("follow_up", "yes"): (0.6, MIN_SAMPLES), ("follow_up", "no"): (0.4, MIN_SAMPLES)})
        choices = [policy.choose("follow_up", {"yes": 0.5, "no": 0.5}) for _ in range(200)]
        assert 0 < choices.count("no") < choices.count("yes")


class TestTraitSignals:
    def add(self, db, feature, arm, mean, count):
        db.add(EngagementStat(user_id=1, feature=feature, arm=arm, score_sum=mean * count, count=count))
        db.commit()

    def test_clear_preference_gives_signal(self, tracker, db):
        self.add(db, "follow_up", "yes", 0.7, SIGNAL_MIN_SAMPLES)
        self.add(db, "follow_up", "no", 0.3, SIGNAL_MIN_SAMPLES)
        assert tracker.trait_signals(1, db)["curiosity"][0] == 1

    def test_jokes_combine_puns_and_facts(self, tracker, db):
        self.add(db, "humor", "pun", 0.2, SIGNAL_MIN_SAMPLES // 2)
        self.add(db, "humor", "fact", 0.2, SIGNAL_MIN_SAMPLES // 2)
        self.add(db, "humor", "none", 0.6, SIGNAL_MIN_SAMPLES)
        assert tracker.trait_signals(1, db)["humor"][0] == -1

    def test_small_difference_gives_no_signal(self, tracker, db):
        self.add(db, "follow_up", "yes", 0.52, SIGNAL_MIN_SAMPLES)
        self.add(db, "follow_up", "no", 0.48, SIGNAL_MIN_SAMPLES)
        assert tracker.trait_signals(1, db) == {}

    def test_too_few_samples_gives_no_signal(self, tracker, db):
        self.add(db, "follow_up", "yes", 0.9, SIGNAL_MIN_SAMPLES - 1)
        self.add(db, "follow_up", "no", 0.1, SIGNAL_MIN_SAMPLES)
        assert tracker.trait_signals(1, db) == {}


class TestPersonalityDrift:
    def make_personality(self, db, curiosity):
        personality = BotPersonality(user_id=1, name="Buddy", humor=0.5, energy=0.5,
                                     curiosity=curiosity, formality=0.3)
        conversation = Conversation(user_id=1, message_count=0)
        db.add_all([personality, conversation])
        db.commit()
        return personality, conversation

    @pytest.mark.parametrize("direction", [1, -1])
    def test_engagement_signal_moves_curiosity(self, db, direction):
        from services.personality_drift_calculator import personality_drift_calculator

        personality, conversation = self.make_personality(db, curiosity=0.5)
        signal = {"curiosity": (direction, "test signal")}
        with patch("services.engagement_tracker.engagement_tracker.trait_signals", return_value=signal):
            personality_drift_calculator.calculate_drift_after_conversation(personality, conversation, db)
        assert (personality.curiosity - 0.5) * direction > 0

    def test_no_drift_past_the_upper_margin(self, db):
        from services.personality_drift_calculator import personality_drift_calculator

        personality, conversation = self.make_personality(db, curiosity=0.95)
        with patch("services.engagement_tracker.engagement_tracker.trait_signals",
                   return_value={"curiosity": (1, "test signal")}):
            personality_drift_calculator.calculate_drift_after_conversation(personality, conversation, db)
        assert personality.curiosity == pytest.approx(0.95)


@needs_parser
class TestEngineUsesPolicy:
    @pytest.fixture
    def engine(self):
        from services.response_engine import ResponseEngine
        return ResponseEngine(rng=random.Random(0))

    @staticmethod
    def personality(curiosity):
        return SimpleNamespace(id=1, user_id=1, name="Buddy", mood="happy", friendship_level=1,
                               energy=0.7, curiosity=curiosity, formality=0.3, get_interests=lambda: [])

    def follow_up_rate(self, engine, curiosity, policy):
        asked = 0
        for _ in range(60):
            features = {}
            engine.generate_response("I won my soccer game today", self.personality(curiosity),
                                     policy=policy, features=features)
            asked += features.get("follow_up") == "yes"
        return asked / 60

    def test_features_are_recorded(self, engine):
        features = {}
        engine.generate_response("I won my soccer game today", self.personality(1.0), features=features)
        assert features["rule"] == "achievement"
        assert features["follow_up"] == "yes"
        assert "template:achievement" in features

    def test_fallback_features_are_recorded(self, engine):
        features = {}
        engine.generate_response("We went to the zoo", self.personality(0.5), features=features)
        assert features["rule"] == "fallback_reflection"
        assert "template:fallback_reflection" in features

    def test_learning_overrides_curiosity_for_this_child(self, engine):
        dislikes_questions = policy_with({("follow_up", "yes"): (0.1, 30), ("follow_up", "no"): (0.7, 30)})
        assert self.follow_up_rate(engine, curiosity=1.0, policy=None) == 1.0
        assert self.follow_up_rate(engine, curiosity=1.0, policy=dislikes_questions) < 0.2

    def test_without_enough_data_curiosity_decides(self, engine):
        little_data = policy_with({("follow_up", "yes"): (0.1, 2), ("follow_up", "no"): (0.7, 2)})
        assert self.follow_up_rate(engine, curiosity=1.0, policy=little_data) == 1.0

    def test_learned_template_preference(self, engine):
        from services.response_engine import template_id

        templates = engine.kb["fallbacks"]["reflection"]
        favorite = template_id(templates[0])
        stats = {("template:fallback_reflection", template_id(t)): (0.9 if template_id(t) == favorite else 0.1, 30)
                 for t in templates}
        policy = policy_with(stats)
        chosen = []
        for _ in range(30):
            features = {}
            engine.generate_response("We went to the zoo", self.personality(0.0), policy=policy, features=features)
            chosen.append(features["template:fallback_reflection"])
        # Never repeated back to back, and the favorite is used whenever it was not just used
        assert all(a != b for a, b in zip(chosen, chosen[1:]))
        assert chosen.count(favorite) >= 14


def test_parent_engagement_endpoint(client):
    from database.database import init_db

    init_db()  # the client fixture does not run app startup, which creates the tables
    response = client.get("/api/parent/engagement?user_id=1")
    assert response.status_code == 200
    assert response.json()["user_id"] == 1
    assert isinstance(response.json()["stats"], list)
    assert response.json()["reply_timing"]["slow_after_seconds"] == 120


class TestTiming:
    @pytest.mark.parametrize("seconds,expected", [
        (None, 0.8), (30, 0.8), (120, 0.8), (15 * 60, 0.1), (60 * 60, 0.1),
    ])
    def test_adjust_for_timing(self, seconds, expected):
        from services.engagement_tracker import adjust_for_timing
        assert adjust_for_timing(0.8, seconds) == pytest.approx(expected)

    def test_slow_reply_counts_for_less(self):
        from services.engagement_tracker import adjust_for_timing, SLOWEST_REPLY_FACTOR
        just_before_away = adjust_for_timing(1.0, 15 * 60 - 1)
        assert SLOWEST_REPLY_FACTOR <= just_before_away < 0.61
        assert 0.6 < adjust_for_timing(1.0, 8 * 60) < 1.0

    def test_record_response_uses_reply_time(self, tracker, db):
        from datetime import datetime, timedelta
        message = "the best part was the slide at the water park"
        tracker.set_pending(1, "What was the best part?", {"follow_up": "yes"})
        quick = tracker.record_response(1, message, db, now=datetime.now() + timedelta(seconds=20))
        tracker.set_pending(1, "What was the best part?", {"follow_up": "yes"})
        late = tracker.record_response(1, message, db, now=datetime.now() + timedelta(minutes=30))
        assert quick > 0.5
        assert late == pytest.approx(0.1)


class TestPersonalTiming:
    def reply_after(self, tracker, db, seconds, message="the best part was the slide at the water park"):
        from datetime import datetime, timedelta
        tracker.set_pending(1, "What was the best part?", {"follow_up": "yes"})
        return tracker.record_response(1, message, db, now=datetime.now() + timedelta(seconds=seconds))

    def test_defaults_until_enough_delays(self, tracker, db):
        from services.engagement_tracker import DELAY_MIN_SAMPLES
        for _ in range(DELAY_MIN_SAMPLES - 1):
            self.reply_after(tracker, db, 300)
        thresholds = tracker.thresholds(1, db)
        assert (thresholds.slow, thresholds.away, thresholds.personalized) == (120, 900, False)

    def test_slow_typer_gets_higher_thresholds(self, tracker, db):
        from services.engagement_tracker import DELAY_MIN_SAMPLES
        for index in range(DELAY_MIN_SAMPLES):
            self.reply_after(tracker, db, 200 + index * 10)  # 200s to 390s
        thresholds = tracker.thresholds(1, db)
        assert thresholds.personalized
        assert thresholds.slow == pytest.approx(370)  # 90th percentile
        assert thresholds.away == pytest.approx(370 * 900 / 120)
        # A 5-minute reply is normal for this child, not slow
        fast = score_engagement("What was the best part?", "the best part was the slide at the water park")
        assert self.reply_after(tracker, db, 300) == pytest.approx(fast)

    def test_fast_typer_keeps_the_defaults_as_minimum(self, tracker, db):
        from services.engagement_tracker import DELAY_MIN_SAMPLES
        for _ in range(DELAY_MIN_SAMPLES):
            self.reply_after(tracker, db, 5)
        thresholds = tracker.thresholds(1, db)
        assert (thresholds.slow, thresholds.away) == (120, 900)
        assert thresholds.personalized

    def test_settings_change_the_defaults(self, tracker, db):
        with patch("utils.config.settings.ENGAGEMENT_SLOW_REPLY_SECONDS", 60), \
                patch("utils.config.settings.ENGAGEMENT_AWAY_SECONDS", 600):
            thresholds = tracker.thresholds(1, db)
        assert (thresholds.slow, thresholds.away) == (60, 600)

    def test_return_after_leaving_is_not_recorded(self, tracker, db):
        from models.engagement import ReplyDelay
        self.reply_after(tracker, db, 30)
        self.reply_after(tracker, db, 60 * 60)
        assert [row.seconds for row in db.query(ReplyDelay)] == [pytest.approx(30, abs=1)]

    def test_only_recent_delays_are_kept(self, tracker, db):
        from models.engagement import ReplyDelay
        with patch("services.engagement_tracker.DELAY_HISTORY", 5):
            for seconds in range(10, 80, 10):
                self.reply_after(tracker, db, seconds)
            db.commit()
            assert db.query(ReplyDelay).count() == 5
            assert tracker._recent_delays(1, db) == pytest.approx([30, 40, 50, 60, 70], abs=1)

    def test_delays_survive_a_restart(self, db):
        from services.engagement_tracker import DELAY_MIN_SAMPLES
        first = EngagementTracker(rng=random.Random(0))
        for _ in range(DELAY_MIN_SAMPLES):
            self.reply_after(first, db, 400)
        restarted = EngagementTracker(rng=random.Random(0))
        assert restarted.thresholds(1, db).slow == pytest.approx(400, abs=1)

    def test_timing_summary(self, tracker, db):
        assert tracker.timing_summary(1, db)["samples"] == 0
        assert tracker.timing_summary(1, db)["median_seconds"] is None
        for seconds in (10, 20, 30):
            self.reply_after(tracker, db, seconds)
        summary = tracker.timing_summary(1, db)
        assert summary["samples"] == 3
        assert summary["median_seconds"] == pytest.approx(20, abs=1)
        assert summary["personalized"] is False

    @pytest.mark.parametrize("values,fraction,expected", [
        ([5], 0.9, 5), ([1, 2, 3, 4], 0.5, 2), (list(range(1, 11)), 0.9, 9), ([3, 1, 2], 1.0, 3),
    ])
    def test_percentile(self, values, fraction, expected):
        from services.engagement_tracker import percentile
        assert percentile(values, fraction) == expected


class TestLeaving:
    def test_conversation_end_after_reply_scores_left(self, tracker, db):
        from services.engagement_tracker import LEFT_SCORE
        tracker.set_pending(1, "What was the best part?", {"follow_up": "yes"}, "We went to the zoo")
        assert tracker.record_conversation_end(1, db) == LEFT_SCORE
        assert db.query(EngagementStat).one().score_sum == pytest.approx(LEFT_SCORE)

    @pytest.mark.parametrize("message", ["bye!", "gtg, see you later", "goodnight"])
    def test_goodbye_is_not_leaving(self, tracker, db, message):
        tracker.set_pending(1, "See you later!", {"rule": "greeting"}, message)
        assert tracker.record_conversation_end(1, db) is None
        assert db.query(EngagementStat).count() == 0

    def test_farewell_rule_is_not_leaving(self, tracker, db):
        tracker.set_pending(1, "Bye, Sam!", {"rule": "farewell"})
        assert tracker.record_conversation_end(1, db) is None

    def test_nothing_pending(self, tracker, db):
        assert tracker.record_conversation_end(1, db) is None

    @pytest.mark.parametrize("message,expected", [
        ("bye", True), ("ok bye", True), ("see you tomorrow", True),
        ("I said bye to my friend after school today and then went home", False), ("hello", False),
    ])
    def test_is_farewell(self, message, expected):
        from services.engagement_tracker import is_farewell
        assert is_farewell(message) is expected


class TestDecide:
    def test_uses_probability_without_data(self):
        policy = EngagementPolicy({}, random.Random(0))
        assert all(policy.decide("follow_up", 1.0) for _ in range(20))
        assert not any(policy.decide("follow_up", 0.0) for _ in range(20))

    def test_uses_learned_data(self):
        policy = policy_with({("follow_up", "yes"): (0.1, 30), ("follow_up", "no"): (0.8, 30)})
        assert sum(policy.decide("follow_up", 1.0) for _ in range(100)) < 20


@needs_parser
class TestTwoTemplateRules:
    def test_learned_preference_applies_to_two_template_rules(self):
        from services.response_engine import ResponseEngine, template_id
        engine = ResponseEngine(rng=random.Random(0))
        templates = engine.rules["bad_result"]["responses"]
        assert len(templates) == 2
        favorite = template_id(templates[1])
        policy = policy_with({("template:bad_result", template_id(t)): (0.9 if template_id(t) == favorite else 0.1, 30)
                              for t in templates})
        personality = TestEngineUsesPolicy.personality(0.0)
        chosen = []
        for _ in range(10):
            features = {}
            engine.generate_response("I got a bad grade", personality, policy=policy, features=features)
            chosen.append(features["template:bad_result"])
            engine.generate_response("hi", personality)  # another reply in between
        assert chosen == [favorite] * 10


class TestLLMReplies:
    @pytest.fixture
    def manager(self):
        from services.conversation_manager import ConversationManager
        return ConversationManager()

    @staticmethod
    def personality(curiosity=0.5, level=1):
        from unittest.mock import Mock
        personality = Mock()
        personality.user_id = 1
        personality.curiosity = curiosity
        personality.friendship_level = level
        return personality

    def test_plan_follows_curiosity_without_data(self, manager, db):
        assert manager._plan_llm_reply({}, self.personality(curiosity=1.0), db)["follow_up"] is True
        assert manager._plan_llm_reply({}, self.personality(curiosity=0.0), db)["follow_up"] is False

    def test_plan_uses_learned_data(self, manager, db):
        db.add_all([EngagementStat(user_id=1, feature="follow_up", arm="yes", score_sum=3.0, count=30),
                    EngagementStat(user_id=1, feature="follow_up", arm="no", score_sum=24.0, count=30)])
        db.commit()
        from services.engagement_tracker import engagement_tracker
        engagement_tracker.forget_cache(1)
        try:
            plans = [manager._plan_llm_reply({}, self.personality(curiosity=1.0), db)["follow_up"] for _ in range(50)]
        finally:
            engagement_tracker.forget_cache(1)
        assert sum(plans) < 15

    def test_callback_planned_only_with_memories_and_level_3(self, manager, db):
        memories = {"relevant_memories": [SimpleNamespace(value="soccer")]}
        assert "callback" not in manager._plan_llm_reply(memories, self.personality(level=2), db)
        assert "callback" in manager._plan_llm_reply(memories, self.personality(level=3), db)
        assert "callback" not in manager._plan_llm_reply({}, self.personality(level=3), db)

    def test_observed_features_come_from_the_reply(self, manager):
        context = {"relevant_memories": [SimpleNamespace(value="soccer")]}
        observed = manager._observed_llm_features(
            "Cool! Do you still play soccer?", context, {"follow_up": False, "callback": True})
        assert observed == {"rule": "llm", "follow_up": "yes", "callback": "yes"}
        observed = manager._observed_llm_features("That's great.", context, {"follow_up": True, "callback": False})
        assert observed == {"rule": "llm", "follow_up": "no", "callback": "no"}
