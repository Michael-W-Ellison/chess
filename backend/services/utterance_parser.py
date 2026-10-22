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
}

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
                r"always|probably|draw|read|call|text|come|help|work|remember)\b)", re.IGNORECASE),
     "I'll"),
]
# "my moms room" -> "my mom's room"
_POSSESSIVE_RE = re.compile(
    r"\b(mom|dad|mommy|daddy|sister|brother|grandma|grandpa|friend|cousin|aunt|uncle)s (?=(room|house|car|bed|"
    r"phone|office|work|birthday|friend|dog|cat|toys?|lap|side)\b)", re.IGNORECASE
)
# "mr kim" -> "Mr Kim", so the parser reads a name
_TITLE_RE = re.compile(r"\b(mr|mrs|ms|dr)\.? ([a-z])", re.IGNORECASE)

_WORD_RE = re.compile(r"[A-Za-z]+")


class UtteranceParser:
    """Lazily loads spaCy and parses normalized user messages"""

    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self._nlp = None
        self._load_failed = False

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
        text = " ".join(text.split())
        for pattern, replacement in _CONTEXT_NORMALIZATIONS:
            text = pattern.sub(replacement, text)
        text = _POSSESSIVE_RE.sub(r"\1's ", text)
        text = _TITLE_RE.sub(lambda m: f"{m.group(1).capitalize()} {m.group(2).upper()}", text)

        def replace(match):
            word = match.group(0)
            return NORMALIZATIONS.get(word.lower(), word)

        return _WORD_RE.sub(replace, text)

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
        return self._nlp(normalized_text)

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
        return words


# Global instance
utterance_parser = UtteranceParser()
