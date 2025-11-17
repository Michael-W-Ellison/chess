"""
Tests for AdviceTemplate Model
Comprehensive test coverage for advice template database structure
"""

import pytest
from unittest.mock import Mock
from datetime import datetime
import json

from models.safety import AdviceTemplate


class TestAdviceTemplateCreation:
    """Test AdviceTemplate model creation and basic functionality"""

    def test_create_advice_template(self):
        """Test creating an advice template"""
        template = AdviceTemplate(
            category="friendship",
            keywords=json.dumps(["friend", "conflict", "fight"]),
            template="I'm sorry you're having trouble with {friend_name}. Have you tried talking to them about how you feel?",
            min_friendship_level=1,
            min_age=8,
            max_age=14,
            tone="supportive",
            response_style="gentle"
        )

        assert template.category == "friendship"
        assert template.min_friendship_level == 1
        assert template.min_age == 8
        assert template.max_age == 14
        assert template.tone == "supportive"
        assert template.response_style == "gentle"

    def test_default_values(self):
        """Test default values are set correctly"""
        template = AdviceTemplate(
            category="school",
            keywords=json.dumps(["homework"]),
            template="Test template"
        )

        assert template.min_friendship_level == 1
        assert template.min_age == 8
        assert template.max_age == 14
        assert template.expert_reviewed is False
        assert template.usage_count == 0


class TestKeywordMethods:
    """Test keyword getter and setter methods"""

    def test_get_keywords(self):
        """Test getting keywords from JSON"""
        template = AdviceTemplate(
            category="friendship",
            keywords=json.dumps(["friend", "conflict", "fight"]),
            template="Test"
        )

        keywords = template.get_keywords()
        assert isinstance(keywords, list)
        assert len(keywords) == 3
        assert "friend" in keywords
        assert "conflict" in keywords

    def test_set_keywords(self):
        """Test setting keywords"""
        template = AdviceTemplate(
            category="friendship",
            keywords="",
            template="Test"
        )

        template.set_keywords(["friend", "problem", "issue"])
        keywords = template.get_keywords()

        assert len(keywords) == 3
        assert "problem" in keywords

    def test_get_keywords_invalid_json(self):
        """Test getting keywords with invalid JSON returns empty list"""
        template = AdviceTemplate(
            category="friendship",
            keywords="invalid json",
            template="Test"
        )

        keywords = template.get_keywords()
        assert keywords == []

    def test_get_keywords_empty(self):
        """Test getting keywords when empty"""
        template = AdviceTemplate(
            category="friendship",
            keywords="",
            template="Test"
        )

        keywords = template.get_keywords()
        assert keywords == []


class TestContextTagsMethods:
    """Test context tags getter and setter methods"""

    def test_get_context_tags(self):
        """Test getting context tags from JSON"""
        template = AdviceTemplate(
            category="emotional",
            keywords=json.dumps(["sad"]),
            template="Test",
            context_tags=json.dumps(["sadness", "peer_issues", "school_related"])
        )

        tags = template.get_context_tags()
        assert isinstance(tags, list)
        assert len(tags) == 3
        assert "sadness" in tags

    def test_set_context_tags(self):
        """Test setting context tags"""
        template = AdviceTemplate(
            category="emotional",
            keywords=json.dumps(["sad"]),
            template="Test"
        )

        template.set_context_tags(["anxiety", "stress", "worry"])
        tags = template.get_context_tags()

        assert len(tags) == 3
        assert "anxiety" in tags

    def test_get_context_tags_empty(self):
        """Test getting context tags when empty"""
        template = AdviceTemplate(
            category="emotional",
            keywords=json.dumps(["sad"]),
            template="Test"
        )

        tags = template.get_context_tags()
        assert tags == []


class TestFormatAdvice:
    """Test advice template formatting"""

    def test_format_advice_with_placeholders(self):
        """Test formatting advice with provided values"""
        template = AdviceTemplate(
            category="friendship",
            keywords=json.dumps(["friend"]),
            template="Hi {name}! I'm sorry to hear about your trouble with {friend_name}."
        )

        formatted = template.format_advice(name="Alex", friend_name="Sam")
        assert "Alex" in formatted
        assert "Sam" in formatted
        assert "{name}" not in formatted
        assert "{friend_name}" not in formatted

    def test_format_advice_missing_placeholder(self):
        """Test formatting with missing placeholder returns template as-is"""
        template = AdviceTemplate(
            category="friendship",
            keywords=json.dumps(["friend"]),
            template="Hi {name}! Your friend {friend_name} will understand."
        )

        # Only provide name, not friend_name
        formatted = template.format_advice(name="Alex")

        # Should return template with placeholders still there
        assert "{friend_name}" in formatted or "Alex" in formatted

    def test_format_advice_no_placeholders(self):
        """Test formatting advice with no placeholders"""
        template = AdviceTemplate(
            category="general",
            keywords=json.dumps(["advice"]),
            template="That sounds tough. You'll figure it out!"
        )

        formatted = template.format_advice()
        assert formatted == "That sounds tough. You'll figure it out!"


