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

_SKIP_DEPS = {"punct", "intj"}


@dataclass
class Frame:
    """A structural rule match with its bound slots"""

    rule_id: str
    priority: int
    slots: Dict[str, str]
    memories: List[Tuple[str, str, str]] = field(default_factory=list)
    mood: Optional[str] = None
    valence: str = "neutral"
    rule: Dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass
class Analysis:
    """Result of analyzing one message"""

    frames: List[Frame]
    is_question: bool
    mood: Optional[str]
    doc: Any = field(default=None, repr=False)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:50]


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
        self._load_knowledge_base()

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

        is_question = self._is_question(doc)
        frames: List[Frame] = []
        seen_rules = set()

        for match_id, token_ids in self._get_matcher()(doc):
            key = self.parser.vocab.strings[match_id]
            rule_id = key.split("#")[0]
            if rule_id in seen_rules:
                continue
            nodes = dict(zip(self._pattern_nodes[key], (doc[i] for i in token_ids)))
            frame = self._build_frame(self.rules[rule_id], nodes, doc, is_question)
            if frame is not None:
                frames.append(frame)
                seen_rules.add(rule_id)

        matched = {f.rule_id for f in frames}
        frames = [f for f in frames if not matched.intersection(f.rule.get("suppressed_by", []))]
        frames.sort(key=lambda f: f.priority, reverse=True)
        mood = next((f.mood for f in frames if f.mood), None)
        return Analysis(frames=frames, is_question=is_question, mood=mood, doc=doc)

    @staticmethod
    def _is_question(doc) -> bool:
        text = doc.text.strip()
        return text.endswith("?") or (len(doc) > 0 and doc[0].lower_ in _QUESTION_STARTERS)

    def _build_frame(self, rule: Dict[str, Any], nodes: Dict[str, Any], doc, is_question: bool) -> Optional[Frame]:
        conditions = rule.get("conditions", {})
        slots: Dict[str, str] = {}
        mood = rule.get("mood")
        valence = rule.get("valence", "neutral")

        if "question" in conditions and conditions["question"] != is_question:
            return None
        if "not_negated" in conditions and self._is_negated(nodes[conditions["not_negated"]]):
            return None
        if "first_token" in conditions and nodes[conditions["first_token"]].i != 0:
            return None
        if "subject_is_user" in conditions and not self._has_user_subject(nodes[conditions["subject_is_user"]]):
            return None
        if "emotion" in conditions:
            token = nodes[conditions["emotion"]]
            emotion = self.kb["emotions"].get(token.lower_) or self.kb["emotions"].get(token.lemma_.lower())
            if emotion is None:
                return None
            slots["emotion_mood"] = emotion["mood"]
            mood = emotion["mood"]
            valence = emotion["valence"]

        for slot_name, spec in rule.get("slots", {}).items():
            raw, reflected = self._extract_slot(nodes[spec["node"]], spec["span"])
            if spec.get("capitalize") and raw:
                raw = reflected = raw[:1].upper() + raw[1:]
            slots[f"{slot_name}_raw"] = raw
            slots[slot_name] = reflected
            slots[f"{slot_name}_slug"] = _slug(raw)

        memories = []
        for memory in rule.get("memories", []):
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
            rule=rule,
        )

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
        elif span == "noun_phrase":
            tokens = [t for t in token.subtree
                      if t == token or (t.head == token and t.dep_ in ("amod", "compound"))]
        elif span == "clause":
            tokens = [t for t in token.subtree if t.dep_ not in _SKIP_DEPS]
            while tokens and tokens[0].dep_ == "mark":
                tokens = tokens[1:]
            while tokens and tokens[-1].dep_ in ("cc",):
                tokens = tokens[:-1]
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

        raw = self._join(tokens, reflect=False)
        reflected = self._join(tokens, reflect=True)
        return raw, reflected

    @staticmethod
    def _join(tokens, reflect: bool) -> str:
        parts = []
        for index, token in enumerate(tokens):
            text = token.text
            if reflect:
                text = ResponseEngine._reflect_token(token)
            # Lowercase a sentence-initial capital unless it is a name or "I"
            if index == 0 and token.i == 0 and token.pos_ != "PROPN" and text not in ("I",):
                text = text[:1].lower() + text[1:]
            ws = token.whitespace_ if index < len(tokens) - 1 else ""
            parts.append(text + ws)
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

    @staticmethod
    def _first_person_subject(token) -> bool:
        """True if the token's clause has I/we as subject, including conjuncts ("my mom and I")"""
        for candidate in (token, token.head):
            for child in candidate.children:
                if child.dep_ == "nsubj" and any(t.lower_ in ("i", "we") for t in [child, *child.conjuncts]):
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
    ) -> Optional[str]:
        """
        Compose a reply for a message

        Args:
            message: The child's message
            personality: BotPersonality (traits, mood, friendship level, name)
            context: Conversation context; uses "relevant_memories" for callbacks
            user_name: Child's name for greetings
            allow_reflection: Whether the child's words may be echoed back

        Returns:
            Reply text, or None if the parser is unavailable
        """
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
            core = self._choose_template(frame.rule, slots, level, user_id)
            valence = frame.valence
            use_opener = frame.rule.get("opener", False)
            follow_ups = frame.rule.get("follow_ups", [])
            stored_keys = {key for f in analysis.frames for (_, key, _) in f.memories}
        else:
            slots = _BlankDict(globals_)
            core, valence = self._fallback(analysis, slots, allow_reflection, user_id)
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
        if follow_ups and not asked and self.rng.random() < curiosity:
            parts.append(self.rng.choice(follow_ups).format_map(slots))
            asked = True

        if not asked and level >= 3:
            callback = self._memory_callback(context.get("relevant_memories") or [], stored_keys)
            if callback:
                parts.append(callback)

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
            elif name == "bot_shares_like":
                thing = slots.get("thing_raw", "").lower()
                interests = [i.lower() for i in (personality.get_interests() if hasattr(personality, "get_interests") else [])]
                favorites = [v.lower() for vals in self.kb["bot_profile"]["favorites"].values() for v in vals]
                shares = any(word in thing for word in interests + favorites) or \
                    _stable_index(f"{seed_id}:{slots.get('thing_slug', '')}", 3) == 0
                if shares and thing:
                    slots["bot_shares_like"] = "yes"

    def _choose_template(self, rule: Dict[str, Any], slots: Dict[str, str], level: int, user_id: int) -> str:
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
        return self._pick(candidates, user_id).format_map(slots)

    def _pick(self, options: List[str], user_id: int) -> str:
        """Choose a template, avoiding ones used recently for this user"""
        recent = list(self._recent[user_id])
        # Exclude as many recently used options as possible while leaving at least one
        window = recent[-(len(options) - 1):] if len(options) > 1 else []
        fresh = [o for o in options if o not in window] or options
        choice = self.rng.choice(fresh)
        self._recent[user_id].append(choice)
        return choice

    def _fallback(self, analysis: Analysis, slots: Dict[str, str], allow_reflection: bool, user_id: int) -> Tuple[str, str]:
        fallbacks = self.kb["fallbacks"]
        doc = analysis.doc

        if analysis.is_question:
            return self._pick(fallbacks["question"], user_id), "neutral"

        if allow_reflection and len(doc) <= 15:
            root = next((t for t in doc if t.dep_ == "ROOT"), None)
            if root is not None and root.pos_ in ("VERB", "AUX") and self._first_person_subject(root):
                _, clause = self._extract_slot(root, "clause")
                slots["clause"] = clause
                return self._pick(fallbacks["reflection"], user_id).format_map(slots), "neutral"

        if allow_reflection:
            chunks = [c for c in doc.noun_chunks if c.root.pos_ != "PRON"]
            if chunks:
                slots["topic"] = self._join(list(chunks[-1]), reflect=True)
                return self._pick(fallbacks["topic"], user_id).format_map(slots), "neutral"

        return self._pick(fallbacks["generic"], user_id), "neutral"

    def _memory_callback(self, memories, stored_keys) -> Optional[str]:
        callbacks = self.kb["memory_callbacks"]
        eligible = [m for m in memories
                    if getattr(m, "category", None) in callbacks and getattr(m, "key", None) not in stored_keys]
        if not eligible or self.rng.random() >= 0.35:
            return None
        memory = self.rng.choice(eligible)
        return self.rng.choice(callbacks[memory.category]).format(value=memory.value)

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
