"""
Tests for Template Personalization Service
Comprehensive test coverage for template personalization with user data
"""

import pytest
from unittest.mock import Mock, MagicMock
import json

from services.template_personalization_service import (
    TemplatePersonalizationService,
    template_personalization_service,
    personalize_template,
    get_placeholder_requirements,
    can_fill_template,
    get_stats,
)
from models.safety import AdviceTemplate


class TestTemplatePersonalizationServiceInitialization:
    """Test TemplatePersonalizationService initialization"""

    def test_initialization(self):
        """Test service initializes correctly"""
        service = TemplatePersonalizationService()
        assert service is not None
        assert service.templates_personalized == 0

    def test_global_instance(self):
        """Test global instance is available"""
        assert template_personalization_service is not None


class TestUserContextExtraction:
    """Test user context extraction from database"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = TemplatePersonalizationService()
        self.mock_db = Mock()

    def test_extract_user_context_with_user(self):
        """Test extracting context when user exists"""
        # Mock user
        mock_user = Mock()
        mock_user.name = "Alex"

        # Mock personality
        mock_personality = Mock()
        mock_personality.name = "ChessBot"
        mock_personality.friendship_level = 5
        mock_personality.mood = "happy"
        mock_personality.get_interests.return_value = ["chess", "puzzles", "science"]
        mock_personality.get_quirks.return_value = ["uses_emojis"]

        # Mock database queries
        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value

        # Return user first, then personality
        filter_mock.first.side_effect = [mock_user, mock_personality]

        context = self.service._extract_user_context(self.mock_db, user_id=1)

        assert context["name"] == "Alex"
        assert context["user_name"] == "Alex"
        assert context["bot_name"] == "ChessBot"
        assert context["friendship_level"] == 5
        assert "chess" in context["interests"]

    def test_extract_user_context_no_user(self):
        """Test extracting context when user doesn't exist"""
        # Mock no user found
        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.return_value = None

        context = self.service._extract_user_context(self.mock_db, user_id=999)

        # Should have defaults
        assert context["name"] == "friend"
        assert context["user_name"] == "friend"
        assert context["bot_name"] == "ChessBot"


