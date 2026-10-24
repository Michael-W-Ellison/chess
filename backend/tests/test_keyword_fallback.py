"""
The keyword fallback (ResponseEngine._keyword_reply, "keywords" in the knowledge base): when no
rule answers, the highest-ranked keyword in the raw message picks the reply, whatever the
parse. Skipped when spaCy or its English model is not installed.
"""

import random

import pytest

from services.response_engine import ResponseEngine
from services.utterance_parser import UtteranceParser
from tests.test_dialogue_fixes import make_personality, rule_of

pytestmark = pytest.mark.skipif(
    not UtteranceParser().is_available(), reason="spaCy model en_core_web_sm not installed"
)


@pytest.fixture
def engine():
    return ResponseEngine(rng=random.Random(0))


def test_higher_rank_wins(engine):
    # "pink" (color, rank 1) and "bleeding" (hurt, rank 9)
    assert rule_of(engine, "it was pink and bleeding")[0] == "fallback_keyword_hurt"


@pytest.mark.parametrize("message", ["it stopped bleeding", "no more crying", "dont cry its just a joke"])
def test_negated_keyword_does_not_count(engine, message):
    assert not (rule_of(engine, message)[0] or "").startswith("fallback_keyword")


def test_keyword_keeps_the_childs_spelling(engine):
    assert rule_of(engine, "at mario kart")[1].startswith("Ooh, Mario Kart!")


def test_rules_and_silly_combinations_come_first(engine):
    assert rule_of(engine, "purple monkey dishwasher")[0] == "fallback_silly"
    assert rule_of(engine, "i love pizza")[0] != "fallback_keyword_food"


def test_no_echo_when_reflection_is_off(engine):
    reply = engine.generate_response("it was pink", make_personality(), allow_reflection=False)
    assert "pink" not in reply.lower()
    features = {}
    engine.generate_response("it was bleeding", make_personality(), allow_reflection=False, features=features)
    assert features["rule"] == "fallback_keyword_hurt"
