"""
Safety filter on varied phrasings: concerns that must be flagged, and everyday phrases that
must not be (no spaCy needed)
"""

import pytest

from services.safety_filter import safety_filter


@pytest.mark.parametrize("text,flag", [
    ("i want to die", "crisis"),
    ("i wish i was dead", "crisis"),
    ("nobody would care if i was gone", "crisis"),
    ("i dont want to live anymore", "crisis"),
    ("i cut myself", "crisis"),
    ("my mom hits me", "abuse"),
    ("my dad beats me up", "abuse"),
    ("i am scared to go home", "abuse"),
    ("someone touched me in a bad way", "abuse"),
    ("my babysitter touches me where i dont like", "abuse"),
    ("he showed me pictures of private parts", "abuse"),
    ("a grown up said its our secret", "abuse"),
    ("he told me to keep it a secret", "abuse"),
    ("my uncle touches me and says not to tell", "abuse"),
    ("a stranger asked me to get in his car", "stranger_danger"),
    ("a stranger offered me candy", "stranger_danger"),
    ("a stranger followed me home", "stranger_danger"),
    ("a man in a car asked me to help find his puppy", "stranger_danger"),
    ("a man i dont know wanted me to come with him", "stranger_danger"),
    ("he asked me to get in his car", "stranger_danger"),
    ("an adult online asked for my address", "stranger_danger"),
    ("someone in roblox asked where i live", "stranger_danger"),
    ("a girl online wants to meet me", "stranger_danger"),
])
def test_concern_is_flagged(text, flag):
    result = safety_filter.check_message(text)
    assert flag in result["flags"]
    assert not result["safe"]


@pytest.mark.parametrize("text", [
    "i killed it at the game",
    "my sister beat me at mario kart",
    "i died in minecraft",
    "this homework is killing me",
    "i cut my paper into a heart",
    "my mom touched my head to check for a fever",
    "we kept the surprise party a secret",
    "the stranger things show is cool",
    "i talked to a stranger at the park",
    "we learned about strangers at school",
    "my brother pushed me on the swing",
    "my mom told me to get in her car",
    "my uncle asked me to come with him to the store",
    "my friend in roblox asked me to play",
    "online my teacher asked me to send my homework",
    "in minecraft my brother told me to send him diamonds",
    "i watched a video online about a man in a car",
    "we helped my neighbor find his lost dog",
])
def test_everyday_phrase_is_not_flagged(text):
    result = safety_filter.check_message(text)
    assert not result["flags"]


def test_stranger_danger_has_its_own_reply():
    result = safety_filter.check_message("a stranger offered me candy")
    assert "Never go anywhere with" in result["response_message"]
    assert result["notify_parent"]


def test_online_danger_has_its_own_reply():
    result = safety_filter.check_message("someone online asked for my address")
    assert "Never share your address" in result["response_message"]
