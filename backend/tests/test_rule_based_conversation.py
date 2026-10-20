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