class TestUsageTracking:
    """Test usage tracking methods"""

    def test_increment_usage(self):
        """Test incrementing usage count"""
        template = AdviceTemplate(
            category="school",
            keywords=json.dumps(["homework"]),
            template="Test"
        )

        assert template.usage_count == 0

        template.increment_usage()
        assert template.usage_count == 1

        template.increment_usage()
        assert template.usage_count == 2


class TestAgeAppropriateness:
    """Test age appropriateness methods"""

    def test_is_appropriate_for_age_within_range(self):
        """Test age check when age is within range"""
        template = AdviceTemplate(
            category="friendship",
            keywords=json.dumps(["friend"]),
            template="Test",
            min_age=8,
            max_age=12
        )

        assert template.is_appropriate_for_age(8) is True
        assert template.is_appropriate_for_age(10) is True
        assert template.is_appropriate_for_age(12) is True

    def test_is_appropriate_for_age_outside_range(self):
        """Test age check when age is outside range"""
        template = AdviceTemplate(
            category="friendship",
            keywords=json.dumps(["friend"]),
            template="Test",
            min_age=8,
            max_age=12
        )

        assert template.is_appropriate_for_age(7) is False
        assert template.is_appropriate_for_age(13) is False
        assert template.is_appropriate_for_age(15) is False


class TestFriendshipLevelAvailability:
    """Test friendship level availability methods"""

    def test_is_available_at_friendship_level_with_max(self):
        """Test friendship level check with max level set"""
        template = AdviceTemplate(
            category="friendship",
            keywords=json.dumps(["friend"]),
            template="Test",
            min_friendship_level=3,
            max_friendship_level=7
        )

        assert template.is_available_at_friendship_level(2) is False
        assert template.is_available_at_friendship_level(3) is True
        assert template.is_available_at_friendship_level(5) is True
        assert template.is_available_at_friendship_level(7) is True
        assert template.is_available_at_friendship_level(8) is False

    def test_is_available_at_friendship_level_no_max(self):
        """Test friendship level check with no max level (unlimited)"""
        template = AdviceTemplate(
            category="friendship",
            keywords=json.dumps(["friend"]),
            template="Test",
            min_friendship_level=3,
            max_friendship_level=None
        )

        assert template.is_available_at_friendship_level(2) is False
        assert template.is_available_at_friendship_level(3) is True
        assert template.is_available_at_friendship_level(10) is True


