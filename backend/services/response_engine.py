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

from services import appraisal as appraisal_module
from services.appraisal import Appraisal, Appraiser
from services.emoji_quirk_service import emoji_quirk_service
from services.reference_tracker import ReferenceTracker, gerund
from services.utterance_parser import _NAMED_KINDS, utterance_parser

logger = logging.getLogger("chatbot.response_engine")

RULES_PATH = Path(__file__).resolve().parent.parent / "knowledge" / "conversation_rules.json"
# Short answers to common questions about the world ("Why is the sky blue?")
ANSWERS_PATH = RULES_PATH.parent / "answers.json"

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


def _skipped(token) -> bool:
    """Interjections, and a word like "fine" or "okay" opening the sentence ("fine I'll eat it")"""
    return token.dep_ in _SKIP_DEPS or (token.pos_ == "INTJ" and token.i == token.sent.start)

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


# Stands in for the child's name until they tell it; removed with the space or comma before it
_NO_NAME = "\x00"


# Groups of people that can be a sentence's subject ("Kids chased me")
_PEOPLE_GROUPS = {"kid", "boy", "girl", "classmate", "student", "people", "everyone", "everybody"}

# Making up a story together
STORY_MAX_TURNS = 10
STORY_PROMPTS = ["Ooh! And then what happened?", "Wow! What happened next?", "Ooh, exciting! What did they do next?",
                 "That's so cool! Then what?", "I love this story! Keep going!"]
# Pretend play: replies when the child's message gives no role
PRETEND_MAX_TURNS = 8
PRETEND_PROMPTS = ["Whoa! What happens next?", "Ooh, exciting! Your turn!", "Haha, I didn't see that coming! What next?",
                   "Quick, what do we do now?"]
_PRETEND_SOUNDS = {"dragon": "Rawr!", "lion": "Roar!", "tiger": "Roar!", "dinosaur": "Rawr!", "monster": "Grrr!",
                   "robot": "Beep boop!", "cat": "Meow!", "dog": "Woof!", "wolf": "Awoooo!", "ghost": "Boo!",
                   "pirate": "Arrr!", "owl": "Hoot hoot!", "unicorn": "Neigh!", "horse": "Neigh!"}
STORY_ENDINGS = ["The end! What a great story. I loved it!", "What a fun story! You're a great storyteller."]

# Replies to a joke the child tells: to the setup question, then to the punchline
CHILD_JOKE_GUESSES = ["Hmm, I don't know! What?", "I give up! Tell me!", "Ooh, I'm not sure! What?"]
CHILD_JOKE_LAUGHS = ["Haha! That's a good one! You're really funny.", "Hahaha! I didn't see that coming!"]

# Fragments that continue the previous message: "and stay up late", "to the zoo", "next week"
_CONTINUATION_WORDS = {"and", "then", "also", "but", "or", "with", "to", "at", "in", "on", "for", "after", "before",
                       "next", "last", "this", "tomorrow", "yesterday", "tonight", "today", "so"}


@dataclass
class Expectation:
    """What the bot's last reply asked for"""
    kind: str                       # offer, choice, listen, reason, item
    offer: Optional[str] = None     # for "offer": "joke", or "again" (the same kind as last time)
    options: List[str] = field(default_factory=list)  # for "choice"
    noun: Optional[str] = None      # for "item": "part" in "What part are you playing?"


# "What part are you playing?", "What costume are you wearing?", "What kind of cake?"
_ITEM_QUESTION_RE = re.compile(
    r"\bwhat (?:kind of )?(part|costume|game|song|book|movie|show|animal|sport|color|colour|flavor|cake|pet|name|"
    r"instrument|character|team|toy)\b[^?]*\byou(?:'re)?\b[^?]*\?$"
    r"|\bwhat (?:are|were) you (?:going to be|gonna be|being|dressing up as)\b",
    re.IGNORECASE)


def expectation_from_reply(reply: str) -> Optional[Expectation]:
    """What a bot reply asks the child for, from its closing question or request"""
    if "I'd love to hear it" in reply:
        return Expectation("listen")
    questions = re.findall(r"[^.!?]*\?", reply)
    if not questions:
        return None
    question = questions[-1].strip()
    # The options may come before the question: "We could tell jokes, solve riddles, or share fun facts! Which one?"
    if _CHOICE_OFFER_RE.search(question) or (_CHOICE_OFFER_RE.search(reply) and re.match(r"which\b", question,
                                                                                          re.IGNORECASE)):
        return Expectation("choice", options=["joke", "riddle", "fact"])
    if _JOKE_OFFER_RE.search(question):
        return Expectation("offer", offer="joke")
    if re.search(r"\bwant another( one)?\?", question, re.IGNORECASE):
        return Expectation("offer", offer="again")
    if re.match(r"why\b", question, re.IGNORECASE) and not re.search(r"\bwhy not\b", question, re.IGNORECASE):
        return Expectation("reason")
    item = _ITEM_QUESTION_RE.search(question)
    if item:
        noun = item.group(1)
        return Expectation("item", noun=(noun.lower() if noun else "costume"))
    return None


# A joke the child starts without saying so: "Why did the chicken cross the road?", "Knock knock"
_JOKE_SETUP_RE = re.compile(
    r"^\W*(why did the \w+ cross the road|what do you call (a|an)\b|what did the \w+ say to\b|"
    r"why did the \w+ (go to|bring|sit on|eat|wear)\b|what has \w+ \w+ but|"
    r"what('s| is) [a-z]+ and [a-z]+\W*$)", re.IGNORECASE
)
# "Want to hear a funny joke?" - "yes": tell one
_JOKE_OFFER_RE = re.compile(r"\bwant to hear a (funny |silly )?joke\?", re.IGNORECASE)
# "a joke, a riddle, or a fun fact?" - "a riddle"
_CHOICE_OFFER_RE = re.compile(r"\bjokes?, (a |solve )?riddles?,? or (a |share )?fun facts?\b", re.IGNORECASE)
_YES_RE = re.compile(r"^\W*(yes|yeah|yea|yep|yup|sure|ok|okay|please|yes please|ya|uh huh|of course)\W*$", re.IGNORECASE)
# Riddles the bot asks and waits for a guess: (riddle, answer, words that count as the answer)
RIDDLES = [
    ("What has hands but can't clap?", "A clock!", "clock"),
    ("What has to be broken before you can use it?", "An egg!", "egg"),
    ("What gets wetter the more it dries?", "A towel!", "towel"),
    ("What has a face and two hands but no arms or legs?", "A clock!", "clock|watch"),
    ("What can you catch but not throw?", "A cold!", "cold"),
    ("What has legs but doesn't walk?", "A table!", "table|chair"),
    ("What goes up but never comes down?", "Your age!", "age"),
    ("What has lots of keys but can't open any doors?", "A piano!", "piano|keyboard"),
    ("What has one eye but can't see?", "A needle!", "needle"),
    ("What is full of holes but still holds water?", "A sponge!", "sponge"),
]
_KNOCK_KNOCK_RE = re.compile(r"^\W*knock,? knock\W*$", re.IGNORECASE)

# Kinds of words that make a silly combination when mixed ("purple monkey dishwasher")
_SILLY_GROUPS = {
    "color": {"red", "orange", "yellow", "green", "blue", "purple", "pink", "brown", "black", "white", "rainbow"},
    "animal": {"monkey", "cat", "dog", "pig", "cow", "duck", "chicken", "llama", "unicorn", "dinosaur", "fish",
               "frog", "elephant", "giraffe", "penguin", "banana", "potato", "taco", "pickle", "noodle"},
    "object": {"dishwasher", "toaster", "sock", "spoon", "fridge", "toilet", "shoe", "chair", "lamp", "pants",
               "underwear", "bucket", "couch", "microwave", "spaceship", "robot"},
}

# Things someone (or a pet) can do that hurt the child: "He scratched me"
_HURT_VERBS = {"scratch", "bite", "hit", "push", "kick", "hurt", "pinch", "bump", "punch", "slap", "trip", "shove"}

# "How do you spell because?"
_SPELL_RE = re.compile(r"\b(?:how (?:do|would|can) (?:you|i|we) spell|can you spell|spell) ([a-z]{2,20})\b", re.IGNORECASE)

# "is 1/2 bigger than 1/4"
_FRACTION_COMPARE_RE = re.compile(
    r"\b(\d{1,3})/(\d{1,3}) (?:is )?(bigger|larger|more|greater|smaller|less) than (\d{1,3})/(\d{1,3})\b",
    re.IGNORECASE)

_ARITHMETIC_RE = re.compile(
    r"\b(\d{1,4}) ?(plus|\+|minus|-|times|x|\*|divided by|/) ?(\d{1,4})\b", re.IGNORECASE
)
# "What is half of 10?"
_HALF_RE = re.compile(r"\b(half|a half|a third|a quarter|one third|one quarter) of (\d{1,4})\b", re.IGNORECASE)


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


_NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
                 "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
                 "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30}

