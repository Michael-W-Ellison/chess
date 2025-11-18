"""
Tests for Homeschool Stress Advice Templates
Verifies that homeschool stress templates are properly structured and functional
"""

import pytest
from unittest.mock import Mock
import json

from models.safety import AdviceTemplate


class TestHomeschoolStressTemplateStructure:
    """Test homeschool stress template structure and fields"""

    def test_homeschool_stress_templates_exist(self):
        """Test that homeschool_stress subcategory templates can be queried"""
        mock_db = Mock()

        # Mock query chain
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_filter3 = Mock()
        mock_all = Mock(return_value=[])

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter1
        mock_filter1.filter.return_value = mock_filter2
        mock_filter2.filter.return_value = mock_filter3
        mock_filter3.all.return_value = []

        # Query by subcategory
        templates = AdviceTemplate.get_by_category(
            mock_db,
            category="school",
            friendship_level=3,
            subcategory="homeschool_stress"
        )

        # Verify query was called
        assert mock_db.query.called

    def test_homeschool_template_has_required_fields(self):
        """Test that homeschool templates have all required fields"""
        template = AdviceTemplate(
            category="school",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool", "lonely", "isolated"]),
            template="Hey {name}, I hear you - being homeschooled can sometimes feel lonely.",
            min_friendship_level=2,
            min_age=8,
            max_age=14,
            tone="supportive",
            response_style="encouraging",
            expert_reviewed=True,
            context_tags=json.dumps(["homeschool", "social_isolation"])
        )

        assert template.category == "school"
        assert template.subcategory == "homeschool_stress"
        assert template.min_age == 8
        assert template.max_age == 14
        assert template.expert_reviewed is True
        assert template.tone == "supportive"
        assert template.response_style == "encouraging"

    def test_homeschool_template_keywords_are_valid(self):
        """Test that homeschool template keywords can be parsed"""
        template = AdviceTemplate(
            category="school",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool", "lonely", "no friends", "isolated"]),
            template="Test template"
        )

        keywords = template.get_keywords()
        assert isinstance(keywords, list)
        assert "homeschool" in keywords
        assert len(keywords) == 4

    def test_homeschool_template_context_tags_are_valid(self):
        """Test that homeschool template context tags can be parsed"""
        template = AdviceTemplate(
            category="school",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool"]),
            template="Test",
            context_tags=json.dumps(["homeschool", "social_isolation", "loneliness"])
        )

        tags = template.get_context_tags()
        assert isinstance(tags, list)
        assert "homeschool" in tags
        assert "social_isolation" in tags
        assert len(tags) == 3


