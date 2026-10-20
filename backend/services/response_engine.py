"""
Rule-Based Response Engine
Generates replies without an LLM by matching structural rules against a dependency parse

Pipeline:
1. Parse the message (services/utterance_parser.py)
2. Match the rules in knowledge/conversation_rules.json against the parse tree
   (spaCy DependencyMatcher patterns over node attributes and relations)
3. Build a frame per match: bind tree nodes to named slots, check conditions,
   and collect memory writes, mood and valence
4. Compose a reply from the highest-priority frame: choose a template variant,
   fill its slots (converted to the bot's perspective: "my" -> "your"), and shape it
   with the bot's personality (energy, formality, curiosity) and friendship level
5. Fall back to question/reflection/topic/generic replies when no rule matches
"""

import json
import logging
import random
import re
import zlib
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from services.reference_tracker import ReferenceTracker
from services.utterance_parser import utterance_parser

logger = logging.getLogger("chatbot.response_engine")

RULES_PATH = Path(__file__).resolve().parent.parent / "knowledge" / "conversation_rules.json"

# First person (child) <-> second person (bot) when echoing the child's words
_REFLECT_WORDS = {
    "i": "you", "me": "you", "my": "your", "mine": "yours", "myself": "yourself",
    "we": "you", "us": "you", "our": "your", "ours": "yours", "ourselves": "yourselves",
    "your": "my", "yours": "mine", "yourself": "myself",
    "am": "are", "'m": "'re",
}

_QUESTION_STARTERS = {"what", "who", "where", "when", "why", "how", "which", "do", "does", "did",
                      "are", "is", "can", "could", "would", "will", "should", "have", "has"}

# Interjections ("um", "oh") are dropped from echoed phrases; punctuation is trimmed only at the ends
_SKIP_DEPS = {"intj"}
_TRIM_DEPS = {"punct", "cc"}

# Chance of mentioning a stored memory (friendship level 3+) before engagement data exists
CALLBACK_PROBABILITY = 0.35

# A second sentence in the same message gets its own reply only for substantive rules
# (not greetings, thanks or low-priority memory-only matches)
SECOND_REPLY_MIN_PRIORITY = 50


@dataclass
class Frame:
    """A structural rule match with its bound slots"""

    rule_id: str
    priority: int
    slots: Dict[str, str]
    memories: List[Tuple[str, str, str]] = field(default_factory=list)
    mood: Optional[str] = None
    valence: str = "neutral"
    sentence: int = 0
    rule: Dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass
class Analysis:
    """Result of analyzing one message"""

    frames: List[Frame]
    is_question: bool  # whether the last sentence is a question
    mood: Optional[str]
    doc: Any = field(default=None, repr=False)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:50]


def template_id(template: str) -> str:
    """Short stable identifier for a template, used to key its engagement statistics"""
    return format(zlib.crc32(template.encode("utf-8")), "08x")


def _stable_index(seed: str, size: int) -> int:
    """Deterministic choice so the bot's own preferences stay the same across sessions"""
    return zlib.crc32(seed.encode("utf-8")) % size


class _BlankDict(dict):
    def __missing__(self, key):
        return ""