class TestMessageContextExtraction:
    """Test message context extraction"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = TemplatePersonalizationService()

    def test_extract_friend_names(self):
        """Test extracting friend names from message"""
        message = "My friend Sam is being mean to me"
        names = self.service._extract_friend_names(message)
        assert "Sam" in names

    def test_extract_multiple_friend_names(self):
        """Test extracting multiple friend names"""
        message = "Alex and Jordan are my friends but Alex said something"
        names = self.service._extract_friend_names(message)
        assert "Alex" in names
        assert "Jordan" in names

    def test_extract_friend_names_no_names(self):
        """Test when no friend names in message"""
        message = "I'm having a bad day"
        names = self.service._extract_friend_names(message)
        assert len(names) == 0

    def test_extract_activities(self):
        """Test extracting activities from message"""
        message = "I'm playing soccer with my friends"
        activities = self.service._extract_activities(message)
        assert "soccer" in activities

    def test_extract_topics(self):
        """Test extracting topics from message"""
        message = "I have homework about dinosaurs"
        topics = self.service._extract_topics(message)
        assert "dinosaurs" in topics

    def test_extract_situation(self):
        """Test extracting situation description"""
        message = "I'm having trouble with my math homework"
        situation = self.service._extract_situation(message)
        assert situation is not None
        assert "trouble" in situation or "math" in situation

    def test_extract_message_context_with_mood(self):
        """Test extracting context with detected mood"""
        message = "My friend Sam is ignoring me"
        context = self.service._extract_message_context(message, detected_mood="sad")

        assert context["feeling"] == "sad"
        assert context["emotion"] == "sad"
        assert context["friend_name"] == "Sam"


class TestPersonalizeTemplate:
    """Test template personalization"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = TemplatePersonalizationService()
        self.mock_db = Mock()

        # Create mock template
        self.mock_template = Mock(spec=AdviceTemplate)
        self.mock_template.id = 1
        self.mock_template.template = "Hi {name}! I understand you're having trouble with {friend_name}."
        self.mock_template.format_advice = lambda **kwargs: self.mock_template.template.format(**kwargs)

    def test_personalize_template_basic(self):
        """Test basic template personalization"""
        # Mock user
        mock_user = Mock()
        mock_user.name = "Alex"

        # Mock personality
        mock_personality = Mock()
        mock_personality.name = "ChessBot"
        mock_personality.get_interests.return_value = []
        mock_personality.get_quirks.return_value = []

        # Mock database
        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.side_effect = [mock_user, mock_personality]

        user_message = "My friend Sam is ignoring me"

        result = self.service.personalize_template(
            template=self.mock_template,
            db=self.mock_db,
            user_id=1,
            user_message=user_message
        )

        assert "Alex" in result
        assert "Sam" in result

    def test_personalize_template_with_additional_context(self):
        """Test personalization with additional context"""
        # Mock user
        mock_user = Mock()
        mock_user.name = "Alex"

        # Mock personality
        mock_personality = Mock()
        mock_personality.name = "ChessBot"
        mock_personality.get_interests.return_value = []
        mock_personality.get_quirks.return_value = []

        # Mock database
        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.side_effect = [mock_user, mock_personality]

        result = self.service.personalize_template(
            template=self.mock_template,
            db=self.mock_db,
            user_id=1,
            additional_context={"friend_name": "Jordan"}
        )

        assert "Alex" in result
        assert "Jordan" in result

    def test_personalize_template_increments_counter(self):
        """Test that personalization increments counter"""
        # Mock user and personality
        mock_user = Mock()
        mock_user.name = "Alex"

        mock_personality = Mock()
        mock_personality.name = "ChessBot"
        mock_personality.get_interests.return_value = []
        mock_personality.get_quirks.return_value = []

        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.side_effect = [mock_user, mock_personality]

        initial_count = self.service.templates_personalized

        self.service.personalize_template(
            template=self.mock_template,
            db=self.mock_db,
            user_id=1,
            user_message="test",
            additional_context={"friend_name": "Sam"}
        )

        assert self.service.templates_personalized == initial_count + 1


class TestPlaceholderCleaning:
    """Test placeholder cleaning and default values"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = TemplatePersonalizationService()

    def test_get_default_placeholder_value(self):
        """Test getting default values for placeholders"""
        assert self.service._get_default_placeholder_value("name") == "friend"
        assert self.service._get_default_placeholder_value("friend_name") == "your friend"
        assert self.service._get_default_placeholder_value("bot_name") == "me"
        assert self.service._get_default_placeholder_value("feeling") == "this way"

    def test_clean_remaining_placeholders(self):
        """Test cleaning unfilled placeholders"""
        text = "Hi {name}! How are you feeling about {situation}?"
        filled_context = {"name": "Alex"}

        cleaned = self.service._clean_remaining_placeholders(text, filled_context)

        assert "Alex" in cleaned
        # situation should be replaced with default or removed gracefully
        assert "{situation}" not in cleaned

    def test_remove_placeholder_gracefully(self):
        """Test removing placeholder gracefully"""
        text = "Talk to {friend_name} and see what happens"
        result = self.service._remove_placeholder_gracefully(text, "friend_name")

        # Placeholder should be removed
        assert "{friend_name}" not in result
        # Grammar should be cleaned up
        assert result.strip()  # Should not be empty


class TestPlaceholderRequirements:
    """Test placeholder requirement analysis"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = TemplatePersonalizationService()

    def test_get_placeholder_requirements(self):
        """Test getting placeholder requirements from template"""
        mock_template = Mock(spec=AdviceTemplate)
        mock_template.template = "Hi {name}! Your friend {friend_name} and {topic} are important."

        requirements = self.service.get_placeholder_requirements(mock_template)

        assert "name" in requirements
        assert "friend_name" in requirements
        assert "topic" in requirements
        assert len(requirements) == 3

    def test_get_placeholder_requirements_no_placeholders(self):
        """Test template with no placeholders"""
        mock_template = Mock(spec=AdviceTemplate)
        mock_template.template = "This is a simple message with no placeholders."

        requirements = self.service.get_placeholder_requirements(mock_template)

        assert len(requirements) == 0

    def test_get_placeholder_requirements_duplicate_placeholders(self):
        """Test template with duplicate placeholders"""
        mock_template = Mock(spec=AdviceTemplate)
        mock_template.template = "Hi {name}! {name}, have you talked to {friend_name}?"

        requirements = self.service.get_placeholder_requirements(mock_template)

        # Should deduplicate
        assert requirements.count("name") == 1
        assert len(requirements) == 2