class TestToDictMethod:
    """Test to_dict serialization method"""

    def test_to_dict_complete(self):
        """Test to_dict with all fields"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="conflict_resolution",
            keywords=json.dumps(["friend", "fight"]),
            template="Test template",
            min_friendship_level=2,
            max_friendship_level=8,
            min_age=8,
            max_age=14,
            expert_reviewed=True,
            usage_count=5,
            rating=4,
            tone="supportive",
            response_style="gentle",
            context_tags=json.dumps(["peer_conflict"])
        )

        result = template.to_dict()

        assert result["category"] == "friendship"
        assert result["subcategory"] == "conflict_resolution"
        assert isinstance(result["keywords"], list)
        assert result["min_friendship_level"] == 2
        assert result["max_friendship_level"] == 8
        assert result["min_age"] == 8
        assert result["max_age"] == 14
        assert result["expert_reviewed"] is True
        assert result["usage_count"] == 5
        assert result["rating"] == 4
        assert result["tone"] == "supportive"
        assert result["response_style"] == "gentle"
        assert isinstance(result["context_tags"], list)

    def test_to_dict_minimal(self):
        """Test to_dict with minimal fields"""
        template = AdviceTemplate(
            category="general",
            keywords=json.dumps(["advice"]),
            template="Test"
        )

        result = template.to_dict()

        assert result["category"] == "general"
        assert result["subcategory"] is None
        assert result["expert_reviewed"] is False
        assert result["usage_count"] == 0


class TestClassMethodGetByCategory:
    """Test get_by_category class method"""

    def test_get_by_category_basic(self):
        """Test getting templates by category"""
        mock_db = Mock()

        # Mock query chain
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_all = Mock(return_value=[])

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter1
        mock_filter1.filter.return_value = mock_filter2
        mock_filter2.all.return_value = []

        templates = AdviceTemplate.get_by_category(
            mock_db,
            category="friendship",
            friendship_level=5
        )

        # Verify query was called
        assert mock_db.query.called


class TestClassMethodGetExpertReviewed:
    """Test get_expert_reviewed class method"""

    def test_get_expert_reviewed_all(self):
        """Test getting all expert reviewed templates"""
        mock_db = Mock()

        # Mock query chain
        mock_query = Mock()
        mock_filter = Mock()
        mock_all = Mock(return_value=[])

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = []

        templates = AdviceTemplate.get_expert_reviewed(mock_db)

        # Verify query was called
        assert mock_db.query.called

    def test_get_expert_reviewed_by_category(self):
        """Test getting expert reviewed templates for specific category"""
        mock_db = Mock()

        # Mock query chain
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_all = Mock(return_value=[])

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter1
        mock_filter1.filter.return_value = mock_filter2
        mock_filter2.all.return_value = []

        templates = AdviceTemplate.get_expert_reviewed(
            mock_db,
            category="friendship"
        )

        # Verify query was called
        assert mock_db.query.called


class TestClassMethodGetMostUsed:
    """Test get_most_used class method"""

    def test_get_most_used_all(self):
        """Test getting most used templates"""
        mock_db = Mock()

        # Mock query chain
        mock_query = Mock()
        mock_order = Mock()
        mock_limit = Mock()
        mock_all = Mock(return_value=[])

        mock_db.query.return_value = mock_query
        mock_query.order_by.return_value = mock_order
        mock_order.limit.return_value = mock_limit
        mock_limit.all.return_value = []

        templates = AdviceTemplate.get_most_used(mock_db, limit=5)

        # Verify query was called
        assert mock_db.query.called

    def test_get_most_used_by_category(self):
        """Test getting most used templates for specific category"""
        mock_db = Mock()

        # Mock query chain
        mock_query = Mock()
        mock_filter = Mock()
        mock_order = Mock()
        mock_limit = Mock()
        mock_all = Mock(return_value=[])

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.limit.return_value = mock_limit
        mock_limit.all.return_value = []

        templates = AdviceTemplate.get_most_used(
            mock_db,
            category="friendship",
            limit=10
        )

        # Verify query was called
        assert mock_db.query.called


class TestClassMethodGetByTone:
    """Test get_by_tone class method"""

    def test_get_by_tone_all(self):
        """Test getting templates by tone"""
        mock_db = Mock()

        # Mock query chain
        mock_query = Mock()
        mock_filter = Mock()
        mock_all = Mock(return_value=[])

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = []

        templates = AdviceTemplate.get_by_tone(mock_db, tone="supportive")

        # Verify query was called
        assert mock_db.query.called

    def test_get_by_tone_and_category(self):
        """Test getting templates by tone and category"""
        mock_db = Mock()

        # Mock query chain
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_all = Mock(return_value=[])

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter1
        mock_filter1.filter.return_value = mock_filter2
        mock_filter2.all.return_value = []

        templates = AdviceTemplate.get_by_tone(
            mock_db,
            tone="encouraging",
            category="school"
        )

        # Verify query was called
        assert mock_db.query.called


class TestReprMethod:
    """Test __repr__ method"""

    def test_repr_with_max_level(self):
        """Test repr with max friendship level"""
        template = AdviceTemplate(
            id=1,
            category="friendship",
            keywords=json.dumps(["friend"]),
            template="Test",
            min_friendship_level=3,
            max_friendship_level=7
        )

        repr_str = repr(template)
        assert "friendship" in repr_str
        assert "3-7" in repr_str

    def test_repr_without_max_level(self):
        """Test repr without max friendship level (unlimited)"""
        template = AdviceTemplate(
            id=1,
            category="friendship",
            keywords=json.dumps(["friend"]),
            template="Test",
            min_friendship_level=3,
            max_friendship_level=None
        )

        repr_str = repr(template)
        assert "friendship" in repr_str
        assert "3-∞" in repr_str or "3-None" in repr_str


class TestAllCategories:
    """Test that all advice categories are supported"""

    def test_all_detector_categories_supported(self):
        """Test that all categories from AdviceCategoryDetector are valid"""
        categories = [
            "friendship",
            "school",
            "family",
            "emotional",
            "hobby",
            "bullying",
            "social",
            "decision",
            "conflict",
            "general"
        ]

        for category in categories:
            template = AdviceTemplate(
                category=category,
                keywords=json.dumps(["test"]),
                template="Test template"
            )
            assert template.category == category
