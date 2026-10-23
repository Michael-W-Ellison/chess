"""
Tests for reading crisis phrases with everyday meanings in context (services/crisis_context.py):
"she beats me" at a game, "it makes me scared" about a storm, "kids at school push me"
"""

import itertools
import logging
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import app
from services import crisis_context
from services.crisis_keyword_list import crisis_keyword_list
from services.safety_filter import safety_filter


def decide(message, recent=(), resolved=None, people=()):
    matched = [f["keyword"] for f in crisis_keyword_list.find_crisis_keywords(message)]
    return crisis_context.classify(message, matched, recent, resolved, people)


class TestClassify:
    @pytest.mark.parametrize("message,recent", [
        ("my sister always beats me", ["whats your favorite video game", "mine is mario kart"]),
        ("my dad always beats me at chess", []),
        ("my brother beats me in every race", []),
        ("Zoe beats me at Minecraft", []),
    ])
    def test_winning_a_game(self, message, recent):
        assert decide(message, recent) == "game"

    @pytest.mark.parametrize("message", ["my sister always beats me", "my brother beats me", "he beats me"])
    def test_sibling_or_friend_without_a_game_is_asked_about(self, message):
        assert decide(message) == "clarify"

    @pytest.mark.parametrize("message", [
        "my dad beats me",
        "My mom beats me when I get bad grades",
        "my brother beats me up",
        "my sister beats me and hits me",
    ])
    def test_still_a_crisis(self, message):
        assert decide(message) == "crisis"

    @pytest.mark.parametrize("message", [
        "kids at school take my stuff and push me",
        "some boys at recess pushed me",
        "a kid on the bus hit me",
        "the bullies kick me",
    ])
    def test_other_kids_are_bullying(self, message):
        assert decide(message) == "peer_bullying"

    @pytest.mark.parametrize("message", [
        "a kid hit me with the ball",
        "my sister hit me with a pillow",
        "some kid pushed me during the dodgeball game",
    ])
    def test_part_of_a_game(self, message):
        assert decide(message) == "game"

    def test_earlier_game_talk_does_not_excuse_pushing(self):
        assert decide("kids at recess push me", ["we played tag at recess"]) == "peer_bullying"

    @pytest.mark.parametrize("message", ["my dad pushes me", "my teacher pushed me at school", "he hits me"])
    def test_adults_and_unknown_people_are_a_crisis(self, message):
        assert decide(message) == "crisis"

    @pytest.mark.parametrize("message,resolved", [
        ("it makes me scared", "The thunderstorm makes me scared"),
        ("that makes me afraid", None),
        ("the thunder makes me scared", None),
        ("I'm scared of them", "I'm scared of spiders"),
    ])
    def test_fear_of_something_is_not_abuse(self, message, resolved):
        assert decide(message, resolved=resolved) == "indirect_fear"

    @pytest.mark.parametrize("message,resolved,people", [
        ("my dad makes me scared", None, ()),
        ("he makes me scared", None, ()),
        ("Jake makes me scared", None, ("Jake",)),
        ("I'm scared of him", None, ()),
        ("I'm scared of them", "I'm scared of my parents", ()),
        ("My mom screams at me and makes me scared", None, ()),
    ])
    def test_fear_of_a_person_is_a_crisis(self, message, resolved, people):
        assert decide(message, resolved=resolved, people=people) == "crisis"


class TestReplies:
    def test_clarification_question(self):
        question = crisis_context.clarification_question("my sister always beats me")
        assert "your sister wins when you play games" in question
        assert "she hits you" in question

    @pytest.mark.parametrize("answer,meaning", [
        ("she hits me", "violence"),
        ("yes", "violence"),
        ("at mario kart", "game"),
        ("no she just wins", "game"),
        ("idk", "unclear"),
    ])
    def test_clarification_answer(self, answer, meaning):
        assert crisis_context.clarification_answer(answer) == meaning

    def test_parents_arguing(self):
        reply = crisis_context.indirect_fear_reply("it makes me scared", ["my parents are fighting a lot"])
        assert "parents argue" in reply and "not your fault" in reply

    def test_names_what_is_scary(self):
        reply = crisis_context.indirect_fear_reply("it makes me scared", [], "The thunderstorm makes me scared")
        assert reply.startswith("It's okay to be scared of the thunderstorm.")


