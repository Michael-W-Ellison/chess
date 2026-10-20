"""
Tests for conversation API routes
Covers ending a conversation (both request forms) and the tracking endpoints
that share the /conversation/ prefix with /conversation/{conversation_id}.
"""

import logging

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def api():
    """Test client running the app lifespan against the temporary test database"""
    logging.disable(logging.CRITICAL)
    with TestClient(app) as test_client:
        yield test_client
    logging.disable(logging.NOTSET)


def _start_and_chat(api, user_id=1):
    response = api.post(f"/api/conversation/start?user_id={user_id}")
    assert response.status_code == 200
    conversation_id = response.json()["conversation_id"]

    response = api.post(
        "/api/message",
        json={"content": "My favorite sport is soccer", "conversation_id": conversation_id,
              "user_id": user_id},
    )
    assert response.status_code == 200
    return conversation_id


def _total_conversations(api, user_id=1):
    response = api.get(f"/api/personality?user_id={user_id}")
    assert response.status_code == 200
    return response.json()["total_conversations"]


class TestEndConversation:
    def test_end_with_id_in_path(self, api):
        """The form used by the frontend API client and the Electron IPC handler"""
        conversation_id = _start_and_chat(api)
        before = _total_conversations(api)

        response = api.post(f"/api/conversation/end/{conversation_id}")

        assert response.status_code == 200
        assert response.json()["success"] is True
        # End-of-conversation processing ran (tracker increments the conversation count)
        assert _total_conversations(api) == before + 1

        conversation = api.get(f"/api/conversation/{conversation_id}").json()
        assert conversation["duration_seconds"] is not None

    def test_end_with_id_in_body(self, api):
        conversation_id = _start_and_chat(api)
        before = _total_conversations(api)

        response = api.post(
            "/api/conversation/end", json={"conversation_id": conversation_id, "user_id": 1}
        )

        assert response.status_code == 200
        assert _total_conversations(api) == before + 1


class TestTrackingEndpoints:
    def test_stats(self, api):
        _start_and_chat(api)
        response = api.get("/api/conversation/stats?user_id=1")

        assert response.status_code == 200
        assert response.json()["stats"]["total_conversations"] >= 1

    def test_recent(self, api):
        _start_and_chat(api)
        response = api.get("/api/conversation/recent?user_id=1&limit=5")

        assert response.status_code == 200
        assert response.json()["count"] >= 1

    def test_streak(self, api):
        _start_and_chat(api)
        response = api.get("/api/conversation/streak?user_id=1")

        assert response.status_code == 200
        data = response.json()
        assert data["current_streak"] >= 1
        assert data["longest_streak"] >= 1

    def test_get_conversation_by_id_still_works(self, api):
        conversation_id = _start_and_chat(api)
        response = api.get(f"/api/conversation/{conversation_id}")

        assert response.status_code == 200
        assert response.json()["id"] == conversation_id
