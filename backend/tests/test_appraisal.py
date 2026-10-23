"""
General reply layers: appraisal of what a message says happened (services/appraisal.py),
replies composed from it, the modality guard on specific rules, answers to the bot's own
questions, and fragments that continue the previous message.
Skipped when spaCy or its English model is not installed.
"""

import random

import pytest

from services.appraisal import FUTURE, HOPE, HYPOTHETICAL, POSSIBLE, REAL, WANT
from services.response_engine import ResponseEngine, expectation_from_reply
from services.utterance_parser import UtteranceParser
from tests.test_dialogue_fixes import rule_of

pytestmark = pytest.mark.skipif(
    not UtteranceParser().is_available(), reason="spaCy model en_core_web_sm not installed"
)


@pytest.fixture
def engine():
    return ResponseEngine(rng=random.Random(0))


def appraise(engine, text):
    return engine.appraiser.appraise(engine.parser.parse(text))


class TestAppraiser:
    @pytest.mark.parametrize("text,action,actor,target,valence", [
        ("my cousin pinched me", "harm", "person", "child", "negative"),
        ("a boy at the park threw sand at me", "harm", "person", "child", "negative"),
        ("I pushed my brother", "harm", "child", "person", "negative"),
        ("the dog bit my sister", "harm", "pet", "person", "negative"),
        ("my sister ripped my drawing", "break", "person", "child_thing", "negative"),
        ("our cat knocked my cup off the table", "break", "pet", "child_thing", "negative"),
        ("my grandma knitted me a scarf", "kindness", "person", "child", "positive"),
        ("I made him a card", "kindness", "child", "person", "positive"),
        ("I shared my snack with a new kid", "kindness", "child", "child_thing", "positive"),
        ("my brother made fun of my drawing", "tease", "person", "thing", "negative"),
        ("a kid laughed at my shoes", "tease", "person", None, "negative"),
        ("I learned to ride my bike", "achieve", "child", None, "positive"),
        ("I missed the bus", "setback", "child", "thing", "negative"),
        ("my hamster escaped", "lost_item", "pet", None, "negative"),
        ("the wind blew my kite away", "lost_item", "thing", "child_thing", "negative"),
        ("we went to the aquarium", "fun", "child", None, "positive"),
        ("I had hot chocolate", "eat", "child", "thing", "positive"),
        ("my parents argued", "conflict", "person", None, "negative"),
        ("I got invited to a party", "kindness", "unknown", "child", "positive"),
    ])
    def test_action_roles_and_valence(self, engine, text, action, actor, target, valence):
        a = appraise(engine, text)
        assert (a.action, a.actor, a.target, a.valence) == (action, actor, target, valence)

    @pytest.mark.parametrize("text,modality", [
        ("we went to the zoo", REAL),
        ("we will go to the zoo", FUTURE),
        ("we are going to the beach on saturday", FUTURE),
        ("I hope my team wins", HOPE),
        ("I want to go to space", WANT),
        ("I wish I could fly", WANT),
        ("what if I get lost", HYPOTHETICAL),
        ("we might go to the zoo", POSSIBLE),
        ("we can't go to the park", REAL),
    ])
    def test_modality(self, engine, text, modality):
        assert appraise(engine, text).modality == modality

    @pytest.mark.parametrize("text,valence", [
        ("I didn't win", "negative"),
        ("I didn't get invited to the party", "negative"),
        ("he didn't hit me", "positive"),
    ])
    def test_negation_flips_how_it_feels(self, engine, text, valence):
        a = appraise(engine, text)
        assert a.negated and a.valence == valence

    def test_going_to_the_dentist_is_not_fun(self, engine):
        assert appraise(engine, "I went to the dentist").action is None

    def test_accident(self, engine):
        assert appraise(engine, "I accidentally kicked my sister").notes.get("accident") == "yes"


