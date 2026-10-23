"""
Parse repairs in services/utterance_parser.py for child phrasings the spaCy model misreads.
Skipped when spaCy or its English model is not installed.
"""

import pytest

from services.utterance_parser import UtteranceParser

parser = UtteranceParser()

pytestmark = pytest.mark.skipif(not parser.is_available(), reason="spaCy model en_core_web_sm not installed")


def token(doc, word):
    return next(t for t in doc if t.lower_ == word)


@pytest.mark.parametrize("text,word", [
    ("my dog snores", "snores"),
    ("the baby cries", "cries"),
    ("can fish swim", "swim"),
    ("do dogs dance", "dance"),
    ("i love to camp", "camp"),
    ("i have to camp today", "camp"),
    ("lets paint", "paint"),
    ("lets race", "race"),
])
def test_verb_is_tagged_verb(text, word):
    assert token(parser.parse(text), word).pos_ == "VERB"


def test_like_before_gerund_is_the_main_verb():
    doc = parser.parse("i like jumping")
    like, jumping = token(doc, "like"), token(doc, "jumping")
    assert like.dep_ == "ROOT" and like.pos_ == "VERB"
    assert jumping.dep_ == "xcomp" and jumping.head.i == like.i


@pytest.mark.parametrize("text,name", [
    ("maya and i went to the park", "maya"),
    ("me and lily played tag", "lily"),
])
def test_name_and_i_is_a_shared_subject(text, name):
    doc = parser.parse(text)
    subject, me = token(doc, name), token(doc, "i")
    assert subject.dep_ == "nsubj" and subject.head.pos_ == "VERB"
    assert me.dep_ == "conj" and me.head.i == subject.i


def test_me_and_is_rewritten():
    assert parser.parse("me and my friend built a fort").text.lower().startswith("my friend and i")


@pytest.mark.parametrize("text,word", [("then and i went home", "then"), ("today and tomorrow i have school", "today")])
def test_time_words_are_not_made_subjects(text, word):
    assert token(parser.parse(text), word).dep_ != "nsubj"


def test_me_and_possessive_is_left_alone():
    assert parser.parse("me and my mom's dog ran").text.lower().startswith("me and my mom's")


def test_activity_after_go_is_a_verb():
    swimming = token(parser.parse("let's go swimming"), "swimming")
    assert swimming.dep_ == "xcomp" and swimming.head.lower_ == "go"


class TestLetsSuggestions:
    @pytest.fixture
    def engine(self):
        import random
        from services.response_engine import ResponseEngine
        return ResponseEngine(rng=random.Random(0))

    @pytest.mark.parametrize("text,activity", [
        ("lets paint", "paint"),
        ("lets play tag", "play tag"),
        ("let's go swimming", "go swimming"),
        ("lets go to the park tomorrow", "go to the park"),
    ])
    def test_lets_activity(self, engine, text, activity):
        from tests.test_dialogue_fixes import rule_of
        rule, reply = rule_of(engine, text)
        assert rule == "lets_activity" and reply.startswith(f"I wish I could {activity} with you!")

    @pytest.mark.parametrize("text,topic", [
        ("let's talk about dogs", "dogs"),
        ("can we talk about dogs", "dogs"),
        ("i want to talk about my dog", "your dog"),
    ])
    def test_talk_about(self, engine, text, topic):
        from tests.test_dialogue_fixes import rule_of
        assert rule_of(engine, text) == ("talk_about", f"Sure, let's talk about {topic}! What do you want to tell me?")

    @pytest.mark.parametrize("text", ["let me think", "let him go", "we talked about dogs at school"])
    def test_not_a_suggestion(self, engine, text):
        from tests.test_dialogue_fixes import rule_of
        assert rule_of(engine, text)[0] not in ("lets_activity", "talk_about")

    def test_lets_be_friends(self, engine):
        from tests.test_dialogue_fixes import rule_of
        assert rule_of(engine, "lets be friends")[0] == "lets_be_friends"
