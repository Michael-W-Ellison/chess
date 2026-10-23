"""
Utterance Parser
Turns a user message into a dependency parse tree with spaCy

The parse is the input analysis layer for the rule-based response engine:
each token carries its base form (lemma), part of speech, dependency relation
and head, so rules can match sentence structure instead of exact wording.

spaCy and its English model are optional. If they are not installed,
is_available() returns False and callers fall back to keyword handling.
"""

import logging
import re
from functools import lru_cache

logger = logging.getLogger("chatbot.utterance_parser")

MODEL_NAME = "en_core_web_sm"

# Common spellings in children's messages, mapped to standard forms the parser knows
NORMALIZATIONS = {
    "i": "I",
    "im": "I'm",
    "ive": "I've",
    "dont": "don't",
    "cant": "can't",
    "wont": "won't",
    "didnt": "didn't",
    "doesnt": "doesn't",
    "isnt": "isn't",
    "wasnt": "wasn't",
    "luv": "love",
    "u": "you",
    "ur": "your",
    "r": "are",
    "becuz": "because",
    "becoz": "because",
    "cuz": "because",
    "bc": "because",
    "wanna": "want to",
    "gonna": "going to",
    "gotta": "got to",
    "fav": "favorite",
    "fave": "favorite",
    "favourite": "favorite",
    "colour": "color",
    "pls": "please",
    "plz": "please",
    "bday": "birthday",
    "bro": "brother",
    "sis": "sister",
    "shes": "she's",
    "hes": "he's",
    "theyre": "they're",
    "thats": "that's",
    "whats": "what's",
    "idk": "I don't know",
    "nm": "not much",
    "rn": "right now",
    "gtg": "got to go",
    "g2g": "got to go",
    "ttyl": "talk to you later",
    "brb": "be right back",
    "jk": "just kidding",
    # Common misspellings and texting shortcuts
    "lik": "like",
    "liek": "like",
    "alot": "a lot",
    "bilt": "built",
    "hous": "house",
    "rlly": "really",
    "rly": "really",
    "realy": "really",
    "becuase": "because",
    "beacuse": "because",
    "frend": "friend",
    "freind": "friend",
    "frends": "friends",
    "freinds": "friends",
    "skool": "school",
    "wat": "what",
    "wut": "what",
    "sumthing": "something",
    "somthing": "something",
    "gud": "good",
    "kool": "cool",
    "prolly": "probably",
    "probly": "probably",
    "tmrw": "tomorrow",
    "tmr": "tomorrow",
    "tomorow": "tomorrow",
    "tommorow": "tomorrow",
    "2day": "today",
    "2morrow": "tomorrow",
    "b4": "before",
    "gr8": "great",
    "nvm": "never mind",
    "ppl": "people",
    "cya": "bye",
    "thx": "thanks",
    "ty": "thank you",
    "favrite": "favorite",
    "favorit": "favorite",
    "pizzza": "pizza",
    "sooo": "so",
    "soo": "so",
    "verry": "very",
    "vary": "very",
    "dinosour": "dinosaur",
    "dinosours": "dinosaurs",
    "minecraf": "minecraft",
}

_EMOJI_WORDS = {
    **dict.fromkeys("😂🤣😆😄😁😹", "haha"),
    **dict.fromkeys("😊🙂😀😃☺", "I am happy"),
    **dict.fromkeys("👍👌✅", "ok"),
    **dict.fromkeys("❤💕💖💗💙💜🥰😍😻", "aww"),
    **dict.fromkeys("😢😭😞😔☹🙁😿💔", "I am sad"),
    **dict.fromkeys("😡😠🤬", "I am mad"),
    **dict.fromkeys("😱😨😰", "I am scared"),
    **dict.fromkeys("😴🥱", "I am sleepy"),
    **dict.fromkeys("🤔", "hmm"),
    **dict.fromkeys("👋", "hi"),
    **dict.fromkeys("😮😲🤯", "wow"),
}