class TestComposedReplies:
    @pytest.mark.parametrize("text,kind,words", [
        ("my cousin pinched me", "harm_real", "tell a grown-up"),
        ("I pushed my brother", "harm_real", "take a deep breath"),
        ("I accidentally kicked my sister", "harm_real", "Accidents happen"),
        ("our cat knocked my cup off the table", "break_real", "Pets can be so silly"),
        ("my grandma knitted me a scarf", "kindness_real", ""),
        ("a kid laughed at my shoes", "tease_real", "wasn't kind"),
        ("my friend learned to swim", "achieve_real", ""),
        ("I didn't win", "achieve_real", "next time"),
        ("I didn't get invited to the party", "kindness_real", "left out"),
        ("my hamster escaped", "lost_item_real", ""),
        ("we went to the aquarium", "fun_real", ""),
        ("I wish I had a puppy", "any_want", ""),
        ("I wish my dad was home more", "any_want", "matters to you"),
        ("we might go to the zoo on sunday", "fun_possible", ""),
        ("what if I get lost", "fear_hypothetical", "worry"),
        ("what if I win", "achieve_hypothetical", "amazing"),
        ("what if I fail the test", "setback_hypothetical", "worry"),
        ("I will score a goal tomorrow", "achieve_future", "spirit"),
        ("I'm going to give my mom a card", "kindness_future", "thoughtful"),
        ("I never finish my homework on time", "achieve_real", "plan"),
    ])
    def test_reply_fits_the_event(self, engine, text, kind, words):
        rule, reply = rule_of(engine, text)
        assert rule == f"fallback_appraisal_{kind}"
        assert words in reply

    def test_plain_events_keep_plain_reflections(self, engine):
        assert rule_of(engine, "We sat on the porch")[0] == "fallback_reflection"
        assert rule_of(engine, "we can't go to the park")[0] == "fallback_reflection_cant"

    def test_long_message_is_not_echoed_whole(self, engine):
        rule, _ = rule_of(engine, "today i went to school and we had art and i painted a cat and then at recess "
                                  "i played tag with my friends")
        assert not rule.startswith("fallback_appraisal")

    def test_no_jokes_after_composed_replies(self, engine):
        assert engine.rule_flag("fallback_appraisal_fun_real", "no_jokes")
        assert engine.rule_flag("fallback_continuation_eat_real", "no_jokes")


class TestModalityGuard:
    @pytest.mark.parametrize("text,not_rule", [
        ("I will score a goal tomorrow", "achievement"),
        ("my mom said we can get a new one", "got_gift"),
        ("I hope I win the race", "achievement"),
        ("my brother made fun of my drawing", "person_kindness"),
    ])
    def test_reaction_rule_does_not_fire(self, engine, text, not_rule):
        assert rule_of(engine, text)[0] != not_rule

    def test_real_events_still_get_their_rules(self, engine):
        assert rule_of(engine, "I won the race")[0] == "achievement"
        assert rule_of(engine, "I lost a tooth today")[0] == "lost_tooth"
        assert rule_of(engine, "I will miss her")[0] in ("miss_person", "fallback_appraisal_loss_future")


class TestExpectations:
    @pytest.mark.parametrize("reply,kind,extra", [
        ("Want to hear a funny joke?", "offer", "joke"),
        ("Saving is smart! Want another one?", "offer", "again"),
        ("Want to hear a joke, a riddle, or a fun fact?", "choice", None),
        ("We could tell jokes, solve riddles, or share fun facts! Which one sounds fun?", "choice", None),
        ("Mine too! Why is Saturn your favorite?", "reason", None),
        ("Ooh, you're in a play! What part are you playing?", "item", "part"),
        ("Ooh, Halloween! What are you going to be?", "item", "costume"),
        ("Yes, please! I'd love to hear it!", "listen", None),
    ])
    def test_expectation_from_reply(self, reply, kind, extra):
        expectation = expectation_from_reply(reply)
        assert expectation.kind == kind
        if kind == "offer":
            assert expectation.offer == extra
        if kind == "item":
            assert expectation.noun == extra

    @pytest.mark.parametrize("reply", ["What part is tricky?", "How did that go?", "What happened next?"])
    def test_open_questions_expect_nothing(self, reply):
        assert expectation_from_reply(reply) is None

    def test_answer_to_why(self, engine):
        rule_of(engine, "my favorite planet is saturn")
        engine.record_bot_reply(1, "Mine too! Why is Saturn your favorite?")
        rule, reply = rule_of(engine, "it has rings")
        assert rule == "answer_reason" and reply == "Ooh, that's a good reason! Saturn has rings? Cool!"

    def test_answer_item(self, engine):
        engine.record_bot_reply(1, "Ooh, Halloween! What are you going to be?")
        assert rule_of(engine, "a ninja") == ("answer_item", "A ninja! That sounds like a fun costume!")

    def test_a_rule_still_answers_its_own_message(self, engine):
        engine.record_bot_reply(1, "Mine too! Why is Saturn your favorite?")
        assert rule_of(engine, "bye")[0] != "answer_reason"


class TestContinuations:
    def test_place_fragment(self, engine):
        rule_of(engine, "we went on a field trip")
        rule, reply = rule_of(engine, "to the zoo")
        assert rule == "fallback_continuation_fun_real" and reply.startswith("To the zoo?")

    def test_verb_fragment(self, engine):
        rule_of(engine, "we made snow angels")
        rule, reply = rule_of(engine, "and had hot chocolate")
        assert rule == "fallback_continuation_eat_real" and "you had hot chocolate" in reply
