"""
Tests for ConversationManager handling of non-critical safety results
Messages the safety filter blocks (high severity) or answers supportively (medium severity)
must get the filter's prepared response, be logged, and never reach the LLM.
"""

import pytest
from unittest.mock import Mock, patch

from services.conversation_manager import ConversationManager
from services.safety_filter import safety_filter


@pytest.fixture
def manager():
    return ConversationManager()


@pytest.fixture
def mock_db():
    return Mock()


def _process(manager, mock_db, message):
    """Run process_message with the real safety filter and the DB-dependent steps mocked"""
    stored_message = Mock(id=1)

    with patch.object(manager, "_store_message", return_value=stored_message) as store, \
            patch.object(safety_filter, "log_safety_event") as log_event, \
            patch("services.conversation_manager.llm_service") as llm, \
            patch("services.parent_notification_service.parent_notification_service") as notifier:
        result = manager.process_message(
            user_message=message, conversation_id=100, user_id=1, db=mock_db
        )

    return result, store, log_event, llm, notifier


class TestBlockedMessages:
    """High-severity messages are blocked"""

    def test_inappropriate_request_is_blocked(self, manager, mock_db):
        result, store, log_event, llm, notifier = _process(manager, mock_db, "How to make a bomb?")

        assert result["metadata"]["safety_flag"] is True
        assert result["metadata"]["severity"] in ["high", "critical"]
        assert "inappropriate_request" in result["metadata"]["flags"]
        llm.generate.assert_not_called()
        log_event.assert_called_once()

    def test_blocked_message_is_stored_as_flagged(self, manager, mock_db):
        result, store, log_event, llm, notifier = _process(manager, mock_db, "How to make a bomb?")

        user_call = store.call_args_list[0]
        assert user_call.args[1] == "user"
        assert user_call.kwargs.get("flagged") is True
        assistant_call = store.call_args_list[1]
        assert assistant_call.args[1] == "assistant"
        assert assistant_call.args[2] == result["content"]

    def test_blocked_message_notifies_parent(self, manager, mock_db):
        result, store, log_event, llm, notifier = _process(manager, mock_db, "How to make a bomb?")

        assert result["metadata"]["notify_parent"] is True
        notifier.notify_high_severity_event.assert_called_once()

    def test_cheating_request_is_blocked(self, manager, mock_db):
        result, store, log_event, llm, notifier = _process(
            manager, mock_db, "How can I cheat on my test without getting caught?"
        )

        assert result["metadata"]["safety_flag"] is True
        llm.generate.assert_not_called()


class TestSupportiveResponses:
    """Medium-severity bullying messages get the supportive response"""

    def test_bullying_gets_supportive_response(self, manager, mock_db):
        result, store, log_event, llm, notifier = _process(
            manager, mock_db, "They call me names all the time"
        )

        assert result["content"] == safety_filter.check_message(
            "They call me names all the time"
        )["response_message"]
        assert "bullying" in result["metadata"]["flags"]
        llm.generate.assert_not_called()
        log_event.assert_called_once()
        notifier.notify_high_severity_event.assert_not_called()