class TestHomeschoolTemplateCategories:
    """Test different category assignments for homeschool templates"""

    def test_school_category_homeschool_template(self):
        """Test homeschool template with 'school' category"""
        template = AdviceTemplate(
            category="school",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool", "focus"]),
            template="Staying focused at home is hard, {name}!"
        )

        assert template.category == "school"
        assert template.subcategory == "homeschool_stress"

    def test_family_category_homeschool_template(self):
        """Test homeschool template with 'family' category"""
        template = AdviceTemplate(
            category="family",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool", "parent", "teacher"]),
            template="Having your parent as your teacher can be tricky, {name}."
        )

        assert template.category == "family"
        assert template.subcategory == "homeschool_stress"

    def test_emotional_category_homeschool_template(self):
        """Test homeschool template with 'emotional' category"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool", "miss", "regular school"]),
            template="It's totally okay to miss parts of traditional school, {name}."
        )

        assert template.category == "emotional"
        assert template.subcategory == "homeschool_stress"

    def test_social_category_homeschool_template(self):
        """Test homeschool template with 'social' category"""
        template = AdviceTemplate(
            category="social",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool", "different", "weird"]),
            template="When people ask about homeschooling and don't get it, {name}..."
        )

        assert template.category == "social"
        assert template.subcategory == "homeschool_stress"


class TestHomeschoolTemplateFormatting:
    """Test template formatting with placeholders"""

    def test_format_with_name_placeholder(self):
        """Test formatting template with name placeholder"""
        template = AdviceTemplate(
            category="school",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool"]),
            template="Hey {name}, being homeschooled can feel lonely sometimes."
        )

        formatted = template.format_advice(name="Alex")
        assert "Alex" in formatted
        assert "{name}" not in formatted

    def test_format_with_multiple_placeholders(self):
        """Test formatting template with multiple placeholders"""
        template = AdviceTemplate(
            category="school",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool"]),
            template="Hi {name}! Try joining {activity} to meet friends."
        )

        formatted = template.format_advice(name="Jordan", activity="sports teams")
        assert "Jordan" in formatted
        assert "sports teams" in formatted
        assert "{name}" not in formatted
        assert "{activity}" not in formatted


class TestHomeschoolTemplateAgeAppropriateness:
    """Test age appropriateness of homeschool templates"""

    def test_age_8_14_template(self):
        """Test template appropriate for ages 8-14"""
        template = AdviceTemplate(
            category="school",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool"]),
            template="Test",
            min_age=8,
            max_age=14
        )

        assert template.is_appropriate_for_age(8) is True
        assert template.is_appropriate_for_age(11) is True
        assert template.is_appropriate_for_age(14) is True
        assert template.is_appropriate_for_age(7) is False
        assert template.is_appropriate_for_age(15) is False

    def test_age_9_14_template(self):
        """Test template appropriate for ages 9-14"""
        template = AdviceTemplate(
            category="school",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool"]),
            template="Test",
            min_age=9,
            max_age=14
        )

        assert template.is_appropriate_for_age(8) is False
        assert template.is_appropriate_for_age(9) is True
        assert template.is_appropriate_for_age(14) is True

    def test_age_10_14_template(self):
        """Test template appropriate for ages 10-14"""
        template = AdviceTemplate(
            category="school",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool"]),
            template="Test",
            min_age=10,
            max_age=14
        )

        assert template.is_appropriate_for_age(9) is False
        assert template.is_appropriate_for_age(10) is True
        assert template.is_appropriate_for_age(14) is True


class TestHomeschoolTemplateFriendshipLevels:
    """Test friendship level requirements"""

    def test_friendship_level_2_template(self):
        """Test template available at friendship level 2+"""
        template = AdviceTemplate(
            category="school",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool"]),
            template="Test",
            min_friendship_level=2
        )

        assert template.is_available_at_friendship_level(1) is False
        assert template.is_available_at_friendship_level(2) is True
        assert template.is_available_at_friendship_level(5) is True

    def test_friendship_level_3_template(self):
        """Test template available at friendship level 3+"""
        template = AdviceTemplate(
            category="school",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool"]),
            template="Test",
            min_friendship_level=3
        )

        assert template.is_available_at_friendship_level(2) is False
        assert template.is_available_at_friendship_level(3) is True
        assert template.is_available_at_friendship_level(10) is True

    def test_friendship_level_4_template(self):
        """Test template available at friendship level 4+"""
        template = AdviceTemplate(
            category="school",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool"]),
            template="Test",
            min_friendship_level=4
        )

        assert template.is_available_at_friendship_level(3) is False
        assert template.is_available_at_friendship_level(4) is True
        assert template.is_available_at_friendship_level(10) is True


class TestHomeschoolTemplateTones:
    """Test template tone assignments"""

    def test_supportive_tone_template(self):
        """Test template with supportive tone"""
        template = AdviceTemplate(
            category="school",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool"]),
            template="Test",
            tone="supportive"
        )

        assert template.tone == "supportive"

    def test_practical_tone_template(self):
        """Test template with practical tone"""
        template = AdviceTemplate(
            category="school",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool"]),
            template="Test",
            tone="practical"
        )

        assert template.tone == "practical"

    def test_empathetic_tone_template(self):
        """Test template with empathetic tone"""
        template = AdviceTemplate(
            category="family",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool"]),
            template="Test",
            tone="empathetic"
        )

        assert template.tone == "empathetic"

    def test_encouraging_tone_template(self):
        """Test template with encouraging tone"""
        template = AdviceTemplate(
            category="social",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool"]),
            template="Test",
            tone="encouraging"
        )

        assert template.tone == "encouraging"


class TestHomeschoolTemplateResponseStyles:
    """Test template response style assignments"""

    def test_encouraging_response_style(self):
        """Test template with encouraging response style"""
        template = AdviceTemplate(
            category="school",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool"]),
            template="Test",
            response_style="encouraging"
        )

        assert template.response_style == "encouraging"

    def test_direct_response_style(self):
        """Test template with direct response style"""
        template = AdviceTemplate(
            category="school",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool"]),
            template="Test",
            response_style="direct"
        )

        assert template.response_style == "direct"

    def test_validating_response_style(self):
        """Test template with validating response style"""
        template = AdviceTemplate(
            category="family",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool"]),
            template="Test",
            response_style="validating"
        )

        assert template.response_style == "validating"

    def test_practical_response_style(self):
        """Test template with practical response style"""
        template = AdviceTemplate(
            category="school",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool"]),
            template="Test",
            response_style="practical"
        )

        assert template.response_style == "practical"


class TestHomeschoolTemplateUseCases:
    """Test real-world use cases for homeschool templates"""

    def test_social_isolation_template(self):
        """Test social isolation homeschool template"""
        template = AdviceTemplate(
            category="school",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool", "lonely", "no friends", "isolated"]),
            template="Hey {name}, I hear you - being homeschooled can sometimes feel lonely. But here's the good news: there are lots of ways to connect!",
            min_friendship_level=2,
            min_age=8,
            max_age=14,
            tone="supportive",
            response_style="encouraging",
            expert_reviewed=True
        )

        formatted = template.format_advice(name="Alex")
        assert "Alex" in formatted
        assert "lonely" in formatted
        assert template.is_appropriate_for_age(10) is True
        assert template.is_available_at_friendship_level(3) is True

    def test_self_motivation_template(self):
        """Test self-motivation homeschool template"""
        template = AdviceTemplate(
            category="school",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool", "focus", "distracted", "motivation"]),
            template="Staying focused at home is hard, {name} - even adults struggle with this!",
            min_friendship_level=3,
            min_age=8,
            max_age=14,
            tone="practical",
            response_style="direct",
            expert_reviewed=True
        )

        assert template.tone == "practical"
        assert template.response_style == "direct"
        assert template.is_available_at_friendship_level(3) is True

    def test_parent_as_teacher_template(self):
        """Test parent-as-teacher homeschool template"""
        template = AdviceTemplate(
            category="family",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool", "parent", "mom", "dad", "teacher", "frustrated"]),
            template="Having your parent as your teacher can be tricky sometimes, {name}.",
            min_friendship_level=4,
            min_age=8,
            max_age=14,
            tone="empathetic",
            response_style="validating",
            expert_reviewed=True
        )

        assert template.category == "family"
        assert template.tone == "empathetic"
        assert template.response_style == "validating"
        assert template.is_available_at_friendship_level(4) is True

    def test_missing_traditional_school_template(self):
        """Test missing traditional school template"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool", "miss", "regular school", "traditional school"]),
            template="It's totally okay to miss parts of traditional school, {name}.",
            min_friendship_level=3,
            min_age=8,
            max_age=14,
            tone="empathetic",
            response_style="validating",
            expert_reviewed=True
        )

        assert template.category == "emotional"
        assert template.tone == "empathetic"


