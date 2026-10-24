"""
The confidence gate (ResponseEngine._doubt): a strongly worded reply is not used when the
message is mixed or the parse looks broken, and a plain echo of the message answers instead.
Skipped when spaCy or its English model is not installed.
"""

import random

import pytest

from services.response_engine import Frame, ResponseEngine
from services.utterance_parser import UtteranceParser
from tests.test_dialogue_fixes import make_personality

pytestmark = pytest.mark.skipif(
    not UtteranceParser().is_available(), reason="spaCy model en_core_web_sm not installed"
)


@pytest.fixture
def engine():
    return ResponseEngine(rng=random.Random(0))


def reply(engine, message):
    features = {}
    text = engine.generate_response(engine.resolve_references(message, 1), make_personality(), features=features)
    return features.get("rule"), text, features.get("doubted", [])


@pytest.mark.parametrize("message,doubted", [
    ("i scored a goal but then i got hurt", "achievement:mixed"),
    ("i got a new bike and then it broke", "got_gift:mixed"),
    ("i passed my test and my dog died", "achievement:mixed"),
    ("my cat had kittens and my mom yelled at me", "pet_babies:mixed"),
])
def test_good_news_with_bad_news_is_not_cheered(engine, message, doubted):
    rule, text, gated = reply(engine, message)
    assert doubted in gated
    assert "Congratulations" not in text and "Yay" not in text


def test_plain_echo_answers_after_a_doubt(engine):
    rule, text, _ = reply(engine, "i got a new bike and then it broke")
    assert rule == "fallback_reflection_sad"
    assert "you got a new bike and then it broke" in text


@pytest.mark.parametrize("message,rule", [
    ("i passed my test and my dog died", "person_event"),
    ("i got a puppy and i cried", "crying"),
])
def test_caring_replies_are_kept(engine, message, rule):
    assert reply(engine, message)[0] == rule


@pytest.mark.parametrize("message,rule", [
    ("i got a red card", "penalty_card"),
    ("i won the race", "achievement"),
    ("i got a new bike", "got_gift"),
])
def test_rules_on_the_same_verb_or_plain_news_are_not_doubted(engine, message, rule):
    found, _, gated = reply(engine, message)
    assert found == rule and not gated


def test_broken_parse_doubts_a_repaired_match(engine):
    # Simulate a parse the repairs could not fix: the root read as a noun, a verb inside
    doc = engine.parser._get_nlp()("i think my dog ate my homework")  # uncached: safe to change
    doc[0].sent.root.pos_ = "NOUN"
    verb = next(t for t in doc if t.lower_ == "ate")
    doc.user_data["repaired"] = {verb.i}
    frame = Frame(rule_id="test", priority=1, slots={}, valence="positive", tokens=[verb.i], anchor=verb.i)
    assert engine._doubt(frame, [frame], doc) == "fragment"
    doc.user_data["repaired"] = set()
    assert engine._doubt(frame, [frame], doc) is None