class TestSafetyFilter:
    def test_game_is_not_flagged(self):
        result = safety_filter.check_message("my sister always beats me", recent_messages=["mine is mario kart"])
        assert result["flags"] == [] and result["severity"] == "none"

    def test_clarify(self):
        result = safety_filter.check_message("my sister always beats me")
        assert result["action"] == "clarify" and result["safe"] and result["severity"] == "none"

    def test_forced_crisis_after_the_child_confirms(self):
        result = safety_filter.check_message("my sister always beats me", force_crisis=True)
        assert result["severity"] == "critical" and "abuse" in result["flags"]

    def test_peer_bullying(self):
        result = safety_filter.check_message("kids at school take my stuff and push me")
        assert result["flags"] == ["bullying"]
        assert result["severity"] != "critical"
        assert "Childhelp" not in result["response_message"]

    def test_fear_support(self):
        result = safety_filter.check_message("it makes me scared", recent_messages=["my parents are fighting"])
        assert result["action"] == "fear_support" and result["flags"] == []
        assert "Childhelp" not in result["response_message"]


# ----------------------------------------------------------------------
# Through the API
# ----------------------------------------------------------------------

_user_ids = itertools.count(9300)


@pytest.fixture(scope="module")
def api():
    logging.disable(logging.CRITICAL)
    with patch("utils.config.settings.USE_LLM", False), TestClient(app) as client:
        yield client
    logging.disable(logging.NOTSET)


def conversation(api, *messages):
    user_id = next(_user_ids)
    conversation_id = api.post(f"/api/conversation/start?user_id={user_id}").json()["conversation_id"]
    replies = []
    for message in messages:
        response = api.post("/api/message",
                            json={"content": message, "conversation_id": conversation_id, "user_id": user_id})
        assert response.status_code == 200
        replies.append(response.json()["content"])
    return replies


class TestConversation:
    def test_game_talk_then_beats_me(self, api):
        replies = conversation(api, "mine is mario kart", "my sister always beats me")
        assert "Childhelp" not in replies[-1]

    def test_clarification_then_game(self, api):
        replies = conversation(api, "my sister always beats me", "at mario kart")
        assert "do you mean your sister wins" in replies[0]
        assert replies[1] == crisis_context.CLARIFY_REPLY_GAME

    def test_clarification_then_hitting(self, api):
        replies = conversation(api, "my sister always beats me", "she hits me")
        assert "Childhelp" in replies[1]

    def test_clarification_unclear(self, api):
        replies = conversation(api, "my brother beats me", "idk")
        assert replies[1] == crisis_context.CLARIFY_REPLY_UNCLEAR

    def test_parents_arguing(self, api):
        replies = conversation(api, "my parents are fighting a lot", "it makes me scared")
        assert "Childhelp" not in replies[1] and "parents argue" in replies[1]

    def test_kids_at_school(self, api):
        replies = conversation(api, "kids at school take my stuff and push me")
        assert "Childhelp" not in replies[0] and "Bullying is never okay" in replies[0]

    def test_gentle_reply_after_the_bullying_response(self, api):
        replies = conversation(api, "kids at school take my stuff and push me", "they do it every day")
        assert not any(emoji in replies[1] for emoji in ("😄", "😊", "🌟", "🎉", "✨"))
        assert "What happened next" not in replies[1]

    def test_abuse_still_gets_the_crisis_response(self, api):
        assert "Childhelp" in conversation(api, "my dad hits me")[0]