# "hiii", "heyyy", "hellooo": a greeting, not a name
_STRETCHED_GREETINGS = [
    (re.compile(r"^h+i+$", re.IGNORECASE), "hi"),
    (re.compile(r"^h+e+y+$", re.IGNORECASE), "hey"),
    (re.compile(r"^h+e+l+o+$", re.IGNORECASE), "hello"),
    (re.compile(r"^b+y+e+$", re.IGNORECASE), "bye"),
    (re.compile(r"^y+o+$", re.IGNORECASE), "yo"),
]
# Emoji and other pictographs: not words, so they are not echoed back ("Your cat is fluffy 😻?")
_EMOJI_RE = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u200D\u2B50\u2764]")

# Spellings that are also words, replaced only where the next word shows which is meant:
# "its so fun" (it's), "ill try" (I'll); "its wings" and "I feel ill" stay
_CONTEXT_NORMALIZATIONS = [
    (re.compile(r"\bits(?= (so|really|very|not|too|just|a|an|the|my|ok|okay|fine|fun|boring|hard|easy|cool|"
                r"great|good|bad|true|time|going|gonna|like|always|never|raining|snowing|gross|yummy|awesome|"
                r"amazing|weird|scary|funny|cute|about|mine|yours|over|super|kind|pretty)\b)", re.IGNORECASE),
     "it's"),
    (re.compile(r"\bur(?= (so|really|very|not|the|a|an|my|weird|cool|funny|nice|mean|smart|awesome|silly|dumb|"
                r"stupid|annoying|best|worst|welcome|right|wrong|crazy|lying|kidding|joking|amazing|great|good|"
                r"bad|too)\b)", re.IGNORECASE),
     "you're"),
    (re.compile(r"\bill(?= (try|do|be|go|ask|tell|practice|study|see|talk|play|have|get|make|show|let|just|never|"
                r"always|probably|draw|read|call|text|come|help|work|remember|eat|drink|wait|clean|finish|sleep|bring|"
                r"buy|use|build|write|stop|take|give|send|keep|think|put|pick|sit|stay|watch|listen|look|fix|"
                r"share|win|beat|check|miss|need|wear|sing|dance|run|swim|ride)\b)", re.IGNORECASE),
     "I'll"),
]
# "my moms room" -> "my mom's room"
_POSSESSIVE_RE = re.compile(
    r"\b(mom|dad|mommy|daddy|sister|brother|grandma|grandpa|friend|cousin|aunt|uncle)s (?=(room|house|car|bed|"
    r"phone|office|work|birthday|friend|dog|cat|toys?|lap|side)\b)", re.IGNORECASE
)
_QUESTION_START_RE = re.compile(r"^(what|how|where|when|why|who|do|does|are|is|can|will)\b", re.IGNORECASE)
_JOINED_QUESTION_RE = re.compile(
    r",?\s+and\s+(?=(how|what|where|when|why|who|do you|are you|can you|will you)\b)", re.IGNORECASE
)
# "a snowman named frosty" -> "a snowman named Frosty"
_NAMED_RE = re.compile(r"\b(named|called) (?!(after|it|him|her|them|me|you|us|that|this|what|a|an|the|my)\b)([a-z])")
# "their names are luna and milo" -> "their names are Luna and Milo"
_NAMES_ARE_RE = re.compile(r"\b(names are) ([a-z]+) and ([a-z]+)\b")
# Places a child may name in lowercase
_PLACES = ["alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut", "delaware",
           "florida", "georgia", "hawaii", "idaho", "illinois", "indiana", "iowa", "kansas", "kentucky",
           "louisiana", "maine", "maryland", "massachusetts", "michigan", "minnesota", "mississippi", "missouri",
           "montana", "nebraska", "nevada", "ohio", "oklahoma", "oregon", "pennsylvania", "tennessee", "texas",
           "utah", "vermont", "virginia", "washington", "wisconsin", "wyoming", "canada", "mexico", "england",
           "france", "spain", "italy", "germany", "china", "japan", "india", "australia", "brazil", "africa",
           "europe", "disneyland", "disney world", "new york", "chicago", "paris", "london", "hawaii"]