class ResponseEngine:
    """Structural rule matcher and reply composer"""

    def __init__(self, rules_path: Path = RULES_PATH, parser=utterance_parser, rng: Optional[random.Random] = None):
        self.parser = parser
        self.rules_path = rules_path
        self.rng = rng or random.Random()
        self.kb: Dict[str, Any] = {}
        self.rules: Dict[str, Dict[str, Any]] = {}
        self._matcher = None
        self._pattern_nodes: Dict[str, List[str]] = {}
        self._recent: Dict[int, deque] = defaultdict(lambda: deque(maxlen=8))
        self._last_request: Dict[int, str] = {}
        self._load_knowledge_base()
        self.references = ReferenceTracker(
            parser, self.kb["lexicons"]["relations"], self.kb["lexicons"]["common_capitalized"]
        )

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _load_knowledge_base(self) -> None:
        with open(self.rules_path, encoding="utf-8") as f:
            self.kb = json.load(f)
        lexicons = self.kb.get("lexicons", {})

        def resolve(value):
            if isinstance(value, str) and value.startswith("@"):
                return lexicons[value[1:]]
            if isinstance(value, dict):
                return {k: resolve(v) for k, v in value.items()}
            if isinstance(value, list):
                return [resolve(v) for v in value]
            return value

        for rule in self.kb.get("rules", []):
            rule["patterns"] = resolve(rule["patterns"])
            self.rules[rule["id"]] = rule

    def is_available(self) -> bool:
        """True if the parser (spaCy and its model) is available"""
        return self.parser.is_available()

    def resolve_references(self, message: str, user_id: int) -> str:
        """
        Replace pronouns ("she", "it") with the people and things they refer to from earlier
        turns, and remember what this message mentions. Call once per message, before
        analysis; pass the result to extract_memories, detect_mood and generate_response.
        """
        if not self.is_available():
            return message
        return self.references.resolve(message, user_id)

    def reset_references(self, user_id: int) -> None:
        """Forget earlier people and things (new conversation)"""
        self.references.reset(user_id)

    def _get_matcher(self):
        if self._matcher is None:
            from spacy.matcher import DependencyMatcher

            matcher = DependencyMatcher(self.parser.vocab)
            for rule_id, rule in self.rules.items():
                for index, pattern in enumerate(rule["patterns"]):
                    key = f"{rule_id}#{index}"
                    matcher.add(key, [pattern])
                    self._pattern_nodes[key] = [node["RIGHT_ID"] for node in pattern]
            self._matcher = matcher
        return self._matcher

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def analyze(self, message: str) -> Optional[Analysis]:
        """Parse a message and match all structural rules against it"""
        doc = self.parser.parse(message)
        if doc is None:
            return None

        sentences = list(doc.sents)
        is_question = self._is_question(sentences[-1]) if sentences else False
        frames: List[Frame] = []
        seen_rules = set()

        for match_id, token_ids in self._get_matcher()(doc):
            key = self.parser.vocab.strings[match_id]
            rule_id = key.split("#")[0]
            if rule_id in seen_rules:
                continue
            nodes = dict(zip(self._pattern_nodes[key], (doc[i] for i in token_ids)))
            frame = self._build_frame(self.rules[rule_id], nodes, doc)
            if frame is not None:
                frames.append(frame)
                seen_rules.add(rule_id)

        matched = {f.rule_id for f in frames}
        frames = [f for f in frames if not matched.intersection(f.rule.get("suppressed_by", []))]
        frames.sort(key=lambda f: f.priority, reverse=True)
        mood = next((f.mood for f in frames if f.mood), None)
        return Analysis(frames=frames, is_question=is_question, mood=mood, doc=doc)

    @staticmethod
    def _is_question(span) -> bool:
        """Question if the sentence ends with "?" or starts with a question word"""
        text = span.text.strip()
        return text.endswith("?") or (len(span) > 0 and span[0].lower_ in _QUESTION_STARTERS)

    def _build_frame(self, rule: Dict[str, Any], nodes: Dict[str, Any], doc) -> Optional[Frame]:
        conditions = rule.get("conditions", {})
        slots: Dict[str, str] = {}
        mood = rule.get("mood")
        valence = rule.get("valence", "neutral")
        sentence = next(iter(nodes.values())).sent

        # Lets templates distinguish "it will be hard" from "it was hard"
        if any(t.dep_ == "aux" and t.lower_ in ("will", "'ll", "gonna") for t in sentence):
            slots["future"] = "yes"

        if "question" in conditions and conditions["question"] != self._is_question(sentence):
            return None
        if "max_tokens" in conditions and \
                sum(1 for t in doc if not t.is_punct) > conditions["max_tokens"]:
            return None
        if "not_negated" in conditions and self._is_negated(nodes[conditions["not_negated"]]):
            return None
        if "first_token" in conditions and nodes[conditions["first_token"]].i != 0:
            return None
        if "subject_is_user" in conditions and not self._has_user_subject(nodes[conditions["subject_is_user"]]):
            return None
        if "addressed_to_bot" in conditions and not self._addressed_to_bot(nodes[conditions["addressed_to_bot"]]):
            return None
        if "emotion" in conditions:
            token = nodes[conditions["emotion"]]
            emotion = self.kb["emotions"].get(token.lower_) or self.kb["emotions"].get(token.lemma_.lower())
            if emotion is None:
                return None
            slots["emotion_mood"] = emotion["mood"]
            slots["emotion_variant"] = emotion.get("variant", emotion["mood"])
            mood = emotion["mood"]
            valence = emotion["valence"]
        if "evaluation" in conditions:
            token = nodes[conditions["evaluation"]]
            valence = self.kb["evaluations"].get(token.lower_)
            if valence is None:
                return None
            # "not bad" is positive, "not fun" is negative
            if any(self._is_negated(t) for t in (token, token.head)):
                valence = {"positive": "negative", "negative": "positive"}.get(valence, valence)
            slots["evaluation_valence"] = valence
            slots["negation"] = "not " if any(self._is_negated(t) for t in (token, token.head)) else ""

        for slot_name, spec in rule.get("slots", {}).items():
            if spec["node"] not in nodes:  # optional node absent from this pattern
                continue
            raw, reflected = self._extract_slot(nodes[spec["node"]], spec["span"])
            if spec.get("capitalize") and raw:
                raw = reflected = raw[:1].upper() + raw[1:]
            # Lowercase a capitalized common word ("School was boring", "Today was fun"), not a name
            node = nodes[spec["node"]]
            if spec.get("lowercase") and raw and (
                    node.pos_ != "PROPN" or node.lower_ in self.kb["lexicons"]["common_capitalized"]):
                raw = raw[:1].lower() + raw[1:]
                reflected = reflected[:1].lower() + reflected[1:]
            slots[f"{slot_name}_raw"] = raw
            slots[slot_name] = reflected
            slots[f"{slot_name}_slug"] = _slug(raw)

        slots["message_text"] = doc.text
        if "comparison_preference" in rule.get("compute", []):
            self._comparison_preference(slots)

        if "negation_flips" in rule and self._is_negated(nodes[rule["negation_flips"]]):
            # "My friend isn't happy": respond as to a sad feeling, keep the words accurate
            slots["emotion"] = f"not {slots.get('emotion', '')}".strip()
            flipped = "sad" if valence == "positive" else "default"
            slots["emotion_mood"] = flipped
            mood = "sad" if flipped == "sad" else None
            valence = "negative" if flipped == "sad" else "neutral"

        memories = []
        for memory in rule.get("memories", []):
            referenced = re.findall(r"\{(\w+)\}", memory["key"] + memory["value"])
            if any(not slots.get(name) for name in referenced):
                continue  # e.g. "bigger than" states no preference
            value = memory["value"].format_map(_BlankDict(slots)).strip()
            key = memory["key"].format_map(_BlankDict(slots)).strip("_")
            if value and key:
                memories.append((memory["category"], key, value))

        return Frame(
            rule_id=rule["id"],
            priority=rule.get("priority", 0),
            slots=slots,
            memories=memories,
            mood=mood,
            valence=valence,
            sentence=sentence.start,
            rule=rule,
        )

    @staticmethod
    def _addressed_to_bot(token) -> bool:
        """
        True for a request to the bot: no subject ("Tell me a joke"), or "you"/"we"/"us" as
        subject ("Can you...", "Can we..."), but not "I want to tell you a joke"
        """
        if any(c.dep_ in ("nsubj", "nsubjpass") and c.lower_ not in ("you", "we", "us", "'s")
               for c in token.children):
            return False
        if token.dep_ in ("xcomp", "ccomp") and any(
                c.dep_ == "nsubj" and c.lower_ in ("i", "we") for c in token.head.children):
            return False
        return True

    def _comparison_preference(self, slots: Dict[str, str]) -> None:
        """Which side of "X is better/worse than Y" the child prefers"""
        comp = slots.get("comp", "").lower()
        if comp in self.kb["lexicons"]["comparatives_positive"]:
            preferred, other = "x", "y"
        elif comp == "worse":
            preferred, other = "y", "x"
        else:
            return  # "bigger", "faster": a comparison, not a preference
        slots["preferred"], slots["other"] = slots[preferred], slots[other]
        slots["preferred_slug"], slots["other_slug"] = slots[f"{preferred}_slug"], slots[f"{other}_slug"]

    @staticmethod
    def _is_negated(token) -> bool:
        return any(child.dep_ == "neg" for child in token.children)

    @staticmethod
    def _has_user_subject(token) -> bool:
        for candidate in (token, token.head):
            if any(c.dep_ == "nsubj" and c.lower_ == "i" for c in candidate.children):
                return True
        return False

    # ------------------------------------------------------------------
    # Slot extraction and perspective
    # ------------------------------------------------------------------

    def _extract_slot(self, token, span: str) -> Tuple[str, str]:
        """Return (child's wording, bot-perspective wording) for a bound node"""
        if span == "text":
            return token.text, token.text
        if span == "lemma":
            lemma = token.lemma_.lower()
            return lemma, lemma
        if span == "subtree":
            tokens = [t for t in token.subtree if t.dep_ not in _SKIP_DEPS]
            if token.dep_ == "xcomp" and tokens and tokens[0].lower_ == "to":
                tokens = tokens[1:]
        elif span == "verb_group":
            # "will be", "has been": auxiliaries with the verb, without negation
            tokens = sorted([c for c in token.children if c.dep_ in ("aux", "auxpass")] + [token],
                            key=lambda t: t.i)
        elif span == "compound_phrase":
            # The noun with compound words only ("chocolate ice cream", not "cats more")
            tokens = [t for t in token.subtree if t == token or (t.head == token and t.dep_ == "compound")]
        elif span == "noun_phrase":
            tokens = [t for t in token.subtree
                      if t == token or (t.head == token and t.dep_ in ("amod", "compound"))]
        elif span == "clause":
            tokens = [t for t in token.subtree if t.dep_ not in _SKIP_DEPS]
            while tokens and tokens[0].dep_ == "mark":
                tokens = tokens[1:]
        elif span == "predicate":
            excluded = set()
            for child in token.children:
                if child.dep_ in ("nsubj", "aux", "neg") or child.ent_type_ in ("DATE", "TIME"):
                    excluded.update(child.subtree)
            tokens = [t for t in token.subtree
                      if t not in excluded and t.dep_ not in _SKIP_DEPS and t.ent_type_ not in ("DATE", "TIME")]
        elif span == "because_clause":
            tokens = []
            for child in token.children:
                if child.dep_ == "advcl" and any(m.dep_ == "mark" and m.lower_ in ("because", "cause", "since")
                                                 for m in child.children):
                    tokens = [t for t in child.subtree
                              if t.dep_ not in _SKIP_DEPS and not (t.dep_ == "mark" and t.head == child)]
                    break
        else:
            raise ValueError(f"Unknown slot span type: {span}")

        while tokens and tokens[0].dep_ in _TRIM_DEPS:
            tokens = tokens[1:]
        while tokens and tokens[-1].dep_ in _TRIM_DEPS:
            tokens = tokens[:-1]

        raw = self._join(tokens, reflect=False)
        reflected = self._join(tokens, reflect=True)
        return raw, reflected

    @staticmethod
    def _coordinated_subjects(tokens) -> Dict[int, Tuple[set, str]]:
        """
        Rewrite subjects like "my mom and I" / "me and my brother" / "my mom, my dad and I" as
        "you and your mom" / "you and your brother" / "you, your mom and your dad" when reflecting.

        Returns:
            {first token index: (covered token indices, replacement text)}
        """
        rewrites = {}
        included = {t.i for t in tokens}
        for token in tokens:
            if token.dep_ not in ("nsubj", "nsubjpass"):
                continue
            phrase = list(token.subtree)
            pronouns = [t for t in phrase if t.lower_ in ("i", "me", "we", "us") and t.pos_ == "PRON"]
            if not pronouns or len(phrase) < 3 or not {t.i for t in phrase} <= included:
                continue
            pronoun = pronouns[0]
            removed = {pronoun.i}
            position = phrase.index(pronoun)
            for neighbor in (position - 1, position + 1):
                if 0 <= neighbor < len(phrase) and phrase[neighbor].dep_ in ("cc", "punct"):
                    removed.add(phrase[neighbor].i)
                    break
            rest = [t for t in phrase if t.i not in removed]
            while rest and rest[-1].dep_ in ("cc", "punct"):
                rest = rest[:-1]
            others = ResponseEngine._join(rest, reflect=True)
            if not others:
                continue
            if "," in others:
                head, _, last = others.rpartition(",")
                text = f"you, {head.strip()} and {last.strip()}"
            else:
                text = f"you and {others}"
            rewrites[phrase[0].i] = ({t.i for t in phrase}, text)
        return rewrites

    @staticmethod
    def _space_after(tokens, index: int) -> str:
        """Original whitespace if the next token is adjacent; a space if tokens were skipped"""
        if index >= len(tokens) - 1:
            return ""
        token, following = tokens[index], tokens[index + 1]
        return token.whitespace_ if following.i == token.i + 1 else " "

    @staticmethod
    def _join(tokens, reflect: bool) -> str:
        tokens = list(tokens)
        rewrites = ResponseEngine._coordinated_subjects(tokens) if reflect else {}
        skip = set()
        parts = []
        for index, token in enumerate(tokens):
            if token.i in skip:
                continue
            if token.i in rewrites:
                covered, text = rewrites[token.i]
                skip |= covered
                last = max(covered)
                after = next((i for i, t in enumerate(tokens) if t.i == last), None)
                parts.append(text + (ResponseEngine._space_after(tokens, after) if after is not None else ""))
                continue
            text = token.text
            if reflect:
                text = ResponseEngine._reflect_token(token)
            # Lowercase a sentence-initial capital unless it is a name or "I"
            if index == 0 and token.i == 0 and token.pos_ != "PROPN" and text not in ("I",):
                text = text[:1].lower() + text[1:]
            parts.append(text + ResponseEngine._space_after(tokens, index))
        return "".join(parts).strip()

    @staticmethod
    def _reflect_token(token) -> str:
        lower = token.lower_
        if lower == "you":
            return "I" if token.dep_ in ("nsubj", "nsubjpass") else "me"
        if lower == "was" and ResponseEngine._first_person_subject(token):
            return "were"
        if lower in ("are", "'re") and any(c.dep_ == "nsubj" and c.lower_ == "you" for c in token.head.children):
            return "am" if lower == "are" else "'m"
        if lower in _REFLECT_WORDS:
            return _REFLECT_WORDS[lower]
        return token.text

    def _known_person_subject(self, token) -> bool:
        """True if the clause's subject is "my <relation>" or a recognized name ("Maya said no")"""
        relations = set(self.kb["lexicons"]["relations"])
        for child in token.children:
            if child.dep_ != "nsubj":
                continue
            if child.lemma_.lower() in relations and any(c.dep_ == "poss" and c.lower_ == "my" for c in child.children):
                return True
            if child.pos_ == "PROPN" and child.ent_type_ == "PERSON":
                return True
        return False

    @staticmethod
    def _first_person_subject(token) -> bool:
        """True if the token's clause has I/we as subject, including conjuncts ("my mom and I")"""
        for candidate in (token, token.head):
            for child in candidate.children:
                if child.dep_ == "nsubj" and any(t.lower_ in ("i", "me", "we", "us") and t.pos_ == "PRON"
                                                 for t in child.subtree):
                    return True
        return False

    # ------------------------------------------------------------------
    # Public helpers used by memory extraction and mood detection
    # ------------------------------------------------------------------

    def extract_memories(self, message: str) -> List[Tuple[str, str, str]]:
        """Memory writes from every matched rule: (category, key, value)"""
        analysis = self.analyze(message)
        if analysis is None:
            return []
        memories = []
        for frame in analysis.frames:
            memories.extend(frame.memories)
        return memories

    def detect_mood(self, message: str) -> Optional[str]:
        """Mood from matched rules (e.g. "I feel sad because..."), or None"""
        analysis = self.analyze(message)
        return analysis.mood if analysis else None

    # ------------------------------------------------------------------
    # Response composition
    # ------------------------------------------------------------------

    def generate_response(
        self,
        message: str,
        personality,
        context: Optional[Dict[str, Any]] = None,
        user_name: Optional[str] = None,
        allow_reflection: bool = True,
        policy=None,
        features: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """
        Compose a reply for a message

        Args:
            message: The child's message
            personality: BotPersonality (traits, mood, friendship level, name)
            context: Conversation context; uses "relevant_memories" for callbacks
            user_name: Child's name for greetings
            allow_reflection: Whether the child's words may be echoed back
            policy: Optional EngagementPolicy; once it has enough data for a choice
                (template variant, follow-up question, memory reference), that choice
                favors what this child has engaged with
            features: Optional dict that receives the choices made in this reply, for
                crediting the child's next message (see services/engagement_tracker.py)

        Returns:
            Reply text, or None if the parser is unavailable
        """
        features = features if features is not None else {}
        analysis = self.analyze(message)
        if analysis is None:
            return None

        context = context or {}
        user_id = getattr(personality, "user_id", 0) or 0
        level = getattr(personality, "friendship_level", 1) or 1
        globals_ = {
            "user_name": user_name or "friend",
            "bot_name": getattr(personality, "name", None) or "Buddy",
            "bot_mood": getattr(personality, "mood", None) or "happy",
        }

        responding = [f for f in analysis.frames
                      if f.rule.get("responses") or f.rule.get("responses_by")]
        if not allow_reflection:
            # Only rules whose replies use no words taken from the message
            responding = [f for f in responding if not f.rule.get("slots")]

        if responding:
            frame = responding[0]
            slots = _BlankDict({**globals_, **frame.slots})
            self._compute_slots(frame, slots, personality)
            core = self._choose_template(frame.rule, slots, level, user_id, policy, features)
            features["rule"] = frame.rule_id

            # Multi-sentence messages: also answer the strongest match in another sentence
            # ("I won my game today! Do you like soccer?")
            second = next((f for f in responding[1:]
                           if f.sentence != frame.sentence and f.priority >= SECOND_REPLY_MIN_PRIORITY), None)
            if second is not None:
                second_slots = _BlankDict({**globals_, **second.slots})
                self._compute_slots(second, second_slots, personality)
                second_core = self._choose_template(second.rule, second_slots, level, user_id, policy, features)
                # Answer in the order the sentences were written
                core = f"{core} {second_core}" if frame.sentence < second.sentence else f"{second_core} {core}"
            valence = frame.valence
            use_opener = frame.rule.get("opener", False)
            follow_ups = frame.rule.get("follow_ups", [])
            stored_keys = {key for f in analysis.frames for (_, key, _) in f.memories}
        else:
            slots = _BlankDict(globals_)
            core, valence, kind = self._fallback(analysis, slots, allow_reflection, user_id, policy, features)
            features["rule"] = f"fallback_{kind}"
            use_opener = False
            follow_ups = []
            stored_keys = set()

        parts = []
        energy = getattr(personality, "energy", 0.5)
        if use_opener:
            openers = self.kb["openers"].get(valence, {}).get("high" if energy >= 0.5 else "low", [])
            if openers:
                parts.append(self.rng.choice(openers))
        parts.append(core)

        curiosity = getattr(personality, "curiosity", 0.5)
        asked = core.rstrip().endswith("?")
        if follow_ups and not asked:
            if self._decide("follow_up", curiosity, policy):
                parts.append(self.rng.choice(follow_ups).format_map(slots))
                asked = True
                features["follow_up"] = "yes"
            else:
                features["follow_up"] = "no"

        if not asked and level >= 3:
            eligible = self._callback_memories(context.get("relevant_memories") or [], stored_keys)
            if eligible:
                if self._decide("callback", CALLBACK_PROBABILITY, policy):
                    parts.append(self._memory_callback(eligible))
                    features["callback"] = "yes"
                else:
                    features["callback"] = "no"

        text = " ".join(p.strip() for p in parts if p and p.strip())
        return self._apply_style(text, personality)

    def _compute_slots(self, frame: Frame, slots: Dict[str, str], personality) -> None:
        seed_id = getattr(personality, "id", None) or getattr(personality, "user_id", 0) or 0
        for name in frame.rule.get("compute", []):
            if name == "bot_favorite":
                options = self.kb["bot_profile"]["favorites"].get(slots.get("category", ""))
                if options:
                    favorite = options[_stable_index(f"{seed_id}:{slots['category']}", len(options))]
                    if favorite.lower() == slots.get("value_raw", "").lower():
                        slots["same_favorite"] = "yes"
                    else:
                        slots["bot_favorite"] = favorite
            elif name == "requested_content":
                self._requested_content(slots.get("kind", ""), slots, user_id=getattr(personality, "user_id", 0))
            elif name == "repeat_request":
                kind = self._last_request.get(getattr(personality, "user_id", 0))
                if kind:
                    self._requested_content(kind, slots, user_id=getattr(personality, "user_id", 0))
            elif name == "bot_pick":
                options = [slots.get("x", ""), slots.get("y", "")]
                if all(options):
                    pair = ":".join(sorted(o.lower() for o in options))
                    slots["bot_pick"] = options[_stable_index(f"{seed_id}:{pair}", 2)]
            elif name == "bot_shares_like":
                thing = slots.get("thing_raw", "").lower()
                interests = [i.lower() for i in (personality.get_interests() if hasattr(personality, "get_interests") else [])]
                favorites = [v.lower() for vals in self.kb["bot_profile"]["favorites"].values() for v in vals]
                shares = any(word in thing for word in interests + favorites) or \
                    _stable_index(f"{seed_id}:{slots.get('thing_slug', '')}", 3) == 0
                if shares and thing:
                    slots["bot_shares_like"] = "yes"

    def _requested_content(self, kind: str, slots: Dict[str, str], user_id: int) -> None:
        """Fill {content} with a joke or fact (topical if the message names a topic)"""
        from services.fact_quirk_service import fact_quirk_service
        from services.pun_quirk_service import pun_quirk_service

        if kind in ("joke", "pun", "riddle"):
            slots["content"] = pun_quirk_service.random_pun(slots.get("message_text", ""))
        elif kind == "fact":
            slots["content"] = fact_quirk_service.random_fact(slots.get("message_text", ""))
        else:
            return
        self._last_request[user_id] = kind

    def rule_flag(self, rule_id: Optional[str], flag: str) -> bool:
        """A rule's boolean option from the knowledge base (e.g. "no_jokes")"""
        return bool(rule_id and self.rules.get(rule_id, {}).get(flag))

    def _decide(self, feature: str, probability: float, policy) -> bool:
        """
        Yes/no choice for an optional part of a reply. Uses the personality-based probability
        until the policy has enough engagement data for both options, then Thompson sampling
        with that probability as the prior.
        """
        if policy is not None and policy.has_data(feature, ["yes", "no"]):
            return policy.choose(feature, {"yes": probability, "no": 1.0 - probability}) == "yes"
        return self.rng.random() < probability

    def _choose_template(self, rule: Dict[str, Any], slots: Dict[str, str], level: int, user_id: int,
                         policy=None, features: Optional[Dict[str, str]] = None) -> str:
        if "responses_by" in rule:
            by = rule["responses_by"]
            variants = by["variants"]
            options = variants.get(slots.get(by["slot"], ""), variants.get("default", []))
        else:
            options = rule["responses"]

        candidates = []
        for option in options:
            spec = option if isinstance(option, dict) else {"text": option}
            if spec.get("min_level", 1) > level:
                continue
            if any(not slots.get(req) for req in spec.get("requires", [])):
                continue
            candidates.append(spec)

        # Prefer the most specific templates (those that use the most optional slots)
        most_specific = max((len(c.get("requires", [])) for c in candidates), default=0)
        candidates = [c["text"] for c in candidates if len(c.get("requires", [])) == most_specific]
        return self._pick(candidates, user_id, f"template:{rule['id']}", policy, features).format_map(slots)

    def _pick(self, options: List[str], user_id: int, feature: Optional[str] = None,
              policy=None, features: Optional[Dict[str, str]] = None) -> str:
        """
        Choose a template, avoiding ones used recently for this user. Among the remaining
        ones, prefer templates this child has engaged with once each has enough data.
        """
        recent = list(self._recent[user_id])
        learned = (feature is not None and policy is not None and len(options) > 2
                   and policy.has_data(feature, [template_id(o) for o in options]))
        if learned:
            # Only avoid an exact repeat, so the learned preference has options to choose from
            window = recent[-1:]
        else:
            # Exclude as many recently used options as possible while leaving at least one
            window = recent[-(len(options) - 1):] if len(options) > 1 else []
        fresh = [o for o in options if o not in window] or options

        if learned and len(fresh) > 1:
            ids = {template_id(o): o for o in fresh}
            choice = ids[policy.rank(feature, list(ids))[0]]
        else:
            choice = self.rng.choice(fresh)

        self._recent[user_id].append(choice)
        if feature and features is not None:
            features[feature] = template_id(choice)
        return choice

    def _fallback(self, analysis: Analysis, slots: Dict[str, str], allow_reflection: bool, user_id: int,
                  policy=None, features: Optional[Dict[str, str]] = None) -> Tuple[str, str, str]:
        """Reply when no rule matched. Returns (text, valence, fallback kind)."""
        fallbacks = self.kb["fallbacks"]
        doc = analysis.doc

        def pick(kind: str) -> str:
            return self._pick(fallbacks[kind], user_id, f"template:fallback_{kind}", policy, features)

        if analysis.is_question:
            return pick("question"), "neutral", "question"

        # Reflect the last sentence that is short and about the child
        if allow_reflection:
            for sentence in reversed(list(doc.sents)):
                root = sentence.root
                if (len(sentence) <= 15 and root.pos_ in ("VERB", "AUX")
                        and (self._first_person_subject(root) or self._known_person_subject(root))):
                    _, clause = self._extract_slot(root, "clause")
                    slots["clause"] = clause
                    return pick("reflection").format_map(slots), "neutral", "reflection"

        # Long sentences: echo the last clause about the child ("...and then I fell down")
        if allow_reflection:
            clause = self._last_clause_about_child(doc)
            if clause:
                slots["clause"] = clause
                return pick("long_reflection").format_map(slots), "neutral", "long_reflection"

        # A he/she/they the reference tracker could not resolve
        if any(t.lower_ in ("he", "she", "they") and t.dep_ in ("nsubj", "nsubjpass") for t in doc):
            return pick("unknown_person"), "neutral", "unknown_person"

        if allow_reflection:
            chunks = [c for c in doc.noun_chunks if c.root.pos_ != "PRON"]
            if chunks:
                slots["topic"] = self._join(list(chunks[-1]), reflect=True)
                return pick("topic").format_map(slots), "neutral", "topic"

        return pick("generic"), "neutral", "generic"

    def _last_clause_about_child(self, doc) -> Optional[str]:
        """
        The last clause in a long message whose subject is the child or a known person,
        as a short bot-perspective phrase. Clauses joined with "and" that have no subject
        of their own take it from the clause they are joined to.
        """
        verbs = [t for t in doc if t.pos_ in ("VERB", "AUX") and t.dep_ in ("ROOT", "conj")]
        for verb in reversed(verbs):
            subject_owner = verb
            while (not any(c.dep_ == "nsubj" for c in subject_owner.children)
                   and subject_owner.dep_ == "conj"):
                subject_owner = subject_owner.head
            if not (self._first_person_subject(subject_owner) or self._known_person_subject(subject_owner)):
                continue

            # The clause's own words: not the clauses joined to it
            joined = {t.i for c in verb.children if c.dep_ == "conj" for t in c.subtree}
            tokens = [t for t in verb.subtree
                      if t.i not in joined and t.dep_ not in _SKIP_DEPS
                      and not (t.dep_ == "cc" and t.head == verb)
                      and not (t.dep_ == "advmod" and t.lower_ == "then" and t.head == verb)]
            if subject_owner is not verb:
                subject = next(c for c in subject_owner.children if c.dep_ == "nsubj")
                tokens = sorted(set(tokens) | set(subject.subtree), key=lambda t: t.i)
            while tokens and tokens[0].dep_ in _TRIM_DEPS | {"advmod"} and tokens[0].lower_ in ("and", "then", "so", ","):
                tokens = tokens[1:]
            while tokens and tokens[-1].dep_ in _TRIM_DEPS:
                tokens = tokens[:-1]
            if 0 < len(tokens) <= 15:
                return self._join(tokens, reflect=True)
        return None

    def _callback_memories(self, memories, stored_keys) -> List[Any]:
        """Stored memories that can be mentioned (not the ones stored from this message)"""
        callbacks = self.kb["memory_callbacks"]
        return [m for m in memories
                if getattr(m, "category", None) in callbacks and getattr(m, "key", None) not in stored_keys]

    def _memory_callback(self, eligible) -> str:
        memory = self.rng.choice(eligible)
        return self.rng.choice(self.kb["memory_callbacks"][memory.category]).format(value=memory.value)

    def _apply_style(self, text: str, personality) -> str:
        """Shape the reply with formality and energy, then fix capitalization"""
        if getattr(personality, "formality", 0.3) > 0.6:
            for informal, formal in self.kb["formal_substitutions"].items():
                if informal[-1].isalpha():
                    text = re.sub(rf"\b{re.escape(informal)}\b", formal, text)
                else:
                    text = text.replace(informal, formal)
        if getattr(personality, "energy", 0.5) < 0.35:
            text = text.replace("!", ".")

        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"\s+([?.!,])", r"\1", text)
        # Capitalize the start of each sentence
        return re.sub(r"(^|[.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), text)


# Global instance
response_engine = ResponseEngine()
