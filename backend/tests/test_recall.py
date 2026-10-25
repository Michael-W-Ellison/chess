"""
Questions about what the child told the bot ("how old am i?", "what pets do i have?"),
answered from the stored memories (the "recall" section of knowledge/conversation_rules.json,
ResponseEngine._recall_reply). Skipped when spaCy or its English model is not installed.
"""

import random

import pytest

from services.response_engine import ResponseEngine
from services.utterance_parser import UtteranceParser
from tests.test_dialogue_fixes import make_personality

pytestmark = pytest.mark.skipif(
    not UtteranceParser().is_available(), reason="spaCy model en_core_web_sm not installed"
)

MEMORIES = [
    ("basic", "age", "8"), ("person", "dog_rex", "Rex"), ("basic", "has_cat", "two cats"),
    ("person", "best_friend_maya", "Maya"), ("person", "little_sister_emma", "Emma"),
    ("favorite", "likes_soccer", "soccer"), ("favorite", "favorite_color", "green"),
    ("dislike", "dislikes_broccoli", "broccoli"), ("basic", "has_brother", "a little brother"),
]


def ask(message, memories=MEMORIES, user_name="Lily"):
    engine = ResponseEngine(rng=random.Random(0))
    context = {"known_memories": memories, "known_facts": {k: v for _, k, v in memories}}
    features = {}
    reply = engine.generate_response(message, make_personality(), context=context, user_name=user_name,
                                     features=features)
    return features.get("rule"), reply


@pytest.mark.parametrize("message,rule,expected", [
    ("how old am i", "recall_age", "You're 8!"),
    ("do i like soccer", "recall_do_i_like", "Yes! You told me you like soccer."),
    ("do i like broccoli", "recall_do_i_like", "you don't like broccoli"),
    ("what do i like", "recall_what_i_like", "you like soccer, and your favorite color is green"),
    ("what dont i like", "recall_what_i_dislike", "you don't like broccoli"),
    ("what pets do i have", "recall_my_pets", "You have a dog named Rex and two cats!"),
    ("do i have a dog", "recall_do_i_have", "You have a dog named Rex."),
    ("do i have a sister", "recall_do_i_have", "a little sister named Emma"),
    ("who is my best friend", "recall_who_is_my", "Your best friend is Maya!"),
    ("what do you know about me", "recall_about_me", "You're Lily, you're 8"),
])
def test_answered_from_memories(message, rule, expected):
    found, reply = ask(message)
    assert found == rule and expected in reply


@pytest.mark.parametrize("message,expected", [
    ("how old am i", "How old are you?"),
    ("do i like dogs", "Do you like dogs?"),
    ("what pets do i have", "Do you have one?"),
    ("who is my teacher", "Who is your teacher?"),
    ("what do you know about me", "getting to know you"),
])
def test_unknown_answers_ask(message, expected):
    assert expected in ask(message, memories=[], user_name=None)[1]


@pytest.mark.parametrize("message", ["do i have homework", "do i have to go to school"])
def test_other_questions_are_left_to_the_rules(message):
    assert not (ask(message)[0] or "").startswith("recall_")


def test_compound_relation_name_is_recalled():
    assert "Maya" in ask("whats my best friends name")[1]
