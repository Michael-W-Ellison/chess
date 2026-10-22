"""
Tests for recognizing keyboard mashing and random letters (services/gibberish_detector.py)
Skipped when spaCy or its English model is not installed.
"""

import pytest

from services.gibberish_detector import GibberishDetector, gibberish_detector
from services.utterance_parser import UtteranceParser

pytestmark = pytest.mark.skipif(
    not UtteranceParser().is_available(), reason="spaCy model en_core_web_sm not installed"
)


@pytest.mark.parametrize("message", [
    "asdfghjkl", "sdkjfh skdjfh sdkjfhsdf", "lkjsdf lkjsdf", "ajsdkfjaksdjf?",
    "qwerty uiop", "hjkl", "zxcvbnm", "asdf",          # keyboard rows
    "jkjkjk", "fjfjfj dfgdfg",                          # repeated chunks without vowels
    "xxxxxxxxxxx", "AAAAAAAA",                          # one letter repeated
    "lol asdfgh",                                       # half the words garbled
])
def test_gibberish(message):
    assert gibberish_detector.is_gibberish(message)


@pytest.mark.parametrize("message", [
    "hi", "k", "ok", "hmm", "zzz", "zzzzzz", "ugh",
    "lol", "idk", "omg", "brb", "tbh", "nvm", "thx", "gg", "jk", "smh",   # slang
    "hahaha", "lolol", "hehe", "sooooo", "heyyy", "nooooooo", "hmmmmmm",  # stretched
    "I played minecraft with Jake", "roblox", "my pokemon", "skibidi rizz",  # games, names
    "Sophia and Aiden", "I am sooooo bored", "becuz", "gonna", "wanna",
    "blorp zib flarg", "My zorbin is flimflam",          # made-up but pronounceable
    "hola como estas", "je suis content",                 # other languages
    "123456789", "!!!???...", "\U0001F92A\U0001F92A",     # no letters
    "I love sdkjfh",                                      # one garbled word of three
])
def test_not_gibberish(message):
    assert not gibberish_detector.is_gibberish(message)


def test_inflected_and_stretched_forms_are_words():
    assert not gibberish_detector.is_garbled("dogs")
    assert not gibberish_detector.is_garbled("running")
    assert not gibberish_detector.is_garbled("pizzza")


def test_nothing_flagged_without_the_parser():
    class Unavailable:
        def is_available(self):
            return False

    assert not GibberishDetector(parser=Unavailable()).is_gibberish("asdfghjkl")
