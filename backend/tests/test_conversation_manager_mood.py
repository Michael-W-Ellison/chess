"""
Tests for ConversationManager Mood Change on Crisis
Tests that bot mood changes to 'concerned' when crisis is detected
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from services.conversation_manager import ConversationManager, conversation_manager


class TestMoodChangeOnCrisis:
    """Test that bot mood changes to 'concerned' during crisis"""

    def setup_method(self):
        """Set up test fixtures"""
        self.manager = ConversationManager()
        self.mock_db = Mock()

        # Mock user
        self.mock_user = Mock()
        self.mock_user.id = 1
        self.mock_user.name = "TestUser"
        self.mock_user.last_active = datetime.now()

        # Mock personality
        self.mock_personality = Mock()
        self.mock_personality.user_id = 1
        self.mock_personality.name = "ChessBot"
        self.mock_personality.mood = "happy"
        self.mock_personality.friendship_level = 5
        self.mock_personality.friendship_points = 50
        self.mock_personality.total_conversations = 10

        # Mock conversation
        self.mock_conversation = Mock()
        self.mock_conversation.id = 100
        self.mock_conversation.user_id = 1
        self.mock_conversation.message_count = 0

        # Mock message
        self.mock_message = Mock()
        self.mock_message.id = 1
        self.mock_message.conversation_id = 100
        self.mock_message.role = "user"
        self.mock_message.content = "test message"

    @patch('services.conversation_manager.safety_filter')
    @patch('services.conversation_manager.conversation_tracker')
    def test_mood_changes_to_concerned_on_suicide_crisis(
        self, mock_tracker, mock_safety_filter
    ):
        """Test mood changes to 'concerned' when suicide crisis detected"""
        # Mock safety filter to return critical severity (suicide)
        mock_safety_filter.check_message.return_value = {
            "safe": False,
            "flags": ["crisis"],
            "severity": "critical",
            "action": "crisis_response",
            "original_message": "I want to kill myself",
            "response_message": "Crisis response with 988...",
            "notify_parent": True,
            "details": {
                "crisis": {
                    "detected": True,
                    "primary_category": "suicide",
                }
            },
        }

        # Mock database queries
        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.return_value = self.mock_personality

        # Verify initial mood
        assert self.mock_personality.mood == "happy"

        # Process message that triggers crisis
        with patch.object(self.manager, '_store_message', return_value=self.mock_message):
            with patch.object(self.manager, '_handle_crisis', return_value="Crisis response"):
                result = self.manager.process_message(
                    user_message="I want to kill myself",
                    conversation_id=100,
                    user_id=1,
                    db=self.mock_db
                )

        # Verify mood was changed to 'concerned'
        assert self.mock_personality.mood == "concerned"

        # Verify metadata includes mood_change
        assert result["metadata"]["mood_change"] == "concerned"
        assert result["metadata"]["crisis_response"] is True

    @patch('services.conversation_manager.safety_filter')
    @patch('services.conversation_manager.conversation_tracker')
    def test_mood_changes_to_concerned_on_self_harm_crisis(
        self, mock_tracker, mock_safety_filter
    ):
        """Test mood changes to 'concerned' when self-harm crisis detected"""
        # Mock safety filter to return critical severity (self-harm)
        mock_safety_filter.check_message.return_value = {
            "safe": False,
            "flags": ["crisis"],
            "severity": "critical",
            "action": "crisis_response",
            "original_message": "I cut myself",
            "response_message": "Crisis response...",
            "notify_parent": True,
            "details": {
                "crisis": {
                    "detected": True,
                    "primary_category": "self_harm",
                }
            },
        }

        # Mock database queries
        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.return_value = self.mock_personality

        # Process message
        with patch.object(self.manager, '_store_message', return_value=self.mock_message):
            with patch.object(self.manager, '_handle_crisis', return_value="Crisis response"):
                result = self.manager.process_message(
                    user_message="I cut myself",
                    conversation_id=100,
                    user_id=1,
                    db=self.mock_db
                )

        # Verify mood changed
        assert self.mock_personality.mood == "concerned"

    @patch('services.conversation_manager.safety_filter')
    @patch('services.conversation_manager.conversation_tracker')
    def test_mood_changes_to_concerned_on_abuse_crisis(
        self, mock_tracker, mock_safety_filter
    ):
        """Test mood changes to 'concerned' when abuse crisis detected"""
        # Mock safety filter to return critical severity (abuse)
        mock_safety_filter.check_message.return_value = {
            "safe": False,
            "flags": ["abuse"],
            "severity": "critical",
            "action": "crisis_response",
            "original_message": "My dad hits me",
            "response_message": "Abuse response with Childhelp...",
            "notify_parent": True,
            "details": {
                "crisis": {
                    "detected": True,
                    "primary_category": "abuse_physical",
                }
            },
        }

        # Mock database queries
        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.return_value = self.mock_personality

        # Process message
        with patch.object(self.manager, '_store_message', return_value=self.mock_message):
            with patch.object(self.manager, '_handle_crisis', return_value="Abuse response"):
                result = self.manager.process_message(
                    user_message="My dad hits me",
                    conversation_id=100,
                    user_id=1,
                    db=self.mock_db
                )

        # Verify mood changed
        assert self.mock_personality.mood == "concerned"

    @patch('services.conversation_manager.safety_filter')
    @patch('services.conversation_manager.conversation_tracker')
    def test_mood_changes_from_different_initial_moods(
        self, mock_tracker, mock_safety_filter
    ):
        """Test mood changes to 'concerned' from various initial moods"""
        initial_moods = ["happy", "energetic", "curious", "playful", "calm"]

        for initial_mood in initial_moods:
            # Reset personality mood
            self.mock_personality.mood = initial_mood

            # Mock safety filter
            mock_safety_filter.check_message.return_value = {
                "safe": False,
                "flags": ["crisis"],
                "severity": "critical",
                "action": "crisis_response",
                "original_message": "I want to die",
                "response_message": "Crisis response...",
                "notify_parent": True,
                "details": {"crisis": {"primary_category": "suicide"}},
            }

            # Mock database queries
            query_mock = self.mock_db.query.return_value
            filter_mock = query_mock.filter.return_value
            filter_mock.first.return_value = self.mock_personality

            # Process message
            with patch.object(self.manager, '_store_message', return_value=self.mock_message):
                with patch.object(self.manager, '_handle_crisis', return_value="Crisis response"):
                    result = self.manager.process_message(
                        user_message="I want to die",
                        conversation_id=100,
                        user_id=1,
                        db=self.mock_db
                    )

            # Verify mood changed to 'concerned' regardless of initial mood
            assert self.mock_personality.mood == "concerned", f"Failed for initial mood: {initial_mood}"

    @patch('services.conversation_manager.safety_filter')
    @patch('services.conversation_manager.conversation_tracker')
    def test_mood_does_not_change_on_non_critical_severity(
        self, mock_tracker, mock_safety_filter
    ):
        """Test mood does NOT change for non-critical severity (high, medium, low)"""
        # Mock safety filter to return high severity (not critical)
        mock_safety_filter.check_message.return_value = {
            "safe": False,
            "flags": ["profanity"],
            "severity": "high",
            "action": "block_with_education",
            "original_message": "severe profanity",
            "response_message": "Educational response...",
            "notify_parent": True,
            "details": {},
        }

        # Mock database queries for personality
        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value

        # Create a list to track calls - personality query should happen later
        personality_query_results = [self.mock_personality, self.mock_personality]

        def side_effect_first():
            return personality_query_results.pop(0)

        filter_mock.first.side_effect = side_effect_first

        # Mock tracker
        mock_tracker.on_message_sent.return_value = {
            "points_awarded": [],
            "activities_detected": [],
        }

        # Mock memory manager
        with patch('services.conversation_manager.memory_manager') as mock_memory:
            mock_memory.extract_and_store_memories.return_value = None
            mock_memory.extract_keywords.return_value = []
            mock_memory.get_relevant_memories.return_value = []

            # Mock LLM service
            with patch('services.conversation_manager.llm_service') as mock_llm:
                mock_llm.is_loaded = False

                # Mock message storage
                with patch.object(self.manager, '_store_message', return_value=self.mock_message):
                    # Mock conversation query
                    conv_query = Mock()
                    conv_filter = Mock()
                    conv_filter.first.return_value = self.mock_conversation
                    conv_query.filter.return_value = conv_filter
                    self.mock_db.query.return_value = conv_query

                    # Verify initial mood
                    initial_mood = "happy"
                    self.mock_personality.mood = initial_mood

                    # Process message with high (not critical) severity
                    result = self.manager.process_message(
                        user_message="severe profanity",
                        conversation_id=100,
                        user_id=1,
                        db=self.mock_db
                    )

                    # Verify mood did NOT change (still happy, not concerned)
                    # Since the severity was 'high' not 'critical', mood should stay the same
                    # Note: The mood might still be 'happy' if it wasn't changed
                    assert "mood_change" not in result.get("metadata", {})

    @patch('services.conversation_manager.safety_filter')
    @patch('services.conversation_manager.conversation_tracker')
    def test_mood_change_persists_in_database(
        self, mock_tracker, mock_safety_filter
    ):
        """Test that mood change is committed to database"""
        # Mock safety filter
        mock_safety_filter.check_message.return_value = {
            "safe": False,
            "flags": ["crisis"],
            "severity": "critical",
            "action": "crisis_response",
            "original_message": "I want to kill myself",
            "response_message": "Crisis response...",
            "notify_parent": True,
            "details": {"crisis": {"primary_category": "suicide"}},
        }

        # Mock database queries
        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.return_value = self.mock_personality

        # Process message
        with patch.object(self.manager, '_store_message', return_value=self.mock_message):
            with patch.object(self.manager, '_handle_crisis', return_value="Crisis response"):
                result = self.manager.process_message(
                    user_message="I want to kill myself",
                    conversation_id=100,
                    user_id=1,
                    db=self.mock_db
                )

        # Verify database commit was called
        assert self.mock_db.commit.called

        # Verify mood was changed
        assert self.mock_personality.mood == "concerned"

    @patch('services.conversation_manager.safety_filter')
    @patch('services.conversation_manager.conversation_tracker')
    def test_mood_change_handles_missing_personality(
        self, mock_tracker, mock_safety_filter
    ):
        """Test that mood change handles case where personality is not found"""
        # Mock safety filter
        mock_safety_filter.check_message.return_value = {
            "safe": False,
            "flags": ["crisis"],
            "severity": "critical",
            "action": "crisis_response",
            "original_message": "I want to kill myself",
            "response_message": "Crisis response...",
            "notify_parent": True,
            "details": {"crisis": {"primary_category": "suicide"}},
        }

        # Mock database queries - personality NOT found
        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.return_value = None  # No personality found

        # Process message - should not crash
        with patch.object(self.manager, '_store_message', return_value=self.mock_message):
            with patch.object(self.manager, '_handle_crisis', return_value="Crisis response"):
                result = self.manager.process_message(
                    user_message="I want to kill myself",
                    conversation_id=100,
                    user_id=1,
                    db=self.mock_db
                )

        # Should still return crisis response even without personality
        assert result["metadata"]["crisis_response"] is True


class TestMoodChangeMetadata:
    """Test that mood change is properly reflected in metadata"""

    def setup_method(self):
        """Set up test fixtures"""
        self.manager = ConversationManager()
        self.mock_db = Mock()

        # Mock personality
        self.mock_personality = Mock()
        self.mock_personality.user_id = 1
        self.mock_personality.mood = "happy"

        # Mock message
        self.mock_message = Mock()
        self.mock_message.id = 1

    @patch('services.conversation_manager.safety_filter')
    @patch('services.conversation_manager.conversation_tracker')
    def test_metadata_includes_mood_change(
        self, mock_tracker, mock_safety_filter
    ):
        """Test that response metadata includes mood_change field"""
        # Mock safety filter
        mock_safety_filter.check_message.return_value = {
            "safe": False,
            "flags": ["crisis"],
            "severity": "critical",
            "action": "crisis_response",
            "original_message": "test",
            "response_message": "Crisis response...",
            "notify_parent": True,
            "details": {"crisis": {"primary_category": "suicide"}},
        }

        # Mock database
        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.return_value = self.mock_personality

        # Process message
        with patch.object(self.manager, '_store_message', return_value=self.mock_message):
            with patch.object(self.manager, '_handle_crisis', return_value="Crisis response"):
                result = self.manager.process_message(
                    user_message="crisis message",
                    conversation_id=100,
                    user_id=1,
                    db=self.mock_db
                )

        # Verify metadata
        assert "metadata" in result
        assert "mood_change" in result["metadata"]
        assert result["metadata"]["mood_change"] == "concerned"

    @patch('services.conversation_manager.safety_filter')
    @patch('services.conversation_manager.conversation_tracker')
    def test_metadata_includes_all_crisis_fields(
        self, mock_tracker, mock_safety_filter
    ):
        """Test that crisis response metadata includes all expected fields"""
        # Mock safety filter
        mock_safety_filter.check_message.return_value = {
            "safe": False,
            "flags": ["crisis"],
            "severity": "critical",
            "action": "crisis_response",
            "original_message": "test",
            "response_message": "Crisis response...",
            "notify_parent": True,
            "details": {"crisis": {"primary_category": "suicide"}},
        }

        # Mock database
        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.return_value = self.mock_personality

        # Process message
        with patch.object(self.manager, '_store_message', return_value=self.mock_message):
            with patch.object(self.manager, '_handle_crisis', return_value="Crisis response"):
                result = self.manager.process_message(
                    user_message="crisis message",
                    conversation_id=100,
                    user_id=1,
                    db=self.mock_db
                )

        # Verify all expected metadata fields
        metadata = result["metadata"]
        assert metadata["safety_flag"] is True
        assert metadata["severity"] == "critical"
        assert metadata["crisis_response"] is True
        assert metadata["flags"] == ["crisis"]
        assert metadata["notify_parent"] is True
        assert metadata["mood_change"] == "concerned"
