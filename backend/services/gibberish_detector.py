"""
Gibberish Detector
Recognizes keyboard mashing and random letters ("asdfghjkl", "sdkjfh skdjfh", "jkjkjk")

A word is garbled when it is not an English word (see UtteranceParser.known_words; plural,
past and -ing forms and stretched spellings like "sooo" count) and its spelling is unlike
English:
- at least three of its letter triples never occur in English words ("sdkjfh": sdk, dkj,
  kjf, jfh), and they are at least 30% of its triples,
- it contains four neighboring keys along a keyboard row ("qwerty", "asdf", "hjkl"), or
- it repeats a short chunk without vowels ("jkjkjk", "dfgdfg") or one letter five or more
  times ("xxxxxxx"; not "zzzzz").
A message is gibberish when at least half of its words are garbled.

Pronounceable made-up words ("blorp", "zorbin") are not flagged: they cannot be told apart
from names, games and slang missing from the word lists ("Jake", "roblox", "idk").
Messages without letters ("123", "!!!", emoji) are not gibberish. Without the spaCy model
nothing is flagged.
"""

import logging
import re
from collections import Counter
from typing import Optional, Set

from services.utterance_parser import utterance_parser

logger = logging.getLogger("chatbot.gibberish_detector")

MIN_UNSEEN_TRIGRAMS = 3
MIN_UNSEEN_SHARE = 0.3
KEYBOARD_RUN = 4
_KEYBOARD_ROWS = ("qwertyuiop", "asdfghjkl", "zxcvbnm")
_KEYBOARD_RUNS = {
    row[i:i + KEYBOARD_RUN]
    for keys in _KEYBOARD_ROWS for row in (keys, keys[::-1])
    for i in range(len(row) - KEYBOARD_RUN + 1)
}
_WORD_RE = re.compile(r"[A-Za-z]+")
_VOWELLESS_REPEAT_RE = re.compile(r"([^aeiouy]{2,3})\1+")
_SAME_LETTER_RE = re.compile(r"(.)\1{4,}")
_STRETCH_RE = re.compile(r"(.)\1{2,}")


class GibberishDetector:
    """Decides whether a message is keyboard mashing or random letters"""

    def __init__(self, parser=utterance_parser):
        self.parser = parser
        self._words: Optional[Set[str]] = None
        self._trigrams: Counter = Counter()

    def _load(self) -> bool:
        if self._words is None:
            self._words = self.parser.known_words() if self.parser.is_available() else set()
            for word in self._words:
                if word.isalpha():
                    padded = f"^^{word}$"
                    self._trigrams.update(padded[i:i + 3] for i in range(len(padded) - 2))
        return bool(self._words)

    def is_gibberish(self, message: str) -> bool:
        """True if at least half of the message's words are garbled"""
        if not message or not self._load():
            return False
        words = [w.lower() for w in _WORD_RE.findall(message)]
        if not words:
            return False
        garbled = sum(1 for w in words if self.is_garbled(w))
        return garbled > 0 and garbled * 2 >= len(words)

    def is_garbled(self, word: str) -> bool:
        """True if the (lowercase) word is not English and is not spelled like English"""
        # Before the word check, which would read "aaaaaaa" as a stretched "a"
        if _SAME_LETTER_RE.fullmatch(word) and word[0] != "z":  # "zzzzz" is sleepy
            return True
        if len(word) <= 2 or self._is_known(word):
            return False
        if _VOWELLESS_REPEAT_RE.fullmatch(word):
            return True
        if any(word[i:i + KEYBOARD_RUN] in _KEYBOARD_RUNS for i in range(len(word) - KEYBOARD_RUN + 1)):
            return True
        padded = f"^^{word}$"
        trigrams = [padded[i:i + 3] for i in range(len(padded) - 2)]
        unseen = sum(1 for t in trigrams if self._trigrams[t] == 0)
        return unseen >= MIN_UNSEEN_TRIGRAMS and unseen >= MIN_UNSEEN_SHARE * len(trigrams)

    def _is_known(self, word: str) -> bool:
        """The word, a stretched spelling of it ("sooo"), or an inflected form of it"""
        forms = {word, _STRETCH_RE.sub(r"\1\1", word), _STRETCH_RE.sub(r"\1", word)}
        for form in list(forms):
            for suffix, replacements in (("ies", ("y",)), ("es", ("",)), ("s", ("",)),
                                         ("ed", ("", "e")), ("ing", ("", "e")), ("er", ("", "e")),
                                         ("est", ("", "e")), ("ly", ("",))):
                if form.endswith(suffix) and len(form) > len(suffix) + 1:
                    forms.update(form[:-len(suffix)] + r for r in replacements)
        return any(form in self._words for form in forms)


# Global instance
gibberish_detector = GibberishDetector()