_PLACES_RE = re.compile(r"\b(" + "|".join(sorted(set(_PLACES), key=len, reverse=True)) + r")\b")
# "its math" (a whole message): "it's math"
_ITS_ALONE_RE = re.compile(r"^its (?=[a-z]*[a-rt-z][.!]*$)", re.IGNORECASE)  # not "its wings"
# "mr kim" -> "Mr Kim", so the parser reads a name
_TITLE_RE = re.compile(r"\b(mr|mrs|ms|dr)\.? ([a-z])", re.IGNORECASE)

_WORD_RE = re.compile(r"[A-Za-z]+")


def repair_parse(doc):
    """
    Fix a parse error the small English model makes with "had"/"has" as the main verb:
    in "The cupcakes had sprinkles" and "The pizza had pepperoni" it reads "had" as a helper
    verb and the object as the root. The helper becomes the root and the object its object.
    """
    for sentence in list(doc.sents):
        root = sentence.root
        helper = next((c for c in root.children if c.dep_ == "aux" and c.lemma_ == "have"), None)
        subject = next((c for c in root.children if c.dep_ == "nsubj"), None)
        # "I had eaten" (a real helper) has a past participle; "had sprinkles" does not
        if helper is None or subject is None or root.tag_ in ("VBN", "VBG") or helper.i > root.i:
            continue
        if any(c.dep_ in ("dobj", "aux") and c.i != helper.i for c in root.children):
            continue
        movers = [c for c in root.children
                  if c.i < root.i and c.i != helper.i and c.dep_ in ("nsubj", "neg", "advmod", "aux", "cc")]
        movers += [c for c in root.children if c.dep_ == "punct" and c.i > root.i]
        helper.head = helper
        helper.dep_ = "ROOT"
        helper.pos_ = "VERB"
        for token in movers:
            token.head = helper
        root.head = helper
        root.dep_ = "dobj"
        if root.pos_ == "VERB":
            root.pos_ = "NOUN"
            root.tag_ = "NNS" if root.text.lower().endswith("s") else "NN"
    _repair_objects(doc)
    return doc


_GIVING_VERBS = {"make", "get", "buy", "give", "bring", "send", "show", "cook", "bake", "read", "sing", "draw"}


def _repair_objects(doc) -> None:
    """
    Three more errors of the small model:
    "My dad made me soup": "soup" a clause with "me" its subject -> "me" the dative, "soup" the object
    "I want to name her Lily": "her" Lily's possessive -> "her" the object, "Lily" the name (oprd)
    "What game do you like": "you" the object of "do" -> the subject of "like"
    """
    for token in doc:
        # "brought me a present": "present" read as an adjective
        if token.dep_ == "dobj" and token.pos_ == "ADJ" and any(c.dep_ == "det" for c in token.children):
            token.pos_ = "NOUN"
            token.tag_ = "NN"
        if (token.dep_ == "ccomp" and token.pos_ == "NOUN" and token.head.lemma_ in _GIVING_VERBS
                and token.head.i < token.i):
            pronoun = next((c for c in token.children if c.dep_ == "nsubj"
                            and c.lower_ in ("me", "him", "her", "us", "them")), None)
            if pronoun is not None:
                pronoun.head = token.head
                pronoun.dep_ = "dative"
                token.dep_ = "dobj"
        elif (token.dep_ == "dobj" and token.head.lemma_ in ("name", "call") and token.head.pos_ == "VERB"
              and token.i == max(t.i for t in doc if not t.is_punct)):
            pronoun = next((c for c in token.children if c.dep_ == "poss" and c.lower_ == "her"), None)
            if pronoun is not None:
                pronoun.head = token.head
                pronoun.dep_ = "dobj"
                token.dep_ = "oprd"
        elif (token.lower_ in ("you", "i") and token.dep_ == "dobj" and token.head.lemma_ == "do"
              and token.head.dep_ == "aux"):
            verb = token.head.head
            if not any(c.dep_ == "nsubj" for c in verb.children):
                token.head = verb
                token.dep_ = "nsubj"