class TestCanFillTemplate:
    """Test checking if template can be filled"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = TemplatePersonalizationService()

    def test_can_fill_template_with_all_context(self):
        """Test when we have all required context"""
        mock_template = Mock(spec=AdviceTemplate)
        mock_template.template = "Hi {name}! Talk to {friend_name}."

        available_context = {
            "name": "Alex",
            "friend_name": "Sam"
        }

        can_fill = self.service.can_fill_template(mock_template, available_context)
        assert can_fill is True

    def test_can_fill_template_with_defaults(self):
        """Test when we have defaults for missing context"""
        mock_template = Mock(spec=AdviceTemplate)
        mock_template.template = "Hi {name}! How are you feeling about {situation}?"

        available_context = {
            "name": "Alex"
        }

        # situation has a default value
        can_fill = self.service.can_fill_template(mock_template, available_context)
        assert can_fill is True

    def test_can_fill_template_no_context(self):
        """Test when template has no placeholders"""
        mock_template = Mock(spec=AdviceTemplate)
        mock_template.template = "This is a simple message."

        available_context = {}

        can_fill = self.service.can_fill_template(mock_template, available_context)
        assert can_fill is True


class TestServiceStatistics:
    """Test service statistics"""

    def test_get_stats(self):
        """Test getting service statistics"""
        service = TemplatePersonalizationService()
        service.templates_personalized = 10

        stats = service.get_stats()

        assert stats["templates_personalized"] == 10
        assert stats["service_status"] == "active"


class TestConvenienceFunctions:
    """Test module-level convenience functions"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_db = Mock()
        self.mock_template = Mock(spec=AdviceTemplate)
        self.mock_template.id = 1
        self.mock_template.template = "Hi {name}!"
        self.mock_template.format_advice = lambda **kwargs: self.mock_template.template.format(**kwargs)

    def test_personalize_template_function(self):
        """Test personalize_template convenience function"""
        # Mock user and personality
        mock_user = Mock()
        mock_user.name = "Alex"

        mock_personality = Mock()
        mock_personality.name = "ChessBot"
        mock_personality.get_interests.return_value = []
        mock_personality.get_quirks.return_value = []

        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.side_effect = [mock_user, mock_personality]

        result = personalize_template(
            template=self.mock_template,
            db=self.mock_db,
            user_id=1
        )

        assert result is not None
        assert "Alex" in result

    def test_get_placeholder_requirements_function(self):
        """Test get_placeholder_requirements convenience function"""
        requirements = get_placeholder_requirements(self.mock_template)
        assert "name" in requirements

    def test_can_fill_template_function(self):
        """Test can_fill_template convenience function"""
        available_context = {"name": "Alex"}
        can_fill = can_fill_template(self.mock_template, available_context)
        assert can_fill is True

    def test_get_stats_function(self):
        """Test get_stats convenience function"""
        stats = get_stats()
        assert stats is not None
        assert "service_status" in stats