# Rhyme families for common words children ask about
_RHYME_FAMILIES = [
    ["cat", "hat", "bat", "rat", "mat", "sat", "flat", "that"], ["dog", "log", "frog", "fog", "jog", "hog"],
    ["bee", "tree", "see", "three", "free", "me", "knee", "sea"], ["car", "star", "far", "jar", "guitar"],
    ["sun", "fun", "run", "bun", "one", "done"], ["cake", "lake", "snake", "bake", "make", "shake"],
    ["night", "light", "kite", "bite", "white", "bright", "right"], ["king", "ring", "sing", "wing", "swing", "thing"],
    ["box", "fox", "socks", "rocks", "blocks"], ["fish", "dish", "wish", "swish"], ["bed", "red", "sled", "head", "bread"],
    ["bell", "shell", "well", "smell", "yell"], ["clock", "sock", "rock", "block", "lock"],
    ["bug", "hug", "rug", "mug", "slug"], ["ball", "wall", "tall", "fall", "call", "small"],
    ["day", "play", "say", "way", "hay", "stay", "gray"], ["rain", "train", "brain", "chain", "plane"],
    ["house", "mouse", "blouse"], ["hair", "chair", "bear", "pear", "air", "stair"], ["moon", "spoon", "soon", "balloon"],
    ["boat", "goat", "coat", "float"], ["book", "cook", "look", "hook"], ["pig", "big", "dig", "wig", "twig"],
    ["pen", "hen", "ten", "men", "when"], ["cow", "now", "how", "wow"], ["bear", "chair", "hair", "pear"],
    ["blue", "shoe", "two", "zoo", "glue", "moo"], ["mice", "rice", "nice", "ice", "dice"],
    ["cookie", "rookie", "bookie"], ["kitten", "mitten", "bitten"], ["toy", "boy", "joy", "enjoy"],
    ["cheese", "please", "trees", "knees", "bees"], ["duck", "truck", "luck", "stuck"], ["mom", "bomb", "calm"],
    ["dad", "sad", "glad", "mad", "bad"], ["snow", "go", "slow", "grow", "show", "bow"], ["frog", "dog", "log"],
]


def _number_value(text: str) -> Optional[int]:
    """ "10" or "ten" -> 10; None if it is not a number up to thirty"""
    text = text.strip().lower()
    if text.isdigit():
        return int(text)
    return _NUMBER_WORDS.get(text)


