"""
Tests for Automatic Conversation Summary Generation on End
Tests that LLM summaries are generated when conversations end
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from services.conversation_manager import ConversationManager


class TestConversationEndSummary:
    """Test automatic summary generation when conversation ends"""

    def setup_method(self):
        """Set up test fixtures"""
        self.manager = ConversationManager()
        self.mock_db = Mock()

        # Mock conversation with messages
        self.mock_conversation = Mock()
        self.mock_conversation.id = 100
        self.mock_conversation.user_id = 1
        self.mock_conversation.message_count = 5
        self.mock_conversation.duration_seconds = 300

        # Mock messages
        self.mock_messages = [
            Mock(id=1, role="user", content="How do I castle in chess?", timestamp=datetime.now()),
            Mock(id=2, role="assistant", content="Castling is a special move...", timestamp=datetime.now()),
            Mock(id=3, role="user", content="When should I use it?", timestamp=datetime.now()),
            Mock(id=4, role="assistant", content="You should castle early...", timestamp=datetime.now()),
        ]
        self.mock_conversation.messages = self.mock_messages

        # Mock personality
        self.mock_personality = Mock()
        self.mock_personality.user_id = 1
        self.mock_personality.friendship_level = 5
        self.mock_personality.friendship_points = 50

        # Set conversation start time
        self.manager.conversation_start_time = datetime.now()
        self.manager.message_count = 5

    @patch('services.conversation_manager.settings')
    @patch('services.conversation_manager.conversation_summary_service')
    @patch('services.conversation_manager.conversation_tracker')
    @patch('services.conversation_manager.personality_manager')
    @patch('services.conversation_manager.personality_drift_calculator')
    def test_summary_generated_on_conversation_end_when_enabled(
        self,
        mock_drift_calc,
        mock_personality_manager,
        mock_tracker,
        mock_summary_service,
        mock_settings
    ):
        """Test that LLM summary is generated when AUTO_GENERATE_SUMMARIES is True"""
        # Enable auto-summary generation
        mock_settings.AUTO_GENERATE_SUMMARIES = True

        # Mock summary service response
        mock_summary_data = {
            "summary": "Child learned about castling and when to use it.",
            "topics": ["castling", "chess strategy"],
            "mood": "engaged",
            "key_moments": ["Understood when to castle early"],
            "safety_concerns": []
        }
        mock_summary_service.generate_summary.return_value = mock_summary_data

        # Mock database queries
        def query_side_effect(model):
            mock_query = Mock()
            mock_filter = Mock()
            if model.__name__ == 'Conversation':
                mock_filter.first.return_value = self.mock_conversation
            elif model.__name__ == 'BotPersonality':
                mock_filter.first.return_value = self.mock_personality
            elif model.__name__ == 'Message':
                # Return messages for _calculate_conversation_metrics
                mock_filter.all.return_value = self.mock_messages
            else:
                mock_filter.first.return_value = None
                mock_filter.all.return_value = []
            mock_query.filter.return_value = mock_filter
            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        # Mock tracker
        mock_tracker.on_conversation_end.return_value = {"conversation_quality": "good"}

        # Mock drift calculator
        mock_drift_calc.calculate_drift_after_conversation.return_value = []

        # End conversation
        self.manager.end_conversation(100, self.mock_db)

        # Verify summary service was called
        mock_summary_service.generate_summary.assert_called_once_with(100, self.mock_db)

        # Verify database commit
        assert self.mock_db.commit.called

    @patch('services.conversation_manager.settings')
    @patch('services.conversation_manager.conversation_summary_service')
    @patch('services.conversation_manager.conversation_tracker')
    @patch('services.conversation_manager.personality_manager')
    @patch('services.conversation_manager.personality_drift_calculator')
    def test_summary_not_generated_when_disabled(
        self,
        mock_drift_calc,
        mock_personality_manager,
        mock_tracker,
        mock_summary_service,
        mock_settings
    ):
        """Test that LLM summary is NOT generated when AUTO_GENERATE_SUMMARIES is False"""
        # Disable auto-summary generation
        mock_settings.AUTO_GENERATE_SUMMARIES = False

        # Mock database queries
        def query_side_effect(model):
            mock_query = Mock()
            mock_filter = Mock()
            if model.__name__ == 'Conversation':
                mock_filter.first.return_value = self.mock_conversation
            elif model.__name__ == 'BotPersonality':
                mock_filter.first.return_value = self.mock_personality
            elif model.__name__ == 'Message':
                # Return messages for _calculate_conversation_metrics
                mock_filter.all.return_value = self.mock_messages
            else:
                mock_filter.first.return_value = None
                mock_filter.all.return_value = []
            mock_query.filter.return_value = mock_filter
            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        # Mock tracker
        mock_tracker.on_conversation_end.return_value = {"conversation_quality": "good"}

        # Mock drift calculator
        mock_drift_calc.calculate_drift_after_conversation.return_value = []

        # End conversation
        self.manager.end_conversation(100, self.mock_db)

        # Verify summary service was NOT called
        mock_summary_service.generate_summary.assert_not_called()

    @patch('services.conversation_manager.settings')
    @patch('services.conversation_manager.conversation_summary_service')
    @patch('services.conversation_manager.conversation_tracker')
    @patch('services.conversation_manager.personality_manager')
    @patch('services.conversation_manager.personality_drift_calculator')
    @patch('services.conversation_manager.memory_manager')
    def test_fallback_to_simple_summary_on_llm_failure(
        self,
        mock_memory_manager,
        mock_drift_calc,
        mock_personality_manager,
        mock_tracker,
        mock_summary_service,
        mock_settings
    ):
        """Test that simple summary is used when LLM summary generation fails"""
        # Enable auto-summary generation
        mock_settings.AUTO_GENERATE_SUMMARIES = True

        # Mock summary service to raise exception
        mock_summary_service.generate_summary.side_effect = Exception("LLM service unavailable")

        # Mock memory manager for fallback
        mock_memory_manager.extract_keywords.return_value = ["castling", "chess", "strategy"]

        # Mock database queries - need to handle Message query for fallback
        def query_side_effect(model):
            mock_query = Mock()
            mock_filter = Mock()
            if model.__name__ == 'Conversation':
                mock_filter.first.return_value = self.mock_conversation
            elif model.__name__ == 'BotPersonality':
                mock_filter.first.return_value = self.mock_personality
            elif model.__name__ == 'Message':
                # Return messages for fallback summary
                mock_filter.all.return_value = self.mock_messages
            mock_query.filter.return_value = mock_filter
            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        # Mock tracker
        mock_tracker.on_conversation_end.return_value = {"conversation_quality": "good"}

        # Mock drift calculator
        mock_drift_calc.calculate_drift_after_conversation.return_value = []

        # End conversation - should not raise exception
        self.manager.end_conversation(100, self.mock_db)

        # Verify fallback was used (extract_keywords was called)
        assert mock_memory_manager.extract_keywords.called

        # Verify conversation summary was set (fallback format)
        assert "Discussed:" in self.mock_conversation.conversation_summary

    @patch('services.conversation_manager.settings')
    @patch('services.conversation_manager.conversation_summary_service')
    @patch('services.conversation_manager.conversation_tracker')
    @patch('services.conversation_manager.personality_manager')
    @patch('services.conversation_manager.personality_drift_calculator')
    def test_no_summary_generated_for_empty_conversation(
        self,
        mock_drift_calc,
        mock_personality_manager,
        mock_tracker,
        mock_summary_service,
        mock_settings
    ):
        """Test that no summary is generated for conversation with no messages"""
        # Enable auto-summary generation
        mock_settings.AUTO_GENERATE_SUMMARIES = True

        # Create conversation with no messages
        empty_conversation = Mock()
        empty_conversation.id = 101
        empty_conversation.user_id = 1
        empty_conversation.messages = []  # No messages

        # Mock database queries
        def query_side_effect(model):
            mock_query = Mock()
            mock_filter = Mock()
            if model.__name__ == 'Conversation':
                mock_filter.first.return_value = empty_conversation
            elif model.__name__ == 'BotPersonality':
                mock_filter.first.return_value = self.mock_personality
            elif model.__name__ == 'Message':
                # Return empty messages for _calculate_conversation_metrics
                mock_filter.all.return_value = []
            else:
                mock_filter.first.return_value = None
                mock_filter.all.return_value = []
            mock_query.filter.return_value = mock_filter
            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        # Mock tracker
        mock_tracker.on_conversation_end.return_value = {"conversation_quality": "poor"}

        # Mock drift calculator
        mock_drift_calc.calculate_drift_after_conversation.return_value = []

        # End conversation
        self.manager.end_conversation(101, self.mock_db)

        # Verify summary service was NOT called (no messages to summarize)
        mock_summary_service.generate_summary.assert_not_called()

    @patch('services.conversation_manager.settings')
    @patch('services.conversation_manager.conversation_summary_service')
    @patch('services.conversation_manager.conversation_tracker')
    @patch('services.conversation_manager.personality_manager')
    @patch('services.conversation_manager.personality_drift_calculator')
    def test_conversation_end_continues_despite_summary_failure(
        self,
        mock_drift_calc,
        mock_personality_manager,
        mock_tracker,
        mock_summary_service,
        mock_settings
    ):
        """Test that conversation end completes successfully even if summary generation fails"""
        # Enable auto-summary generation
        mock_settings.AUTO_GENERATE_SUMMARIES = True

        # Mock summary service to raise exception
        mock_summary_service.generate_summary.side_effect = Exception("LLM service crashed")

        # Mock database queries
        def query_side_effect(model):
            mock_query = Mock()
            mock_filter = Mock()
            if model.__name__ == 'Conversation':
                mock_filter.first.return_value = self.mock_conversation
            elif model.__name__ == 'BotPersonality':
                mock_filter.first.return_value = self.mock_personality
            elif model.__name__ == 'Message':
                mock_filter.all.return_value = []  # No messages for fallback
            mock_query.filter.return_value = mock_filter
            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        # Mock tracker
        mock_tracker.on_conversation_end.return_value = {"conversation_quality": "good"}

        # Mock drift calculator
        mock_drift_calc.calculate_drift_after_conversation.return_value = []

        # End conversation - should not raise exception
        try:
            self.manager.end_conversation(100, self.mock_db)
            success = True
        except Exception:
            success = False

        # Verify conversation end succeeded despite summary failure
        assert success

        # Verify tracker was still called
        assert mock_tracker.on_conversation_end.called

        # Verify manager state was reset
        assert self.manager.current_conversation_id is None
        assert self.manager.message_count == 0