class TestEdgeCases:
    """Test edge cases and error handling"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = TemplatePersonalizationService()
        self.mock_db = Mock()

    def test_extract_friend_names_filters_non_names(self):
        """Test that common non-name words are filtered"""
        message = "He said that She told me The problem is"
        names = self.service._extract_friend_names(message)

        # Common words should be filtered out
        assert "He" not in names
        assert "She" not in names
        assert "The" not in names

    def test_extract_activities_filters_stopwords(self):
        """Test that stopwords are filtered from activities"""
        message = "I'm playing the game with my friends"
        activities = self.service._extract_activities(message)

        # Stopwords should be filtered
        assert "the" not in activities
        assert "my" not in activities

    def test_extract_situation_with_question_mark(self):
        """Test situation extraction with question marks"""
        message = "I'm having trouble with homework?"
        situation = self.service._extract_situation(message)

        assert situation is not None

    def test_extract_situation_too_long(self):
        """Test that very long situations are not extracted"""
        message = "I'm having a really really really really really really really really long problem with everything"
        situation = self.service._extract_situation(message)

        # Should either be None or truncated
        if situation:
            assert len(situation) < 50

    def test_personalize_with_no_message(self):
        """Test personalization without user message"""
        # Mock user
        mock_user = Mock()
        mock_user.name = "Alex"

        # Mock personality
        mock_personality = Mock()
        mock_personality.name = "ChessBot"
        mock_personality.get_interests.return_value = []
        mock_personality.get_quirks.return_value = []

        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.side_effect = [mock_user, mock_personality]

        mock_template = Mock(spec=AdviceTemplate)
        mock_template.id = 1
        mock_template.template = "Hi {name}!"
        mock_template.format_advice = lambda **kwargs: mock_template.template.format(**kwargs)

        result = self.service.personalize_template(
            template=mock_template,
            db=self.mock_db,
            user_id=1,
            user_message=None  # No message
        )

        # Should still work with just user context
        assert "Alex" in result


class TestRealWorldScenarios:
    """Test real-world usage scenarios"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = TemplatePersonalizationService()
        self.mock_db = Mock()

    def test_friendship_advice_personalization(self):
        """Test personalization for friendship advice"""
        # Mock user and personality
        mock_user = Mock()
        mock_user.name = "Alex"

        mock_personality = Mock()
        mock_personality.name = "ChessBot"
        mock_personality.friendship_level = 5
        mock_personality.mood = "supportive"
        mock_personality.get_interests.return_value = ["games"]
        mock_personality.get_quirks.return_value = []

        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.side_effect = [mock_user, mock_personality]

        # Create friendship advice template
        mock_template = Mock(spec=AdviceTemplate)
        mock_template.id = 1
        mock_template.template = "Hi {name}! I'm sorry to hear about your trouble with {friend_name}. Have you tried talking to them about how you feel?"
        mock_template.format_advice = lambda **kwargs: mock_template.template.format(**kwargs)

        user_message = "My friend Jordan is being mean to me and ignoring me"

        result = self.service.personalize_template(
            template=mock_template,
            db=self.mock_db,
            user_id=1,
            user_message=user_message,
            detected_mood="sad"
        )

        assert "Alex" in result
        assert "Jordan" in result
        assert "how you feel" in result

    def test_school_advice_personalization(self):
        """Test personalization for school advice"""
        # Mock user and personality
        mock_user = Mock()
        mock_user.name = "Sam"

        mock_personality = Mock()
        mock_personality.name = "StudyBot"
        mock_personality.get_interests.return_value = ["reading"]
        mock_personality.get_quirks.return_value = []

        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.side_effect = [mock_user, mock_personality]

        # Create school advice template
        mock_template = Mock(spec=AdviceTemplate)
        mock_template.id = 2
        mock_template.template = "Hi {name}! {topic} can be tricky. Have you tried breaking it down into smaller parts?"
        mock_template.format_advice = lambda **kwargs: mock_template.template.format(**kwargs)

        user_message = "I'm struggling with my homework about fractions"

        result = self.service.personalize_template(
            template=mock_template,
            db=self.mock_db,
            user_id=1,
            user_message=user_message
        )

        assert "Sam" in result
        assert "fractions" in result or "topic" not in result.lower()