class UtteranceParser:
    """Lazily loads spaCy and parses normalized user messages"""

    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self._nlp = None
        self._load_failed = False
        self._known_words = None

    def is_available(self) -> bool:
        """Return True if spaCy and the language model can be loaded"""
        return self._get_nlp() is not None

    def _get_nlp(self):
        if self._nlp is None and not self._load_failed:
            try:
                import spacy

                self._nlp = spacy.load(self.model_name)
                logger.info(f"Loaded spaCy model {self.model_name}")
            except Exception as e:  # ImportError or missing model (OSError)
                self._load_failed = True
                logger.warning(f"spaCy model {self.model_name} unavailable: {e}")
        return self._nlp

    @staticmethod
    def normalize(text: str) -> str:
        """Collapse whitespace and replace common child spellings word by word"""
        # A message of only emoji: the first one in words ("😂" -> "haha", "😢" -> "I am sad")
        if not any(c.isalnum() for c in text):
            for char in text:
                if char in _EMOJI_WORDS:
                    return _EMOJI_WORDS[char]
        text = " ".join(_EMOJI_RE.sub(" ", text).split())
        # ALL CAPS ("I GOT A PUPPY TODAY") parses badly; read it as lowercase
        letters = [c for c in text if c.isalpha()]
        if len(letters) >= 4 and sum(c.isupper() for c in letters) >= 0.8 * len(letters):
            text = re.sub(r"\bi\b", "I", text.lower())
        text = " ".join(next((r for p, r in _STRETCHED_GREETINGS if p.match(w)), w) for w in text.split())

        def replace(match):
            word = match.group(0)
            if word.lower() == "ur":
                return word  # "ur weird" (you're) or "ur dog" (your): decided below by the next word
            return NORMALIZATIONS.get(word.lower(), word)

        # Spellings first, so "its rlly big" reads "its really big" before "its" -> "it's"
        text = _WORD_RE.sub(replace, text)
        for pattern, replacement in _CONTEXT_NORMALIZATIONS:
            text = pattern.sub(replacement, text)
        text = re.sub(r"\bur\b", "your", text, flags=re.IGNORECASE)
        text = _POSSESSIVE_RE.sub(r"\1's ", text)
        text = _NAMED_RE.sub(lambda m: f"{m.group(1)} {m.group(3).upper()}", text)
        text = _NAMES_ARE_RE.sub(lambda m: f"{m.group(1)} {m.group(2).capitalize()} and {m.group(3).capitalize()}", text)
        text = _PLACES_RE.sub(lambda m: m.group(1).title(), text)
        text = _ITS_ALONE_RE.sub("it's ", text)
        text = _TITLE_RE.sub(lambda m: f"{m.group(1).capitalize()} {m.group(2).upper()}", text)
        # "what's your name and how old are you": two questions, answered one by one
        if _QUESTION_START_RE.match(text):
            text = _JOINED_QUESTION_RE.sub("? ", text)
        return text

    def parse(self, text: str):
        """
        Parse a message into a spaCy Doc

        Returns:
            spaCy Doc, or None if the parser is unavailable or the text is empty
        """
        if not text or not text.strip():
            return None
        if self._get_nlp() is None:
            return None
        return self._parse_cached(self.normalize(text))

    @lru_cache(maxsize=256)
    def _parse_cached(self, normalized_text: str):
        return repair_parse(self._nlp(normalized_text))

    @property
    def vocab(self):
        nlp = self._get_nlp()
        return nlp.vocab if nlp is not None else None

    def known_words(self) -> set:
        """
        Lowercase English words the model knows: the lemmatizer's word lists (base forms
        and irregular forms, from WordNet), its stop words and the child spellings in
        NORMALIZATIONS. Empty if the model is unavailable.
        """
        if self._known_words is not None:
            return self._known_words
        nlp = self._get_nlp()
        if nlp is None:
            return set()
        words = {w.lower() for w in nlp.Defaults.stop_words} | set(NORMALIZATIONS)
        if "lemmatizer" in nlp.pipe_names:
            lookups = nlp.get_pipe("lemmatizer").lookups
            for table_name in ("lemma_index", "lemma_exc"):
                if lookups.has_table(table_name):
                    table = lookups.get_table(table_name)
                    for pos in table.keys():
                        words.update(w.lower() for w in table[pos])
        self._known_words = words
        return words


# Global instance
utterance_parser = UtteranceParser()
