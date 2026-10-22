"""
Replies found wrong in scripted child conversations: names, pets, tenses, sad news,
questions to the bot, short answers and slang.
Skipped when spaCy or its English model is not installed.
"""

import itertools
import logging
import random
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import app
from services.emoji_quirk_service import emoji_quirk_service
from services.response_engine import ResponseEngine
from services.safety_filter import safety_filter
from services.utterance_parser import UtteranceParser

pytestmark = pytest.mark.skipif(
    not UtteranceParser().is_available(), reason="spaCy model en_core_web_sm not installed"
)


@pytest.fixture
def engine():
    return ResponseEngine(rng=random.Random(0))


def make_personality(**overrides):
    values = dict(
        id=1, user_id=1, name="Buddy", mood="happy", friendship_level=1,
        energy=0.7, curiosity=0.0, formality=0.3, get_interests=lambda: [],
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def rule_of(engine, message, user_id=1):
    """The rule (or fallback) the engine used to reply, after resolving references"""
    features = {}
    resolved = engine.resolve_references(message, user_id)
    reply = engine.generate_response(resolved, make_personality(user_id=user_id), features=features)
    engine.record_bot_reply(user_id, reply or "")
    return features.get("rule"), reply


class TestNewRules:
    @pytest.mark.parametrize("message,rule", [
        ("I miss my grandpa", "miss_person"),
        ("coach said I did great", "praise_reported"),
        ("not much you", "not_much"),
        ("yes", "yes_no"),
        ("I guess", "yes_no"),
        ("it's not fair", "not_fair"),
        ("what's up", "whats_up"),
        ("guess what", "guess_what"),
        ("wow", "wow"),
        ("lol", "laugh"),
        ("I don't know", "dont_know"),
        ("I don't know anyone", "know_nobody"),
        ("I don't know how to start", "dont_know_how"),
        ("I have a fever", "sick"),
        ("my tummy hurts", "body_hurts"),
        ("I don't feel good", "not_feel_good"),
        ("my friend said she doesn't want to be my friend anymore", "unfriended"),
        ("nobody plays with me at recess", "left_out"),
        ("my brother says I'm annoying", "person_says_about_me"),
        ("my brother always takes my stuff", "takes_my_stuff"),
        ("I'll try that", "will_try"),
        ("what ride should I go on", "which_should_i"),
        ("have you been there", "bot_been_question"),
        ("have you ever had sushi", "bot_been_question"),
        ("you're funny", "bot_compliment"),
        ("how old are you", "bot_age_question"),
        ("where do you live", "bot_home_question"),
        ("do you have friends", "bot_friends_question"),
        ("what food do you hate", "bot_dislike_question"),
        ("I'm turning 11", "age_short"),
        ("tomorrow is my birthday!", "birthday"),
        ("I learned to ride my bike!", "achievement"),
        ("but I kept trying", "kept_trying"),
        ("now I can ride all by myself", "can_now"),
        ("I have so much homework", "lots_of_homework"),
        ("I don't want to talk about it", "dont_want_to_talk"),
        ("can we talk about something else", "change_subject"),
        ("the dog is named Buster", "relation_named"),
        ("the dragon is named Sparky", "thing_named"),
        ("maybe we can be friends", "could_be_friends"),
        ("got to go bye", "gotta_go"),
        ("just kidding", "just_kidding"),
    ])
    def test_rule(self, engine, message, rule):
        assert rule_of(engine, message)[0] == rule

    def test_arithmetic(self, engine):
        rule, reply = rule_of(engine, "what's 2 plus 2")
        assert rule == "arithmetic"
        assert reply.startswith("2 plus 2 is 4!")

    def test_birthday_today_and_upcoming(self, engine):
        assert "Happy birthday" in rule_of(engine, "today is my birthday")[1]
        assert "coming up" in rule_of(engine, "my birthday is tomorrow")[1]

    def test_what_s_yours_answers_the_last_favorite_category(self, engine):
        rule_of(engine, "My favorite color is purple")
        rule, reply = rule_of(engine, "What's yours?")
        assert rule == "reciprocal"
        assert reply.startswith("My favorite color is")

    def test_school_task_in_the_past_is_not_upcoming(self, engine):
        assert rule_of(engine, "I had a math test today")[0] != "school_upcoming"

    def test_pet_age_in_the_past(self, engine):
        rule_of(engine, "I have a dog named Rocky")
        rule, reply = rule_of(engine, "he was 12")
        assert rule == "person_age_past"
        assert "do together" not in reply


class TestReflectionTense:
    @pytest.mark.parametrize("message,kind", [
        ("I had a math test today", "fallback_reflection"),
        ("we're going to have a party", "fallback_reflection_future"),
        ("my friends are coming over tomorrow", "fallback_reflection_future"),
        ("I'm teaching my dog to sit", "fallback_reflection_present"),
        ("my grandpa is in the hospital", "fallback_reflection_sad"),
        ("the castle is really big", "fallback_reflection_be"),
    ])
    def test_follow_up_fits_the_tense(self, engine, message, kind):
        assert rule_of(engine, message)[0] == kind

    def test_negated_sad_word_is_not_sad(self, engine):
        assert rule_of(engine, "I wasn't scared")[0] != "fallback_reflection_sad"

    def test_gentle_reflection_after_sad_news(self, engine):
        features = {}
        reply = engine.generate_response("I made him a card", make_personality(), {"sensitive": True},
                                         features=features)
        assert features["rule"] == "fallback_reflection_gentle"
        assert "What happened next" not in reply

    def test_reported_future(self, engine):
        assert rule_of(engine, "my mom said she will talk to him")[0] == "fallback_reflection_future"


class TestReferences:
    def test_new_pet_is_his(self, engine):
        rule_of(engine, "I got a new puppy!")
        assert engine.resolve_references("his name is Max", 1) == "My puppy's name is Max"
        assert engine.resolve_references("he is so cute", 1) == "My puppy Max is so cute"

    def test_pet_named_with_is_named(self, engine):
        rule_of(engine, "we have two cats and a dog")
        rule_of(engine, "the dog is named Buster")
        assert engine.resolve_references("he is really old", 1) == "My dog Buster is really old"

    def test_teacher_with_title(self, engine):
        rule_of(engine, "my teacher is mrs garcia")
        assert engine.resolve_references("shes really nice", 1) == "My teacher Mrs Garcia is really nice"

    def test_answer_to_favorite_question(self, engine):
        engine.record_bot_reply(1, "Ooh, I love red pandas! What's your favorite animal?")
        assert engine.resolve_references("mine is a wolf", 1) == "My favorite animal is a wolf"
        engine.record_bot_reply(1, "My favorite food is pancakes! What's yours?")
        assert engine.resolve_references("sushi", 1) == "My favorite food is sushi"

    def test_fair_is_not_a_reference(self, engine):
        rule_of(engine, "my sister always takes my stuff")
        assert engine.resolve_references("it's not fair", 1) == "it's not fair"

    def test_exclamation_in_bot_reply_is_not_a_thing(self, engine):
        rule_of(engine, "I built a castle yesterday")
        engine.record_bot_reply(1, "Awesome! You built a castle yesterday? That's awesome!")
        assert engine.resolve_references("it has a moat", 1) == "The castle has a moat"

    def test_added_joke_is_not_the_latest_thing(self, engine):
        engine.references.record_bot_reply(1, "Mine is Minecraft.", told="joke", mentions=["Minecraft"],
                                           told_was_added=True)
        assert engine.resolve_references("why do you like it", 1) == "why do you like Minecraft"

    def test_missing_name_is_left_out(self, engine):
        reply = engine.generate_response("bye", make_personality(), user_name=None)
        assert "\x00" not in reply and " ," not in reply and " !" not in reply


class TestNormalization:
    @pytest.mark.parametrize("text,expected", [
        ("shes nice", "she's nice"),
        ("idk", "I don't know"),
        ("nm u", "not much you"),
        ("its so boring", "it's so boring"),
        ("its wings", "its wings"),
        ("ok ill try that", "ok I'll try that"),
        ("I feel ill", "I feel ill"),
        ("ur weird", "you're weird"),
        ("ur dog", "your dog"),
        ("my teacher mr kim", "my teacher Mr Kim"),
        ("gtg bye", "got to go bye"),
        ("jk", "just kidding"),
    ])
    def test_normalize(self, text, expected):
        assert UtteranceParser.normalize(text) == expected


class TestSafetyAndEmojis:
    def test_sibling_taking_stuff_is_not_bullying(self):
        result = safety_filter.check_message("she always takes my stuff",
                                             resolved_message="My little sister Ava always takes my stuff")
        assert "bullying" not in result["flags"]

    def test_taking_stuff_without_family_is_still_bullying(self):
        assert "bullying" in safety_filter.check_message("He takes my stuff")["flags"]

    def test_where_do_you_live_is_allowed(self):
        assert safety_filter.check_message("where do you live")["safe"]

    @pytest.mark.parametrize("text,negative", [
        ("my grandpa is in the hospital", True),
        ("I wasn't scared", False),
        ("I'm not sad", False),
        ("we buried him", True),
    ])
    def test_is_negative(self, text, negative):
        assert emoji_quirk_service.is_negative(text) is negative


# ----------------------------------------------------------------------
# Through the API
# ----------------------------------------------------------------------

_user_ids = itertools.count(9100)


@pytest.fixture(scope="module")
def api():
    logging.disable(logging.CRITICAL)
    with patch("utils.config.settings.USE_LLM", False), TestClient(app) as client:
        yield client
    logging.disable(logging.NOTSET)


def start(api):
    user_id = next(_user_ids)
    response = api.post(f"/api/conversation/start?user_id={user_id}").json()
    return user_id, response["conversation_id"], response["greeting"]


def send(api, user_id, conversation_id, text):
    response = api.post("/api/message",
                        json={"content": text, "conversation_id": conversation_id, "user_id": user_id})
    assert response.status_code == 200
    return response.json()["content"]


def memories(api, user_id):
    response = api.get(f"/api/profile/memories?user_id={user_id}").json()["memories"]
    return {(m["category"], m["key"]): m["value"] for m in response}


class TestConversation:
    def test_hi_after_the_name_question_asks_again(self, api):
        user_id, conversation_id, greeting = start(api)
        assert greeting.endswith("What's your name?")
        reply = send(api, user_id, conversation_id, "hi")
        assert "What's your name?" in reply
        assert "User" not in reply

    @pytest.mark.parametrize("answer", ["im Lily", "lily", "Hi I'm Lily"])
    def test_name_answer_is_remembered(self, api, answer):
        user_id, conversation_id, _ = start(api)
        reply = send(api, user_id, conversation_id, answer)
        assert "Lily" in reply
        assert memories(api, user_id)[("basic", "name")] == "Lily"

    def test_feeling_is_not_a_name(self, api):
        user_id, conversation_id, _ = start(api)
        send(api, user_id, conversation_id, "im sad")
        assert ("basic", "name") not in memories(api, user_id)

    def test_answer_to_another_question_is_not_a_name(self, api):
        user_id, conversation_id, _ = start(api)
        send(api, user_id, conversation_id, "do you like pizza or tacos")
        send(api, user_id, conversation_id, "tacos")
        assert ("basic", "name") not in memories(api, user_id)

    def test_sibling_taking_stuff_gets_a_normal_reply(self, api):
        user_id, conversation_id, _ = start(api)
        send(api, user_id, conversation_id, "I have a little sister named Ava")
        reply = send(api, user_id, conversation_id, "she always takes my stuff")
        assert "Bullying" not in reply

    def test_no_jokes_after_sad_news(self, api):
        user_id, conversation_id, _ = start(api)
        with patch("services.conversation_manager.ConversationManager._choose_joke", return_value="pun"):
            for message in ("my grandpa is in the hospital", "we visited him on sunday", "he gave me a hug"):
                reply = send(api, user_id, conversation_id, message)
                assert "joke" not in reply.lower() and "fun one" not in reply.lower()

    def test_generic_advice_when_no_template_matches(self, api):
        user_id, conversation_id, _ = start(api)
        reply = send(api, user_id, conversation_id, "what do you think I should do?")
        assert "What do you think" not in reply