def _same_thing(a: str, b: str) -> bool:
    """ "a dolphin" and "dolphins", "The Moon" and "moon": the same thing, named differently"""
    def base(text):
        words = re.sub(r"^(a|an|the|my)\s+", "", text.strip().lower()).split()
        if words and len(words[-1]) > 3 and words[-1].endswith("s") and not words[-1].endswith("ss"):
            words[-1] = words[-1][:-2] if words[-1].endswith(("ches", "shes", "xes")) else words[-1][:-1]
        return " ".join(words)
    return bool(a.strip()) and base(a) == base(b)


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
        self._last_told: Dict[int, str] = {}  # "joke"/"fun fact" if the last reply told one
        self._last_mentions: Dict[int, List[str]] = {}  # the bot's own answers in the last reply
        self._last_category: Dict[int, str] = {}
        # 1 after "I have a joke for you" (waiting for the setup), 2 after the bot's guess
        self._child_joke: Dict[int, int] = {}
        # Turns of a story the child and the bot are making up together
        self._story_mode: Dict[int, int] = {}  # the favorite category last talked about
        # Turns left of a game of pretend
        self._pretend: Dict[int, int] = {}
        # The answer to a riddle the bot asked, while the child guesses
        self._riddle: Dict[int, Tuple[str, str]] = {}
        # What the bot's last reply asked for, so a short next message can be read as its answer
        self._expect: Dict[int, Expectation] = {}
        # The child's previous message (resolved), for fragments that continue it ("next week")
        self._previous_message: Dict[int, str] = {}
        self._current_message: Dict[int, str] = {}
        self._load_knowledge_base()
        self.references = ReferenceTracker(
            parser, self.kb["lexicons"]["relations"], self.kb["lexicons"]["common_capitalized"],
            self.kb["lexicons"].get("foods", []),
        )

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _load_knowledge_base(self) -> None:
        with open(self.rules_path, encoding="utf-8") as f:
            self.kb = json.load(f)
        answers_path = self.rules_path.parent / ANSWERS_PATH.name
        if answers_path.exists():
            with open(answers_path, encoding="utf-8") as f:
                self.answers = [(re.compile(a["pattern"], re.IGNORECASE), a["answer"]) for a in json.load(f)["answers"]]
        else:
            self.answers = []
        # Whole-message set phrases: (id, pattern, replies)
        self._phrases = [(p["id"], re.compile(p["pattern"]), p["responses"]) for p in self.kb.get("phrases", [])]
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
        self.appraiser = Appraiser(self.kb)

    def is_available(self) -> bool:
        """True if the parser (spaCy and its model) is available"""
        return self.parser.is_available()

    def _thing_words(self, user_id: int) -> frozenset:
        """Lowercase head nouns of the things this child mentioned, not names of people"""
        state = self.references.state(user_id)
        people = {w.lower() for p in state.people if p.name for w in p.name.split()}
        return frozenset(t.text.split()[-1].lower() for t in state.things
                         if not t.added and not t.short) - people

    def resolve_references(self, message: str, user_id: int) -> str:
        """
        Replace pronouns ("she", "it") with the people and things they refer to from earlier
        turns, and remember what this message mentions. Call once per message, before
        analysis; pass the result to extract_memories, detect_mood and generate_response.
        """
        if not self.is_available():
            return message
        resolved = self.references.resolve(message, user_id)
        if user_id in self._current_message:
            self._previous_message[user_id] = self._current_message[user_id]
        self._current_message[user_id] = resolved
        return resolved

    def reset_references(self, user_id: int) -> None:
        """Forget earlier people and things (new conversation)"""
        self.references.reset(user_id)
        self._last_told.pop(user_id, None)
        self._last_mentions.pop(user_id, None)
        self._child_joke.pop(user_id, None)
        self._story_mode.pop(user_id, None)
        self._riddle.pop(user_id, None)
        self._pretend.pop(user_id, None)
        self._expect.pop(user_id, None)
        self._previous_message.pop(user_id, None)
        self._current_message.pop(user_id, None)

    def record_bot_reply(self, user_id: int, reply: str, humor: Optional[str] = None) -> None:
        """
        Let the child refer to what the bot just said ("That's so cool!"). Call after each
        reply with the reply before quirk additions, and humor = "pun"/"fact" if one was added.
        """
        if not self.is_available():
            return
        expectation = expectation_from_reply(reply)
        if expectation is None:
            self._expect.pop(user_id, None)
        else:
            self._expect[user_id] = expectation
        told = self._last_told.pop(user_id, None)
        added = {"pun": "joke", "fact": "fun fact"}.get(humor or "") if told is None else None
        mentions = self._last_mentions.pop(user_id, [])
        self.references.record_bot_reply(user_id, reply, told or added, mentions, told_was_added=added is not None)

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

    def analyze(self, message: str, thing_words: frozenset = frozenset()) -> Optional[Analysis]:
        """
        Parse a message and match all structural rules against it

        thing_words: nouns of things the child mentioned; "Soup was yummy" (after "it" was
        resolved to the soup) is about the soup, not someone named Soup
        """
        doc = self.parser.parse(message)
        if doc is None:
            return None
        if any(t.pos_ == "PROPN" and t.lower_ in thing_words for t in doc):
            doc = doc.copy()  # parses are cached and shared
            for token in doc:
                if token.pos_ == "PROPN" and token.lower_ in thing_words:
                    token.pos_ = "NOUN"

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
    def _embedded_modality(token) -> str:
        """
        The modality the matched words sit under, from outside them: "win" in "I want to win"
        is wanted, in "what if we win" imagined, in "we might win" possible; "want" in
        "I want a dog" is itself real
        """
        sentence = token.sent
        words = [t.lower_ for t in sentence]
        if words[:2] == ["what", "if"] and token.lower_ != "what":
            return appraisal_module.HYPOTHETICAL
        for ancestor in list(token.ancestors)[:3]:
            if ancestor.lemma_ in ("hope", "wish", "pray"):
                return appraisal_module.HOPE
            if ancestor.lemma_ in ("want", "wanna") and token.dep_ in ("xcomp", "ccomp") or (
                    ancestor.lemma_ in ("want", "wanna") and ancestor.i == token.head.i):
                return appraisal_module.WANT
        if any(c.dep_ == "aux" and c.lower_ in ("might", "may", "could") for c in token.children):
            return appraisal_module.POSSIBLE
        # "I will score a goal tomorrow": not happened yet
        if any(c.dep_ == "aux" and c.lower_ in ("will", "'ll", "gonna", "shall") for c in token.children) and \
                not any(c.dep_ == "neg" for c in token.children):
            return appraisal_module.FUTURE
        if any(c.dep_ == "aux" and c.lower_ in ("can", "ca") for c in token.children) and \
                not sentence.text.strip().endswith("?") and token.lemma_ in ("get", "have", "buy", "adopt"):
            return appraisal_module.POSSIBLE
        return appraisal_module.REAL

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
        elif self._is_past(sentence.root):
            slots["past"] = "yes"

        if "question" in conditions and conditions["question"] != self._is_question(sentence):
            return None
        # A reaction to something happening does not fit something only hoped for, wanted,
        # possible or imagined: "we can get a new one" is not "Yay, a new one!", and "I hope he
        # gets better" is not "I'm so glad he's better" (rules meant for these say "modality_ok")
        # A rule's tone that contradicts what the matched words say happened: "my brother made
        # fun of my drawing" is teasing, not the kindness of "made"
        if valence in ("positive", "negative") and not rule.get("valence_ok"):
            first = next(iter(nodes.values()))
            if first.pos_ in ("VERB", "AUX"):
                appraised = self.appraiser.appraise_tokens(first)
                if (appraised.action and appraised.notes.get("source") == "phrasal"
                        and appraised.valence in ("positive", "negative") and appraised.valence != valence):
                    return None
        if valence in ("positive", "negative") and not rule.get("modality_ok"):
            embedded = self._embedded_modality(next(iter(nodes.values())))
            if embedded in rule.get("modality_ok_for", []):
                pass
            elif embedded in (appraisal_module.HOPE, appraisal_module.WANT, appraisal_module.POSSIBLE,
                              appraisal_module.HYPOTHETICAL, appraisal_module.FUTURE):
                return None
        if "max_tokens" in conditions and \
                sum(1 for t in doc if not t.is_punct) > conditions["max_tokens"]:
            return None
        if "not_negated" in conditions and self._is_negated(nodes[conditions["not_negated"]]):
            return None
        if "not_past" in conditions and self._is_past(nodes[conditions["not_past"]]):
            return None
        # "Next time we will win": not a win yet
        if conditions.get("not_future") and slots.get("future"):
            return None
        if "past" in conditions and not self._is_past(nodes[conditions["past"]]):
            return None
        if "first_token" in conditions and nodes[conditions["first_token"]].i != 0:
            return None
        if "last_token" in conditions and \
                nodes[conditions["last_token"]].i != max(t.i for t in doc if not t.is_punct):
            return None
        if "no_det" in conditions and any(c.dep_ == "det" for c in nodes[conditions["no_det"]].children):
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
            # The adjective, its noun or verb, and for "is not a good dog" the verb over the noun
            negatable = [token, token.head] + ([token.head.head] if token.head.dep_ == "attr" else [])
            negated = any(self._is_negated(t) for t in negatable)
            if negated:
                valence = {"positive": "negative", "negative": "positive"}.get(valence, valence)
            slots["evaluation_valence"] = valence
            slots["negation"] = "not " if negated else ""

        for slot_name, spec in rule.get("slots", {}).items():
            if spec["node"] not in nodes:  # optional node absent from this pattern
                continue
            raw, reflected = self._extract_slot(nodes[spec["node"]], spec["span"])
            if raw.lower() in ("what", "which", "who", "whom", "whatever"):
                raw = reflected = ""  # "What do you eat?": no "but what sounds yummy"
            node = nodes[spec["node"]]
            # "capitalize": "names" capitalizes only a name ("jake" -> "Jake", "my brother" stays)
            if spec.get("capitalize") and raw and (spec["capitalize"] is True or node.left_edge.pos_ == "PROPN"):
                raw = raw[:1].upper() + raw[1:]
                reflected = reflected[:1].upper() + reflected[1:]
            # Lowercase a capitalized common word ("School was boring", "Today was fun"), not a name
            if spec.get("lowercase") and raw and (
                    node.pos_ != "PROPN" or node.lower_ in self.kb["lexicons"]["common_capitalized"]):
                raw = raw[:1].lower() + raw[1:]
                reflected = reflected[:1].lower() + reflected[1:]
            slots[f"{slot_name}_raw"] = raw
            slots[slot_name] = reflected
            slots[f"{slot_name}_slug"] = _slug(raw)
            # "{thing} sound{thing_s}", "about {thing_them}": "cupcakes sound", "cheese sounds"
            node = nodes[spec["node"]]
            # A bare "pancakes" can be mistagged as singular
            plural = node.tag_ in ("NNS", "NNPS") or (
                node.pos_ in ("NOUN", "VERB") and node.lower_.endswith("s") and node.lemma_.lower() != node.lower_)
            if plural:
                slots[f"{slot_name}_plural"] = "yes"
            slots[f"{slot_name}_s"] = "" if plural else "s"
            slots[f"{slot_name}_them"] = "them" if plural else "it"
            slots[f"{slot_name}_is"] = "are" if plural else "is"
            slots[f"{slot_name}_has"] = "have" if plural else "has"
            slots[f"{slot_name}_a"] = "an" if reflected[:1].lower() in "aeiou" and reflected else "a"

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

        # "memory_conjuncts": one memory per item of a list ("two cats, a dog, and seven
        # ducks" -> has_cat, has_dog, has_duck), not one for the whole list
        memory_slots = [slots]
        if "memory_conjuncts" in rule:
            node_name = rule["memory_conjuncts"]
            first = nodes[node_name]
            memory_slots = [{**slots, **self._conjunct_slots(rule, node_name, item)}
                            for item in self._list_items(first)]
        memories = []
        for memory in rule.get("memories", []):
            for item_slots in memory_slots:
                referenced = re.findall(r"\{(\w+)\}", memory["key"] + memory["value"])
                if any(not item_slots.get(name) for name in referenced):
                    continue  # e.g. "bigger than" states no preference
                value = memory["value"].format_map(_BlankDict(item_slots)).strip()
                key = memory["key"].format_map(_BlankDict(item_slots)).strip("_")
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
    def _is_past(token) -> bool:
        """True for "I had a test" and "I did have a test", not "I have a test" or "he is named Max" """
        auxes = [c.lower_ for c in token.children if c.dep_ in ("aux", "auxpass")]
        if token.tag_ == "VBD" or (token.tag_ == "VBN" and not any(
                a in ("will", "'ll", "have", "has", "'ve", "is", "are", "am", "'s", "'re", "'m", "be", "get", "gets")
                for a in auxes)):
            return True
        return any(c.dep_ in ("aux", "auxpass") and c.lower_ in ("did", "was", "were", "had")
                   for c in token.children)

    @staticmethod
    def _tense(token) -> str:
        """ "future", "past" or "present" for a clause's verb"""
        # "She said she will talk to him": the tense of what was said
        if token.lemma_ in ("say", "tell"):
            said = next((c for c in token.children if c.dep_ == "ccomp"), None)
            if said is not None:
                token = said
        if any(c.dep_ == "aux" and c.lower_ in ("will", "'ll", "gonna") for c in token.children) \
                or any(t.lower_ in ("tomorrow", "tonight") for t in token.sent):
            return "future"
        # "I'm going to have a party"
        if token.lemma_ == "go" and token.tag_ == "VBG" and any(c.dep_ == "xcomp" for c in token.children):
            return "future"
        if ResponseEngine._is_past(token):
            return "past"
        return "present"

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

    @staticmethod
    def _is_list_link(token) -> bool:
        """
        A child that continues a list: a conjunct, or a common noun in apposition (the small
        model reads "two cats, a dog, and seven ducks" as cats -appos-> dog -conj-> ducks)
        """
        return token.dep_ == "conj" or (token.dep_ == "appos" and token.pos_ == "NOUN")

    def _list_items(self, token) -> List[Any]:
        """The items of the list headed by token, in order (just the token if there is no list)"""
        items = [token]
        for child in token.children:
            if self._is_list_link(child):
                items.extend(self._list_items(child))
        return sorted(items, key=lambda t: t.i)

    def _conjunct_slots(self, rule: Dict[str, Any], node_name: str, conjunct) -> Dict[str, str]:
        """The rule's slots for one item of a list bound to node_name, without the other items"""
        slots = {}
        others = [t for c in conjunct.children
                  if self._is_list_link(c) or c.dep_ in ("cc", "punct") for t in c.subtree]
        tokens = [t for t in conjunct.subtree if t not in others and not _skipped(t)]
        for slot_name, spec in rule.get("slots", {}).items():
            if spec["node"] != node_name:
                continue
            if spec["span"] == "lemma":
                raw = reflected = conjunct.lemma_.lower()
            else:
                raw, reflected = self._join(tokens, reflect=False), self._join(tokens, reflect=True)
            slots.update({slot_name: reflected, f"{slot_name}_raw": raw, f"{slot_name}_slug": _slug(raw)})
        return slots

    def _extract_slot(self, token, span: str) -> Tuple[str, str]:
        """Return (child's wording, bot-perspective wording) for a bound node"""
        if span == "activity":
            # "I like to play Minecraft" -> "playing Minecraft", which reads right after
            # "you like", "you really enjoy" and "isn't your thing"; nouns stay as they are
            raw, reflected = self._extract_slot(token, "subtree")
            if token.dep_ == "xcomp" and token.pos_ == "VERB" and raw.lower().startswith(token.lower_):
                ing = gerund(token.lemma_.lower())
                raw, reflected = ing + raw[len(token.text):], ing + reflected[len(token.text):]
            return raw, reflected
        if span == "text":
            return token.text, token.text
        if span == "lemma":
            lemma = token.lemma_.lower()
            return lemma, lemma
        if span == "subtree":
            tokens = [t for t in token.subtree if not _skipped(t)]
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
            tokens = [t for t in token.subtree if not _skipped(t)]
            # "because", and "when"/"while" (read as adverbs): "I cried when my fish died"
            while tokens and (tokens[0].dep_ == "mark" or (tokens[0].tag_ == "WRB" and tokens[0].head.i == token.i
                                                             and tokens[0].lower_ in ("when", "while", "whenever"))):
                tokens = tokens[1:]
        elif span == "predicate":
            excluded = set()
            for child in token.children:
                if child.dep_ in ("nsubj", "aux", "neg") or child.ent_type_ in ("DATE", "TIME"):
                    excluded.update(child.subtree)
            tokens = [t for t in token.subtree
                      if t not in excluded and not _skipped(t) and t.ent_type_ not in ("DATE", "TIME")]
        elif span == "because_clause":
            tokens = []
            for child in token.children:
                if child.dep_ == "advcl" and any(m.dep_ == "mark" and m.lower_ in ("because", "cause", "since")
                                                 for m in child.children):
                    tokens = [t for t in child.subtree
                              if not _skipped(t) and not (t.dep_ == "mark" and t.head == child)]
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
            # Only pronouns that are part of the subject itself ("my mom and I"), not ones
            # inside a clause describing it ("the game that I played")
            pronouns = [t for t in phrase if t.lower_ in ("i", "me", "we", "us") and t.pos_ == "PRON"
                        and not any(a.pos_ in ("VERB", "AUX") for a in t.ancestors if a.i in {p.i for p in phrase})]
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
            if ResponseEngine._lowercase_person_name(token):
                text = text.capitalize()  # "you and lily played tag" -> "you and Lily"
            # Lowercase a sentence-initial capital unless it is a name or "I"
            if index == 0 and token.i == 0 and token.pos_ != "PROPN" and text not in ("I",):
                text = text[:1].lower() + text[1:]
            parts.append(text + ResponseEngine._space_after(tokens, index))
        return "".join(parts).strip()

    @staticmethod
    def _lowercase_person_name(token) -> bool:
        """A name the child typed in lowercase, in a place only a person fits"""
        if token.pos_ != "PROPN" or not token.is_alpha or not token.text.islower() or len(token.text) < 3:
            return False
        if token.ent_type_ == "PERSON":
            return True
        people = ("i", "me", "you", "we")
        linked = [token.head, *token.children]
        if token.dep_ == "conj" or any(t.dep_ == "conj" for t in token.children):
            return any(t.lower_ in people for t in linked)
        if token.dep_ == "attr" and token.head.lemma_ == "be" and any(
                c.dep_ == "nsubj" and c.lower_ == "i" for c in token.head.children):
            return True  # "I'm ted"
        if token.dep_ == "appos" or (token.i > 0 and token.doc[token.i - 1].dep_ == "compound"
                                     and token.doc[token.i - 1].head.i == token.i
                                     and token.doc[token.i - 1].lower_ in _NAMED_KINDS):
            return True  # "my friend ava", "my sister emma"
        return (token.dep_ == "nsubj" and token.head.pos_ in ("VERB", "AUX")) or (
            token.dep_ == "pobj" and token.head.lower_ == "with")

    @staticmethod
    def _reflect_token(token) -> str:
        lower = token.lower_
        if lower == "you":
            return "I" if token.dep_ in ("nsubj", "nsubjpass") else "me"
        if lower == "was" and ResponseEngine._own_first_person_subject(token):
            return "were"
        if lower in ("are", "'re") and any(c.dep_ == "nsubj" and c.lower_ == "you"
                                           for c in (*token.children, *token.head.children)):
            return "am" if lower == "are" else "'m"
        if lower in _REFLECT_WORDS:
            return _REFLECT_WORDS[lower]
        return token.text

    @staticmethod
    def _definite_thing_subject(token) -> bool:
        """True if the clause's subject is a specific thing ("the tower broke", "my bike is broken")"""
        # The noun can be mistagged ("The starfish felt bumpy" tags "starfish" as an adjective)
        return any(c.dep_ == "nsubj" and c.pos_ in ("NOUN", "ADJ", "PROPN")
                   and any(d.dep_ in ("det", "poss") and d.lower_ in ("the", "my", "our", "your", "his", "her", "their")
                           for d in c.children)
                   for c in token.children)

    @staticmethod
    def _arithmetic(match) -> str:
        """The answer to a small sum ("2 plus 2")"""
        a, op, b = int(match.group(1)), match.group(2).lower(), int(match.group(3))
        if op in ("plus", "+"):
            result = a + b
        elif op in ("minus", "-"):
            result = a - b
        elif op in ("times", "x", "*"):
            result = a * b
        elif b == 0:
            return "Ooh, tricky! You can't divide by zero. Do you like math?"
        elif a % b:
            return f"{a} divided by {b} is {a // b} with {a % b} left over! Do you like math?"
        else:
            result = a // b
        return f"{a} {op} {b} is {result}! Do you like math?"

    def _known_person_subject(self, token, user_id: Optional[int] = None) -> bool:
        """
        True if the clause's subject is "my <relation>", a recognized name ("Maya said no"),
        a name the child used before, or "a girl named Zoe"
        """
        relations = set(self.kb["lexicons"]["relations"])
        known = {p.name.lower() for p in self.references.state(user_id).people if p.name} \
            if user_id is not None else set()
        for child in token.children:
            if child.dep_ != "nsubj":
                continue
            if child.lemma_.lower() in relations and any(c.dep_ == "poss" and c.lower_ == "my" for c in child.children):
                return True
            # "Mom told us to stop", "Kids chased me"
            if not any(c.dep_ in ("det", "poss") for c in child.children) and (
                    child.lemma_.lower() in relations or child.lemma_.lower() in _PEOPLE_GROUPS):
                return True
            if child.pos_ == "PROPN" and (child.ent_type_ == "PERSON" or child.lower_ in known):
                return True
            if any(c.dep_ == "acl" and c.lemma_ == "name" for c in child.children):
                return True
        return False

    @staticmethod
    def _own_first_person_subject(token) -> bool:
        """True if this verb's own subject is I/we ("I was scared", not "it was dark" after it)"""
        verb = token.head if token.dep_ in ("aux", "auxpass") else token
        return any(c.dep_ in ("nsubj", "nsubjpass") and c.lower_ in ("i", "we") for c in verb.children) or (
            verb.dep_ == "conj" and not any(c.dep_ in ("nsubj", "nsubjpass") for c in verb.children)
            and ResponseEngine._first_person_subject(verb.head))

    @staticmethod
    def _done_to_child(root) -> bool:
        """ "a bee chased me", "a boy in my class likes me": someone or something acting on the child"""
        return any(c.dep_ in ("dobj", "dative") and c.lower_ in ("me", "us") for c in root.children) and any(
            c.dep_ == "nsubj" and c.pos_ in ("NOUN", "PROPN") for c in root.children)

    @staticmethod
    def _first_person_subject(token) -> bool:
        """True if the token's clause has I/we as subject, including conjuncts ("my mom and I")"""
        for candidate in (token, token.head):
            for child in candidate.children:
                if child.dep_ not in ("nsubj", "nsubjpass"):  # "I got stung by a bee"
                    continue
                subject = {t.i for t in child.subtree}
                # "I", or "I" coordinated in the subject; not "I" inside "the game that I played"
                if any(t.lower_ in ("i", "me", "we", "us") and t.pos_ == "PRON"
                       and not any(a.pos_ in ("VERB", "AUX") for a in t.ancestors if a.i in subject)
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
            context: Conversation context; uses "relevant_memories" for callbacks and
                "sensitive" (the child said something sad recently) for gentler reflections
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
        user_id = getattr(personality, "user_id", 0) or 0
        analysis = self.analyze(message, self._thing_words(user_id))
        if analysis is None:
            return None

        context = context or {}
        self._context = context  # for computed slots that recall what the child told before
        self._last_mentions.pop(user_id, None)
        level = getattr(personality, "friendship_level", 1) or 1
        globals_ = {
            # Without a name, "Hi {user_name}!" becomes "Hi!" (see _NO_NAME)
            "user_name": user_name or _NO_NAME,
            "known_name": "yes" if user_name else "",
            # The child said something sad recently: templates can require it, or be "unless" it
            "sensitive": "yes" if (context or {}).get("sensitive") else "",
            "bot_name": getattr(personality, "name", None) or "Buddy",
            "bot_mood": getattr(personality, "mood", None) or "happy",
        }

        # Playing pretend: the child gives the bot a role and plays theirs
        pretend_turns = self._pretend.pop(user_id, 0)
        if pretend_turns and re.match(r"\W*(ok |okay )?(stop|the end|i'?m done|done playing|let'?s stop)\W*$", message,
                                      re.IGNORECASE):
            if features is not None:
                features["rule"] = "pretend"
            return self._apply_style("Okay! That was so fun. Thanks for playing pretend with me!", personality)
        if pretend_turns and not re.search(r"\b(stop|the end|i'?m done|done playing|bye|goodbye)\b", message,
                                           re.IGNORECASE):
            reply = self._pretend_reply(message)
            if reply:
                self._pretend[user_id] = pretend_turns - 1
                if features is not None:
                    features["rule"] = "pretend"
                return self._apply_style(reply, personality)

        # Making up a story together: prompts for the child's lines until "the end"
        story_turns = self._story_mode.pop(user_id, 0)
        if story_turns:
            if re.search(r"\bthe end\b", message, re.IGNORECASE):
                if features is not None:
                    features["rule"] = "story"
                return self._apply_style(self.rng.choice(STORY_ENDINGS), personality)
            if not analysis.is_question and story_turns < STORY_MAX_TURNS:
                self._story_mode[user_id] = story_turns + 1
                if features is not None:
                    features["rule"] = "story"
                return self._apply_style(self._pick(STORY_PROMPTS, user_id), personality)

        # The child's guess at the bot's riddle
        riddle = self._riddle.pop(user_id, None)
        # A guess is short ("a clock", "is it a towel?"); "do you like farts" changes the subject,
        # and "you're funny" or "haha" is not a guess (the riddle stays open)
        if riddle is not None and re.match(r"\W*(you|you're|youre|ur|that's|thats|haha\w*|lol|lmao|wow|cool|hehe)\b",
                                           message, re.IGNORECASE):
            self._riddle[user_id] = riddle
            riddle = None
        if (riddle is not None and len(message.split()) <= 6
                and not re.match(r"\W*(do|can|will|what's|whats) you\b|\W*tell me\b", message, re.IGNORECASE)):
            answer, accepted = riddle
            if features is not None:
                features["rule"] = "riddle_answer"
            if re.search(rf"\b({accepted})s?\b", message, re.IGNORECASE):
                reply = f"Yes, you got it! {answer[:-1]}. You're a great riddle solver! Want another one?"
            elif re.search(r"\b(know|idk|give up|no idea|tell me|not sure)\b", message, re.IGNORECASE):
                reply = f"That's okay, it's a tricky one! The answer is: {answer} Want another one?"
            else:
                reply = f"Good guess! The answer is: {answer} Want another one?"
            return self._apply_style(reply, personality)

        # The answer to what the bot just asked or offered
        expectation = self._expect.pop(user_id, None)
        answered = self._answer_expectation(expectation, message, analysis, user_id) if expectation else None
        if answered is not None:
            rule_id, reply = answered
            if features is not None:
                features["rule"] = rule_id
            return self._apply_style(reply, personality)

        # Set phrases that are the whole message ("me too", "nvm", "you're right")
        phrase = self._phrase_reply(message, user_id)
        if phrase is not None:
            rule_id, reply = phrase
            if features is not None:
                features["rule"] = rule_id
            return self._apply_style(reply, personality)

        # The child is telling a joke: "Why did the chicken cross the road?" ... the punchline
        joke_stage = self._child_joke.pop(user_id, 0)
        if not joke_stage and _KNOCK_KNOCK_RE.match(message):
            self._child_joke[user_id] = 3
            if features is not None:
                features["rule"] = "child_joke"
            return "Who's there?"
        if joke_stage == 3:
            # "Knock knock" - "Who's there?" - "Lettuce" - "Lettuce who?"
            self._child_joke[user_id] = 2
            if features is not None:
                features["rule"] = "child_joke"
            return f"{message.strip(' ?!.').capitalize()} who?"
        if not joke_stage and _JOKE_SETUP_RE.match(message):
            joke_stage = 1
        if joke_stage:
            if features is not None:
                features["rule"] = "child_joke"
            if joke_stage == 1 and analysis.is_question:
                self._child_joke[user_id] = 2
                # "Why did ...?" -> "...Why?"; "What do you call ...?" -> "...What?"
                ending = "Why?" if message.strip().lower().startswith("why") else "What?"
                return self._apply_style(self.rng.choice(CHILD_JOKE_GUESSES).replace("What?", ending), personality)
            return self._apply_style(self.rng.choice(CHILD_JOKE_LAUGHS), personality)

        # "What's 2 plus 2?"
        # "Is 1/2 bigger than 1/4?"
        fraction_match = _FRACTION_COMPARE_RE.search(message)
        if fraction_match:
            if features is not None:
                features["rule"] = "arithmetic"
            return self._apply_style(self._compare_fractions(fraction_match), personality)

        half_match = _HALF_RE.search(message)
        if half_match and not analysis.frames:
            part = half_match.group(1).lower().split()[-1]
            whole = int(half_match.group(2))
            parts = {"half": 2, "third": 3, "quarter": 4}[part]
            value = whole / parts
            value_text = str(int(value)) if value == int(value) else f"{value:g}"
            if features is not None:
                features["rule"] = "arithmetic"
            return self._apply_style(f"{part.capitalize()} of {whole} is {value_text}! Do you like math?", personality)

        spell_match = _SPELL_RE.search(message)
        if spell_match and spell_match.group(1).lower() in self.parser.known_words():
            word = spell_match.group(1).lower()
            if features is not None:
                features["rule"] = "spelling"
            return self._apply_style(f"{'-'.join(word.upper())}. That spells \"{word}\"! Great job asking.", personality)

        sum_match = _ARITHMETIC_RE.search(message)
        if sum_match and not analysis.frames:
            if features is not None:
                features["rule"] = "arithmetic"
            return self._apply_style(self._arithmetic(sum_match), personality)

        responding = [f for f in analysis.frames
                      if (f.rule.get("responses") or f.rule.get("responses_by"))
                      # "Did you know how the knight moves?" asks; "Did you know sharks..." tells
                      and not (f.rule.get("unless_world_answer") and self._world_answer(message))]
        if not allow_reflection:
            # Only rules whose replies use no words taken from the message
            responding = [f for f in responding if not f.rule.get("slots")]

        # "What part are you playing?" - "a tree"; "Why is it your favorite?" - "it has rings"
        if expectation is not None and expectation.kind in ("item", "reason") and allow_reflection and not responding:
            answered = self._answer_open_question(expectation, analysis)
            if answered is not None:
                rule_id, reply = answered
                features["rule"] = rule_id
                return self._apply_style(reply, personality)

        if responding:
            frame = responding[0]
            slots = _BlankDict({**globals_, **frame.slots})
            self._compute_slots(frame, slots, personality)
            self._record_answer(frame.rule, slots, user_id)
            core = self._choose_template(frame.rule, slots, level, user_id, policy, features)
            # "What's your favorite animal and why?"
            if frame.rule_id == "bot_favorite_question" and re.search(r"\band why\b|\? why\W*$", message, re.IGNORECASE):
                split = re.match(r"(.*[.!])\s+([^.!?]*\?)$", core)
                core = (f"{split.group(1)} I just think they're really cool! {split.group(2)}" if split
                        else f"{core} I just think they're really cool!")
            features["rule"] = frame.rule_id
            if frame.rule_id == "offer_content" and slots.get("kind") in ("joke", "riddle", "pun"):
                self._child_joke[user_id] = 1  # the next message is the child's joke
            if frame.rule_id == "play_pretend":
                self._pretend[user_id] = PRETEND_MAX_TURNS
            if frame.rule_id == "story_together" or (frame.rule_id == "request" and slots.get("kind") == "story"):
                self._story_mode[user_id] = 1  # the next messages are the child's story

            # Multi-sentence messages: also answer the strongest match in another sentence
            # ("I won my game today! Do you like soccer?")
            second = next((f for f in responding[1:]
                           if f.sentence != frame.sentence and f.priority >= SECOND_REPLY_MIN_PRIORITY), None)
            if second is not None:
                second_slots = _BlankDict({**globals_, **second.slots})
                self._compute_slots(second, second_slots, personality)
                self._record_answer(second.rule, second_slots, user_id)
                second_core = self._choose_template(second.rule, second_slots, level, user_id, policy, features)
                # Answer in the order the sentences were written
                core = f"{core} {second_core}" if frame.sentence < second.sentence else f"{second_core} {core}"
            valence = frame.valence
            use_opener = frame.rule.get("opener", False)
            follow_ups = frame.rule.get("follow_ups", [])
            by = frame.rule.get("follow_ups_by")
            if by:
                variants = by["variants"]
                follow_ups = variants.get(slots.get(by["slot"], ""), variants.get("default", follow_ups))
            stored_keys = {key for f in analysis.frames for (_, key, _) in f.memories}
        else:
            slots = _BlankDict(globals_)
            core, valence, kind = self._fallback(analysis, slots, allow_reflection, user_id, policy, features,
                                                 gentle=bool(context.get("sensitive")))
            features["rule"] = f"fallback_{kind}"
            use_opener = False
            follow_ups = []
            stored_keys = set()

        parts = []
        energy = getattr(personality, "energy", 0.5)
        if use_opener:
            openers = self.kb["openers"].get(valence, {}).get("high" if energy >= 0.5 else "low", [])
            # Not "Awesome! ... That's awesome!"
            openers = [o for o in openers if o.strip("!.").split(",")[0].lower() not in core.lower()]
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
        text = re.sub(rf",? ?{_NO_NAME}", "", text)
        text = re.sub(r"\b (['’](re|s|m|ve|ll|d))\b", r"\1", text)  # "you 're" -> "you're"
        return self._apply_style(text, personality)

    def _compute_slots(self, frame: Frame, slots: Dict[str, str], personality) -> None:
        seed_id = getattr(personality, "id", None) or getattr(personality, "user_id", 0) or 0
        for name in frame.rule.get("compute", []):
            if name == "bot_favorite":
                options = self.kb["bot_profile"]["favorites"].get(slots.get("category", ""))
                if options:
                    favorite = options[_stable_index(f"{seed_id}:{slots['category']}", len(options))]
                    # "the color orange" parses as a thing ("I like orange" does not)
                    mention = f"the {slots['category']} {favorite}" if slots["category"] in ("color", "number") else favorite
                    self._last_mentions[getattr(personality, "user_id", 0)] = [mention]
                    self._last_category[getattr(personality, "user_id", 0)] = slots["category"]
                    if _same_thing(favorite, slots.get("value_raw", "")):
                        slots["same_favorite"] = "yes"
                    else:
                        slots["bot_favorite"] = favorite
            elif name == "reciprocal":
                # "What's yours?" after the child named a favorite: the bot's favorite in that category
                category = self._last_category.pop(getattr(personality, "user_id", 0), None)
                options = self.kb["bot_profile"]["favorites"].get(category or "")
                if options:
                    slots["category"] = category
                    slots["bot_favorite"] = options[_stable_index(f"{seed_id}:{category}", len(options))]
            elif name == "recall_favorite":
                # "What's my favorite color?"
                facts = getattr(self, "_context", {}).get("known_facts") or {}
                value = facts.get(f"favorite_{slots.get('category_slug', '')}")
                if value:
                    slots["recalled"] = value
            elif name == "recall_thing":
                # "Do you remember my dog?": "your dog Max" (a named one), else "your dog"
                facts = getattr(self, "_context", {}).get("known_facts") or {}
                thing = slots.get("thing_slug", "")
                named = next((v for k, v in facts.items() if k.startswith(f"{thing}_")), None) if thing else None
                if not named and thing:
                    # Named earlier in this conversation ("I have a cat named Whiskers")
                    state = self.references.state(getattr(personality, "user_id", 0) or 0)
                    named = next((p.name for p in state.people
                                  if p.name and p.relation and p.relation.split()[-1] == thing), None)
                if named:
                    slots["recalled"] = f"your {slots.get('thing', thing)} {named}"
                    slots["recalled_name"] = named
                elif thing and any(k in (f"has_{thing}", f"likes_{thing}", f"favorite_{thing}") for k in facts):
                    slots["recalled"] = f"your {slots.get('thing', thing)}"
                elif thing:
                    # Told in an earlier conversation but not stored ("my spelling test")
                    noun = slots.get("thing_phrase") or slots.get("thing", thing)
                    earlier = getattr(self, "_context", {}).get("recent_messages") or []
                    if any(getattr(m, "role", "") == "user" and thing in (getattr(m, "content", "") or "").lower()
                           for m in earlier):
                        slots["recalled"] = noun if noun.split()[0].lower() in ("your", "the") else f"your {noun}"
            elif name == "gift_container":
                # "a goody bag" holds something; "a bike" does not
                if slots.get("gift_raw", "").lower().split()[-1:] in (["bag"], ["box"], ["basket"], ["stocking"]):
                    slots["gift_container"] = "yes"
            elif name == "birthday_timing":
                text = slots.get("message_text", "").lower()
                if re.search(r"\btoday\b", text):
                    slots["birthday_timing"] = "today"
                elif re.search(r"\b(tomorrow|next|soon|coming up|in \w+ (days?|weeks?))\b", text):
                    slots["birthday_timing"] = "upcoming"
            elif name == "requested_content":
                self._requested_content(slots.get("kind", ""), slots, user_id=getattr(personality, "user_id", 0))
            elif name == "joke_content":
                # "Tell me something funny"
                self._requested_content("joke", slots, user_id=getattr(personality, "user_id", 0))
            elif name == "count_to":
                # "Count to ten": the numbers, up to 30
                target = _number_value(slots.get("n_raw", ""))
                if target is not None and 1 <= target <= 30:
                    slots["counting"] = ", ".join(str(k) for k in range(1, target + 1))
            elif name == "rhymes":
                # "What rhymes with cat?": words from the same rhyme family
                word = slots.get("word_raw", "").lower()
                family = next((f for f in _RHYME_FAMILIES if word in f), None)
                if family:
                    others = [w for w in family if w != word][:4]
                    slots["rhymes"] = ", ".join(others[:-1]) + (" and " if len(others) > 1 else "") + others[-1]
            elif name == "fact_content":
                # "Tell me something cool"
                self._requested_content("fact", slots, user_id=getattr(personality, "user_id", 0))
            elif name == "repeat_request":
                kind = self._last_request.get(getattr(personality, "user_id", 0))
                if kind:
                    self._requested_content(kind, slots, user_id=getattr(personality, "user_id", 0))
            elif name == "bot_pick":
                options = [slots.get("x", ""), slots.get("y", "")]
                if all(options):
                    pair = ":".join(sorted(o.lower() for o in options))
                    slots["bot_pick"] = options[_stable_index(f"{seed_id}:{pair}", 2)]
                    self._last_mentions[getattr(personality, "user_id", 0)] = [slots["bot_pick"]]
            elif name == "bot_shares_like":
                thing = slots.get("thing_raw", "").lower()
                interests = [i.lower() for i in (personality.get_interests() if hasattr(personality, "get_interests") else [])]
                favorites = [v.lower() for vals in self.kb["bot_profile"]["favorites"].values() for v in vals]
                shares = any(word in thing for word in interests + favorites) or \
                    _stable_index(f"{seed_id}:{slots.get('thing_slug', '')}", 3) == 0
                if shares and thing:
                    slots["bot_shares_like"] = "yes"

    def _record_answer(self, rule: Dict[str, Any], slots: Dict[str, str], user_id: int) -> None:
        """
        Let the child refer to the bot's answer: a rule's "answer" names what its reply says
        from the child's point of view ("your name"), so "I like it" means "I like your name"
        """
        answer = rule.get("answer")
        if answer:
            self._last_mentions.setdefault(user_id, []).append(answer.format_map(slots))

    def _requested_content(self, kind: str, slots: Dict[str, str], user_id: int) -> None:
        """Fill {content} with a joke or fact (topical if the message names a topic)"""
        from services.fact_quirk_service import fact_quirk_service
        from services.pun_quirk_service import pun_quirk_service

        if kind == "riddle":
            question = self._pick([r[0] for r in RIDDLES], user_id)
            riddle, answer, accepted = next(r for r in RIDDLES if r[0] == question)
            slots["content"] = f"{riddle} Take a guess!"
            self._riddle[user_id] = (answer, accepted)
            self._last_told[user_id] = "riddle"
        elif kind in ("joke", "pun"):
            slots["content"] = pun_quirk_service.random_pun(slots.get("message_text", ""))
            self._last_told[user_id] = "joke"
        elif kind == "fact":
            slots["content"] = fact_quirk_service.random_fact(slots.get("message_text", ""))
            self._last_told[user_id] = "fun fact"
        else:
            return
        self._last_request[user_id] = kind

    def rule_flag(self, rule_id: Optional[str], flag: str) -> bool:
        """A rule's boolean option from the knowledge base (e.g. "no_jokes")"""
        # Answers to questions about the world and the child's own joke get no joke added
        # and replies repeating back the child's news ("The present was a book about sharks?")
        if flag == "no_jokes" and rule_id and (
                rule_id.startswith(("fallback_world", "fallback_reflection", "fallback_long_reflection", "fallback_fragment",
                                    "fallback_appraisal", "fallback_continuation"))
                or rule_id in ("child_joke", "riddle_answer", "joke_offer_yes", "spelling", "performance", "play_role", "pretend")):
            return True
        return bool(rule_id and self.rules.get(rule_id, {}).get(flag))

    def _decide(self, feature: str, probability: float, policy) -> bool:
        """
        Yes/no choice for an optional part of a reply. Uses the personality-based probability
        until the policy has enough engagement data for both options, then Thompson sampling
        with that probability as the prior.
        """
        if policy is not None and policy.has_data(feature, ["yes", "no"]):
            return policy.decide(feature, probability)
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
            if any(slots.get(slot) for slot in spec.get("unless", [])):
                continue  # a template for when something is not known
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
        learned = (feature is not None and policy is not None and len(options) > 1
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
                  policy=None, features: Optional[Dict[str, str]] = None,
                  gentle: bool = False) -> Tuple[str, str, str]:
        """
        Reply when no rule matched. Returns (text, valence, fallback kind). gentle: the child
        said something sad recently, so reflections do not ask "What happened next?"
        """
        fallbacks = self.kb["fallbacks"]
        doc = analysis.doc

        def pick(kind: str) -> str:
            return self._pick(fallbacks[kind], user_id, f"template:fallback_{kind}", policy, features)

        # "What if I get lost?": a worry, answered by the appraisal templates
        if analysis.is_question and allow_reflection:
            appraisal = self.appraiser.appraise(doc)
            if appraisal is not None and appraisal.modality == appraisal_module.HYPOTHETICAL:
                composed = self._appraisal_reply(doc, slots, user_id, policy, features, gentle)
                if composed is not None:
                    return composed

        if analysis.is_question:
            # "Why is the sky blue?": a known answer, a fact on the topic, or "let's look it up"
            about_bot = any(t.lower_ in ("you", "your", "yours", "yourself") for t in doc)
            # "How do I get him to stop?" is about the child's life, not the world
            personal = any(t.lower_ in ("i", "me", "my", "mine") for t in doc) and not self._world_answer(doc.text)
            # An answer written for a "you" question ("How much money do you get from the tooth fairy?")
            generic_you = any(p.search(doc.text) and "you" in p.pattern for p, _ in self.answers)
            if (not about_bot or generic_you or re.match(r"(do|did) you know\b", doc.text, re.IGNORECASE)) and not personal:
                answer = self._world_answer(doc.text)
                if answer:
                    return answer, "neutral", "world_answer"
                if any(t.tag_ in ("WRB", "WP", "WDT") for t in doc) or doc[0].lemma_ in ("do", "be", "can"):
                    from services.fact_quirk_service import fact_quirk_service
                    fact = fact_quirk_service.contextual_fact(doc.text)
                    if fact:
                        slots["fact"] = fact
                        return pick("world_question_fact").format_map(slots), "neutral", "world_question_fact"
                    if any(t.tag_ in ("WRB", "WP", "WDT") for t in doc):
                        return pick("world_question"), "neutral", "world_question"
            return pick("question"), "neutral", "question"

        # "with marshmallows" right after "and had hot chocolate": part of that thing
        words = [t for t in doc if not t.is_punct]
        # "and stay up late" after "we are going to watch a movie": more of the plan
        if (allow_reflection and 2 <= len(words) <= 6 and words[0].lower_ in ("and", "then", "also")
                and words[1].pos_ == "VERB" and words[1].tag_ == "VB"):
            rest = " ".join(self._reflect_token(t) for t in words[1:])
            return f"{rest[:1].upper()}{rest[1:]} too? That sounds like so much fun!", "positive", "fragment"
        if allow_reflection and 2 <= len(words) <= 4 and words[0].lower_ == "with":
            state = self.references.state(user_id)
            # The thing from an earlier message, not this one's own "marshmallows"
            thing = next((t for t in state.things if not t.added and not t.short and t.turn < state.turn), None)
            _, extra = self._extract_slot(words[0], "subtree")
            if thing is not None and thing.text.split()[-1].lower() in self.kb["lexicons"].get("foods", []):
                name = " ".join(w for w in thing.text.split() if w.lower() not in ("the", "a", "an"))
                return f"Ooh, {name} {extra}? Yum, that sounds so good!", "positive", "fragment"
            return f"{extra[:1].upper()}{extra[1:]}? That sounds fun!", "positive", "fragment"

        # A fragment continuing the previous message ("next week", "to the zoo")
        if allow_reflection:
            continued = self._continuation_reply(doc, slots, user_id, policy, features, gentle)
            if continued is not None:
                return continued

        # What happened, in general terms: a reply for its kind of event and modality
        if allow_reflection:
            composed = self._appraisal_reply(doc, slots, user_id, policy, features, gentle)
            if composed is not None:
                return composed

        # Reflect the last sentence that is short and about the child
        if allow_reflection:
            for sentence in reversed(list(doc.sents)):
                root = sentence.root
                if (len(sentence) <= 15 and root.pos_ in ("VERB", "AUX")
                        and (self._first_person_subject(root) or self._known_person_subject(root, user_id)
                             or self._definite_thing_subject(root) or self._done_to_child(root)
                             or any(c.dep_ == "nsubj" and c.pos_ == "PROPN" and c.lower_ != "buddy"
                                    for c in root.children))):
                    _, clause = self._extract_slot(root, "clause")
                    slots["clause"] = clause
                    # A follow-up that fits: "How did that go?" only for what already happened
                    if emoji_quirk_service.is_negative(sentence.text) and not self._is_negated(root):
                        kind = "reflection_sad"
                    elif gentle:
                        kind = "reflection_gentle"
                    else:
                        tense = self._tense(root)
                        kind = "reflection" if tense == "past" else f"reflection_{tense}"
                        # "He is a golden retriever": not "What's that like?"
                        # "He is a golden retriever", "It was so tall": not "What's that like?"
                        describes = root.lemma_ == "be" or (
                            root.lemma_ == "have" and not self._first_person_subject(root)) or (
                            root.lemma_ in ("feel", "look", "sound", "smell", "taste", "seem")
                            and any(c.dep_ == "acomp" for c in root.children)
                            and not self._first_person_subject(root))
                        if describes and kind in ("reflection_present", "reflection"):
                            kind = "reflection_be"
                        # "Santa is coming", "my cat sleeps on my bed": not "What's that like?"
                        elif kind == "reflection_present" and not self._first_person_subject(root):
                            kind = "reflection_present_other"
                        # "We can't go to the park", "I don't have one"
                        elif self._is_negated(root) and (
                                any(c.lower_ in ("ca", "can", "could") for c in root.children)
                                or (root.lemma_ == "have" and self._first_person_subject(root))):
                            kind = "reflection_cant"
                    return pick(kind).format_map(slots), "neutral", kind

        # Long sentences: echo the last clause about the child ("...and then I fell down")
        if allow_reflection:
            clause = self._last_clause_about_child(doc)
            if clause:
                slots["clause"] = clause
                return pick("long_reflection").format_map(slots), "neutral", "long_reflection"

        # "She was nice" right after "Maya and Jake came over": ask which one
        options = self.references.ambiguous_options(user_id)
        if options:
            slots["options"] = options[0] if len(options) == 1 else \
                f"{', '.join(options[:-1])} or {options[-1]}"
            # "He scratched me": care first, then the question
            if any(t.lemma_ in _HURT_VERBS for t in doc) or emoji_quirk_service.is_negative(doc.text):
                return pick("ambiguous_person_upset").format_map(slots), "negative", "ambiguous_person"
            return pick("ambiguous_person").format_map(slots), "neutral", "ambiguous_person"

        # A he/she/they the reference tracker could not resolve
        # (not a generic "they gave me a toothbrush" at the dentist)
        if any(t.lower_ in ("he", "she", "they") and t.dep_ in ("nsubj", "nsubjpass")
               and not (t.lower_ == "they" and t.head.lemma_ in ("give", "bring", "let", "show", "teach", "hand"))
               for t in doc):
            return pick("unknown_person"), "neutral", "unknown_person"

        if allow_reflection:
            chunks = [c for c in doc.noun_chunks if c.root.pos_ != "PRON"]
            if chunks:
                slots["topic"] = self._join(list(chunks[-1]), reflect=True)
                # "purple monkey dishwasher": words that don't go together, said for fun
                words = [t.lower_ for t in doc if t.is_alpha]
                kinds = {kind for word in words for kind, group in _SILLY_GROUPS.items() if word in group}
                if 3 <= len(words) <= 5 and len(kinds) >= 2 and not any(t.pos_ in ("VERB", "AUX", "DET") for t in doc):
                    slots["topic"] = slots["topic"][:1].upper() + slots["topic"][1:]
                    return pick("silly").format_map(slots), "positive", "silly"
                return pick("topic").format_map(slots), "neutral", "topic"

        return pick("generic"), "neutral", "generic"

    def _appraisal_reply(self, doc, slots: Dict[str, str], user_id: int, policy=None,
                         features: Optional[Dict[str, str]] = None, gentle: bool = False,
                         clause: Optional[str] = None, kind_prefix: str = "appraisal",
                         root=None) -> Optional[Tuple[str, str, str]]:
        """
        A reply from the appraisal of the message (see services/appraisal.py): templates by kind
        of event, modality and who did what to whom, tried from most to least specific. None
        when the message names no kind of event the knowledge base knows, so plainer
        fallbacks (echoing the child's words) can reply.
        """
        if root is not None:
            appraisal = self.appraiser.appraise_tokens(root, self._pet_names(user_id))
        else:
            appraisal = self.appraiser.appraise(doc, self._pet_names(user_id))
        if appraisal is None:
            return None
        root = appraisal.root
        # Someone the reference tracker could not resolve: ask who first
        subject = next((c for c in root.children if c.dep_ in ("nsubj", "nsubjpass")), None)
        if subject is not None and subject.lower_ in ("he", "she", "they"):
            return None
        if appraisal.question and appraisal.modality != appraisal_module.HYPOTHETICAL:
            return None
        # Long or mixed messages ("he fell down but he was ok"): plainer replies pick out a part
        sentence = root.sent
        if clause is None and (len(sentence) > 15 or any(
                t.lower_ == "but" and t.dep_ == "cc" for t in sentence)):
            return None
        # Nothing known about what happened: plainer replies echo it ("We're having a party? Tell me more!")
        if appraisal.action is None and appraisal.modality in (appraisal_module.REAL, appraisal_module.FUTURE,
                                                               appraisal_module.OBLIGATION):
            return None
        # After sad news, "we visited him" (in the hospital) is not "That sounds like so much fun!"
        if gentle and appraisal.valence == "positive" and appraisal.modality == appraisal_module.REAL \
                and appraisal.action == "fun" and (appraisal.target in ("person", "pet") or root.lemma_ == "visit"):
            return None
        templates = self.kb.get("appraisal", {}).get("templates", {})
        key = self._appraisal_template_key(appraisal, templates)
        if key is None:
            return None
        if clause is None:
            # "You have to clean your room?", not "To clean your room?"
            clause_root = root if appraisal.modality == appraisal_module.REAL else (
                next((t for t in [root, *root.ancestors] if t.dep_ == "ROOT"), root))
            _, clause = self._extract_slot(clause_root, "clause")
        slots["clause"] = clause
        text = self._pick(templates[key], user_id, f"template:appraisal_{key}", policy, features).format_map(slots)
        text = text[:1].upper() + text[1:]
        return text, appraisal.valence, f"{kind_prefix}_{appraisal.action or 'any'}_{appraisal.modality}"

    def _pet_names(self, user_id: int) -> List[str]:
        """Names of the child's pets the reference tracker knows ("Milo")"""
        pets = set(self.kb.get("appraisal", {}).get("pets", []))
        return [p.name for p in self.references.state(user_id).people
                if p.name and p.relation and p.relation.split()[-1] in pets]

    @staticmethod
    def _appraisal_template_key(a: Appraisal, templates: Dict[str, List[str]]) -> Optional[str]:
        """The most specific template key for an appraisal, or None"""
        modality = "negated" if a.modality == appraisal_module.REAL and a.negated else a.modality
        candidates = []
        if a.notes.get("accident") and modality == appraisal_module.REAL:
            candidates += [f"{a.action}.accident", "*.accident"]
        if a.notes.get("habit") and modality == "negated":
            candidates += [f"{a.action}.never", "*.never"]
        if a.action:
            base = f"{a.action}.{modality}"
            candidates += [f"{base}.{a.actor}>{a.target}", f"{base}.{a.actor}>", f"{base}.>{a.target}",
                           f"{base}.{a.tense}", base]
        if a.notes.get("wanter") == "other":
            candidates.insert(0, f"*.{modality}.other")
        if modality != "negated" and modality != appraisal_module.REAL:
            candidates += [f"*.{modality}.{a.actor}>", f"*.{modality}.{a.valence}", f"*.{modality}"]
        return next((c for c in candidates if c in templates), None)

    def _phrase_reply(self, message: str, user_id: int) -> Optional[Tuple[str, str]]:
        """(phrase id, reply) when the whole message is a set phrase from the knowledge base, else None"""
        text = re.sub(r"[^\w' ]+", " ", message.lower()).replace("\u2019", "'")
        text = re.sub(r"\s+(buddy|bud)$", "", " ".join(text.split()))
        if not text or len(text.split()) > 7:
            return None
        for phrase_id, pattern, replies in self._phrases:
            if pattern.fullmatch(text):
                return f"phrase_{phrase_id}", self._pick(replies, user_id, f"phrase:{phrase_id}")
        return None

    def _answer_expectation(self, expectation: "Expectation", message: str, analysis: Analysis,
                            user_id: int) -> Optional[Tuple[str, str]]:
        """
        (rule id, reply) when the message answers an offer or a listening request: "yes" to
        "Want to hear a funny joke?", "a riddle" to "a joke, a riddle, or a fun fact?", the
        child's line after "I'd love to hear it". None otherwise.
        """
        if expectation.kind == "listen" and not analysis.is_question and len(message.split()) <= 25:
            return "performance", "Bravo! That was great! You're going to do awesome."
        if expectation.kind not in ("offer", "choice"):
            return None
        kind = None
        if expectation.kind == "choice":
            chosen = next((o for o in expectation.options if re.search(rf"\b{o}s?\b", message, re.IGNORECASE)), None)
            if chosen and len(message.split()) <= 6:
                kind = chosen
            elif _YES_RE.match(message):
                kind = expectation.options[0]
        elif _YES_RE.match(message):
            kind = expectation.offer if expectation.offer != "again" else self._last_request.get(user_id)
        if not kind:
            return None
        content = {}
        self._requested_content(kind, content, user_id)
        if not content.get("content"):
            return None
        return "joke_offer_yes", f"Okay, here's one: {content['content']}"

    def _answer_open_question(self, expectation: "Expectation", analysis: Analysis) -> Optional[Tuple[str, str]]:
        """
        (rule id, reply) for a short answer to the bot's "What ...?" or "Why ...?" question,
        or None if the message does not read as one
        """
        doc = analysis.doc
        words = [t for t in doc if not t.is_punct]
        if analysis.is_question or not words or len(words) > 10:
            return None
        if expectation.kind == "reason":
            # "Why is Saturn your favorite?" - "it has rings" / "because it has rings"
            root = next((t for t in doc if t.dep_ == "ROOT"), None)
            if root is None or root.pos_ not in ("VERB", "AUX"):
                return "answer_reason", "Ooh, that's a good reason!"
            _, clause = self._extract_slot(root, "clause")
            clause = re.sub(r"^(because|cuz|cause) ", "", clause, flags=re.IGNORECASE)
            return "answer_reason", f"Ooh, that's a good reason! {clause[:1].upper()}{clause[1:]}? Cool!"
        # An item: "a tree", "I'm a tree", "a ninja", "probably the red one"
        match = re.match(r"\W*(?:i'm|i am|im|i'll be|it's|its|it is|maybe|probably|um+|uh+)?\s*"
                         r"(?:going to be |gonna be |playing |be )?((?:an?|the|my) )?([a-z][a-z' -]{1,30}?)[.!]*$",
                         doc.text, re.IGNORECASE)
        if match is None or any(t.pos_ == "VERB" and t.lemma_ not in ("be", "play") for t in doc):
            return None
        item = f"{(match.group(1) or '').lower()}{match.group(2).strip()}"
        item = re.sub(r"^my ", "your ", item)
        noun = expectation.noun
        tail = f"That sounds like a fun {noun}!" if noun else "That sounds awesome!"
        return "answer_item", f"{item[:1].upper()}{item[1:]}! {tail}"

    def _continuation_reply(self, doc, slots: Dict[str, str], user_id: int, policy=None,
                            features: Optional[Dict[str, str]] = None,
                            gentle: bool = False) -> Optional[Tuple[str, str, str]]:
        """
        A fragment that continues the child's previous message ("next week" after "we're going
        to Disneyland", "to the zoo" after "we went on a field trip"): appraised together with
        it, with the fragment echoed back
        """
        words = [t for t in doc if not t.is_punct]
        if not words or len(words) > 6 or any(
                t.pos_ in ("VERB", "AUX") and any(c.dep_ in ("nsubj", "nsubjpass") for c in t.children) for t in doc):
            return None
        previous = self._previous_message.get(user_id)
        if not previous or not (words[0].lower_ in _CONTINUATION_WORDS or not any(
                t.pos_ in ("VERB", "AUX") for t in doc)):
            return None
        previous = previous.rstrip(" .!?")
        combined = self.parser.parse(f"{previous} {doc.text}")
        previous_doc = self.parser.parse(previous)
        if combined is None or previous_doc is None or len(combined) != len(previous_doc) + len(doc):
            return None
        fragment_words = [t for t in words if t.lower_ not in ("and", "then", "also", "so")]
        fragment = self._join(fragment_words, reflect=True)
        if not fragment:
            return None
        verb = next((t for t in doc if t.pos_ == "VERB"), None)
        if verb is not None:
            # "and had hot chocolate" after "we made snow angels": about having the hot chocolate
            if fragment_words[0].i != verb.i:
                return None
            combined_verb = combined[len(previous_doc) + verb.i]
            subject = self.appraiser.subject(combined_verb)
            who = self._reflect_token(subject) if subject is not None else ""
            clause = f"{who} {fragment}".strip()
            return self._appraisal_reply(combined, slots, user_id, policy, features, gentle,
                                         clause=clause, kind_prefix="continuation",
                                         root=combined_verb)
        return self._appraisal_reply(combined, slots, user_id, policy, features, gentle,
                                     clause=fragment, kind_prefix="continuation")

    def _pretend_reply(self, message: str) -> Optional[str]:
        """A line in a game of pretend: take the role the child gives, cheer the child's role, or keep it going"""
        text = message.lower()
        bot_role = re.search(r"\byou(?:'re| are|re) (a|an|the) ([a-z ]{2,25}?)[.!?]*$", text)
        if bot_role:
            role = bot_role.group(2).strip()
            sound = _PRETEND_SOUNDS.get(role.split()[-1], "")
            return f"{sound + ' ' if sound else ''}Okay, I'm {bot_role.group(1)} {role}! Who are you?"
        child_role = re.search(r"\bi(?:'m| am|m) (a|an|the) ([a-z ]{2,25}?)[.!?]*$", text)
        if child_role:
            return f"Ooh, {child_role.group(1)} {child_role.group(2).strip()}! What happens next?"
        if re.search(r"\b(attack|fight|hit|zap|chase)\b", text) and re.search(r"\byou\b", text):
            return "Whoosh! I dodge out of the way! Your turn!"
        return self._pick(PRETEND_PROMPTS, 0)

    @staticmethod
    def _compare_fractions(match) -> str:
        """ "Is 1/2 bigger than 1/4?" -> "Yes! 1/2 is bigger than 1/4." """
        a, b, word, c, d = match.groups()
        if int(b) == 0 or int(d) == 0:
            return "Hmm, you can't split something into zero parts! Try another one?"
        left, right = int(a) / int(b), int(c) / int(d)
        bigger = word.lower() in ("bigger", "larger", "more", "greater")
        first, second = f"{a}/{b}", f"{c}/{d}"
        if left == right:
            return f"They're the same size! {first} and {second} are equal."
        true = (left > right) == bigger
        relation = "bigger" if left > right else "smaller"
        reply = f"{'Yes' if true else 'Nope'}! {first} is {relation} than {second}."
        if a == c == "1":
            reply += " When you split something into more pieces, each piece gets smaller!"
        return reply

    def _world_answer(self, text: str) -> Optional[str]:
        """The answer to a common question about the world ("Why is the sky blue?"), if known"""
        # "What's a fraction?" matches patterns written as "what is"
        expanded = re.sub(r"\b(what|where|who|how|when|why)'s\b", r"\1 is", text, flags=re.IGNORECASE)
        for pattern, answer in self.answers:
            if pattern.search(text) or pattern.search(expanded):
                return answer
        return None

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
                      if t.i not in joined and not _skipped(t)
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
