"""
End-to-end conversation through the API with the LLM disabled (USE_LLM=False)
Replies, memories and mood come from the rule-based response engine.
Skipped when spaCy or its English model is not installed.
"""

import logging
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import app
from services.utterance_parser import UtteranceParser

pytestmark = pytest.mark.skipif(
    not UtteranceParser().is_available(), reason="spaCy model en_core_web_sm not installed"
)

USER_ID = 7


@pytest.fixture(scope="module")
def api():
    logging.disable(logging.CRITICAL)
    with patch("utils.config.settings.USE_LLM", False), TestClient(app) as client:
        yield client
    logging.disable(logging.NOTSET)


@pytest.fixture(scope="module")
def conversation_id(api):
    response = api.post(f"/api/conversation/start?user_id={USER_ID}")
    assert response.status_code == 200
    return response.json()["conversation_id"]


def send(api, conversation_id, text):
    response = api.post(
        "/api/message",
        json={"content": text, "conversation_id": conversation_id, "user_id": USER_ID},
    )
    assert response.status_code == 200
    return response.json()


def stored_memories(api):
    response = api.get(f"/api/profile/memories?user_id={USER_ID}")
    assert response.status_code == 200
    return {(m["category"], m["key"]): m["value"] for m in response.json()["memories"]}


def test_reply_uses_parsed_content(api, conversation_id):
    reply = send(api, conversation_id, "My favorite color is blue")
    assert "blue" in reply["content"].lower()


def test_favorite_is_stored(api, conversation_id):
    assert stored_memories(api)[("favorite", "favorite_color")] == "blue"


def test_person_is_stored(api, conversation_id):
    send(api, conversation_id, "My best friend Maya moved away last week")
    assert stored_memories(api)[("person", "best_friend_maya")] == "Maya"


def test_mood_comes_from_sentence_structure(api, conversation_id):
    reply = send(api, conversation_id, "I feel sad because my dog is sick")
    assert reply["metadata"]["mood_detected"] == "sad"
    assert "your dog is sick" in reply["content"].lower()


def test_changing_a_preference_replaces_it(api, conversation_id):
    send(api, conversation_id, "I love broccoli")
    assert ("favorite", "likes_broccoli") in stored_memories(api)

    send(api, conversation_id, "I don't like broccoli anymore")
    memories = stored_memories(api)
    assert ("dislike", "dislikes_broccoli") in memories
    assert ("favorite", "likes_broccoli") not in memories


def test_bot_answers_questions_about_itself(api, conversation_id):
    reply = send(api, conversation_id, "What's your name?")
    personality = api.get(f"/api/personality?user_id={USER_ID}").json()
    assert personality["name"] in reply["content"]


def test_name_replaces_placeholder_user_name(api, conversation_id):
    send(api, conversation_id, "my name is Sam")
    reply = send(api, conversation_id, "hello")
    assert "Sam" in reply["content"]


def test_pronouns_refer_to_earlier_turns(api, conversation_id):
    send(api, conversation_id, "I played with Zoe today")
    send(api, conversation_id, "She is my cousin")
    assert stored_memories(api)[("person", "cousin_zoe")] == "Zoe"


def test_stored_message_keeps_original_wording(api, conversation_id):
    send(api, conversation_id, "My teacher gave us a test")
    reply = send(api, conversation_id, "She yelled at me")
    assert "your teacher yelled at you" in reply["content"].lower()

    conversation = api.get(f"/api/conversation/{conversation_id}").json()
    user_messages = [m["content"] for m in conversation["messages"] if m["role"] == "user"]
    assert "She yelled at me" in user_messages
    assert "My teacher yelled at me" not in user_messages


def test_new_conversation_forgets_references(api, conversation_id):
    send(api, conversation_id, "My best friend Maya moved away")
    new_id = api.post(f"/api/conversation/start?user_id={USER_ID}").json()["conversation_id"]
    reply = send(api, new_id, "She is so annoying")
    assert "Maya" not in reply["content"]


def engagement_rows(user_id):
    from database.database import SessionLocal
    from models.engagement import EngagementStat

    session = SessionLocal()
    try:
        return {(r.feature, r.arm): r.count
                for r in session.query(EngagementStat).filter(EngagementStat.user_id == user_id)}
    finally:
        session.close()


def test_replies_are_scored_by_the_next_message(api, conversation_id):
    before = engagement_rows(USER_ID)
    send(api, conversation_id, "I won my soccer game today")
    send(api, conversation_id, "It was so exciting because I scored the winning goal at the end")
    after = engagement_rows(USER_ID)
    assert after.get(("rule", "achievement"), 0) == before.get(("rule", "achievement"), 0) + 1


def test_crisis_message_is_not_an_engagement_signal(api, conversation_id):
    send(api, conversation_id, "I won my soccer game today")
    before = engagement_rows(USER_ID)
    send(api, conversation_id, "I want to hurt myself")
    assert engagement_rows(USER_ID) == before


def test_child_can_refer_to_what_the_bot_said(api, conversation_id):
    send(api, conversation_id, "tell me a fun fact")
    reply = send(api, conversation_id, "That's so cool")
    assert "fun fact" in reply["content"].lower()