class TestHomeschoolTemplateExpertReview:
    """Test expert review status"""

    def test_all_homeschool_templates_expert_reviewed(self):
        """Test that homeschool templates are marked as expert reviewed"""
        template = AdviceTemplate(
            category="school",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool"]),
            template="Test",
            expert_reviewed=True
        )

        assert template.expert_reviewed is True

    def test_query_expert_reviewed_homeschool_templates(self):
        """Test querying only expert-reviewed homeschool templates"""
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
            category="school"
        )

        assert mock_db.query.called


class TestHomeschoolTemplateToDictSerialization:
    """Test serialization of homeschool templates"""

    def test_to_dict_includes_subcategory(self):
        """Test that to_dict includes subcategory field"""
        template = AdviceTemplate(
            category="school",
            subcategory="homeschool_stress",
            keywords=json.dumps(["homeschool", "lonely"]),
            template="Hey {name}, being homeschooled can feel lonely.",
            min_friendship_level=2,
            min_age=8,
            max_age=14,
            tone="supportive",
            response_style="encouraging",
            expert_reviewed=True,
            context_tags=json.dumps(["homeschool", "social_isolation"])
        )

        result = template.to_dict()

        assert result["category"] == "school"
        assert result["subcategory"] == "homeschool_stress"
        assert isinstance(result["keywords"], list)
        assert isinstance(result["context_tags"], list)
        assert result["tone"] == "supportive"
        assert result["response_style"] == "encouraging"
        assert result["expert_reviewed"] is True
        assert result["min_age"] == 8
        assert result["max_age"] == 14
