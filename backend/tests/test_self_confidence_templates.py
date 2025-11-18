"""
Tests for Self Confidence Advice Templates
Verifies that self confidence templates are properly structured and functional
"""

import pytest
from unittest.mock import Mock
import json

from models.safety import AdviceTemplate


class TestSelfConfidenceTemplateStructure:
    """Test self confidence template structure and fields"""

    def test_self_confidence_templates_exist(self):
        """Test that self_confidence subcategory templates can be queried"""
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
            category="emotional",
            friendship_level=3,
            subcategory="self_confidence"
        )

        # Verify query was called
        assert mock_db.query.called

    def test_self_confidence_template_has_required_fields(self):
        """Test that self confidence templates have all required fields"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["not good at", "bad at", "I can't"]),
            template="Hey {name}, everyone is good at different things!",
            min_friendship_level=3,
            min_age=8,
            max_age=14,
            tone="encouraging",
            response_style="supportive",
            expert_reviewed=True,
            context_tags=json.dumps(["self_confidence", "self_doubt", "abilities"])
        )

        assert template.category == "emotional"
        assert template.subcategory == "self_confidence"
        assert template.min_age == 8
        assert template.max_age == 14
        assert template.expert_reviewed is True
        assert template.tone == "encouraging"
        assert template.response_style == "supportive"

    def test_self_confidence_template_keywords_are_valid(self):
        """Test that self confidence template keywords can be parsed"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["not good at", "bad at", "terrible", "awful"]),
            template="Test template"
        )

        keywords = template.get_keywords()
        assert isinstance(keywords, list)
        assert "not good at" in keywords
        assert len(keywords) == 4

    def test_self_confidence_template_context_tags_are_valid(self):
        """Test that self confidence template context tags can be parsed"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["not good at"]),
            template="Test",
            context_tags=json.dumps(["self_confidence", "self_doubt", "abilities", "growth_mindset"])
        )

        tags = template.get_context_tags()
        assert isinstance(tags, list)
        assert "self_confidence" in tags
        assert "growth_mindset" in tags
        assert len(tags) == 4


class TestSelfConfidenceTemplateScenarios:
    """Test different self confidence scenarios"""

    def test_general_self_doubt_template(self):
        """Test general self-doubt template"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["not good at", "bad at", "everyone else", "I can't"]),
            template="Hey {name}, everyone is good at different things!",
            min_friendship_level=3,
            min_age=8,
            max_age=14,
            tone="encouraging",
            response_style="supportive"
        )

        assert template.category == "emotional"
        assert template.subcategory == "self_confidence"
        assert template.min_friendship_level == 3
        assert template.tone == "encouraging"

    def test_comparing_to_others_template(self):
        """Test comparing to others template"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["compare", "better than me", "not as good"]),
            template="Comparing yourself to others is a tough habit, {name}.",
            min_friendship_level=4,
            min_age=8,
            max_age=14,
            tone="validating",
            response_style="encouraging"
        )

        assert template.min_friendship_level == 4
        assert template.tone == "validating"
        assert template.response_style == "encouraging"

    def test_body_image_template(self):
        """Test body image and appearance template"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["ugly", "look bad", "appearance", "body", "fat", "skinny"]),
            template="How you feel about your appearance is really personal, {name}.",
            min_friendship_level=5,
            min_age=9,
            max_age=14,
            tone="gentle",
            response_style="validating"
        )

        assert template.min_friendship_level == 5
        assert template.min_age == 9
        assert template.tone == "gentle"

    def test_academic_abilities_template(self):
        """Test academic abilities template"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["not smart", "dumb", "stupid", "bad at school"]),
            template="I hear you feeling down about school, {name}.",
            min_friendship_level=3,
            min_age=8,
            max_age=14,
            tone="encouraging",
            response_style="validating"
        )

        assert template.tone == "encouraging"
        assert template.response_style == "validating"

    def test_social_skills_fitting_in_template(self):
        """Test social skills and fitting in template"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["don't fit in", "weird", "awkward", "no friends"]),
            template="Feeling like you don't fit in is one of the hardest feelings, {name}.",
            min_friendship_level=4,
            min_age=9,
            max_age=14,
            tone="empathetic",
            response_style="validating"
        )

        assert template.min_age == 9
        assert template.tone == "empathetic"

    def test_fear_of_trying_new_things_template(self):
        """Test fear of trying new things template"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["scared to try", "embarrassed", "what if I fail"]),
            template="Being scared to try new things because you might fail or look silly is SO normal, {name}.",
            min_friendship_level=3,
            min_age=8,
            max_age=14,
            tone="encouraging",
            response_style="direct"
        )

        assert template.response_style == "direct"
        assert template.tone == "encouraging"

    def test_not_good_enough_template(self):
        """Test not being good enough template"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["not good enough", "never enough", "disappointing"]),
            template="That feeling of not being 'good enough' is really painful, {name}.",
            min_friendship_level=5,
            min_age=9,
            max_age=14,
            tone="gentle",
            response_style="validating"
        )

        assert template.min_friendship_level == 5
        assert template.tone == "gentle"

    def test_being_picked_last_template(self):
        """Test being picked last template"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["picked last", "nobody wants me", "not chosen"]),
            template="Being picked last really stings, {name}.",
            min_friendship_level=4,
            min_age=8,
            max_age=14,
            tone="empathetic",
            response_style="supportive"
        )

        assert template.min_friendship_level == 4
        assert template.tone == "empathetic"

    def test_learning_from_mistakes_template(self):
        """Test learning from mistakes template"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["made a mistake", "messed up", "did something wrong"]),
            template="Making mistakes feels terrible in the moment, {name}.",
            min_friendship_level=3,
            min_age=8,
            max_age=14,
            tone="supportive",
            response_style="encouraging"
        )

        assert template.tone == "supportive"
        assert template.response_style == "encouraging"

    def test_unique_interests_template(self):
        """Test unique interests template"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["different interests", "nobody likes", "weird hobby", "nerdy"]),
            template="Having different interests than other kids can make you feel alone, {name}.",
            min_friendship_level=4,
            min_age=9,
            max_age=14,
            tone="validating",
            response_style="encouraging"
        )

        assert template.min_age == 9
        assert template.tone == "validating"

    def test_standing_up_for_yourself_template(self):
        """Test standing up for yourself template"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["can't stand up", "scared to speak", "pushover"]),
            template="Learning to stand up for yourself takes practice and courage, {name}.",
            min_friendship_level=4,
            min_age=10,
            max_age=14,
            tone="encouraging",
            response_style="direct"
        )

        assert template.min_age == 10
        assert template.response_style == "direct"


class TestSelfConfidenceTemplateFormatting:
    """Test template formatting with placeholders"""

    def test_format_with_name_placeholder(self):
        """Test formatting template with name placeholder"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["not good at"]),
            template="Hey {name}, everyone is good at different things!"
        )

        formatted = template.format_advice(name="Taylor")
        assert "Taylor" in formatted
        assert "{name}" not in formatted

    def test_format_with_multiple_placeholders(self):
        """Test formatting template with multiple placeholders"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["compare"]),
            template="Hi {name}! Focus on {strength} instead of comparing."
        )

        formatted = template.format_advice(name="Alex", strength="your creativity")
        assert "Alex" in formatted
        assert "your creativity" in formatted
        assert "{name}" not in formatted
        assert "{strength}" not in formatted


class TestSelfConfidenceTemplateAgeAppropriateness:
    """Test age appropriateness of self confidence templates"""

    def test_age_8_14_template(self):
        """Test template appropriate for ages 8-14"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["not good at"]),
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
        """Test template appropriate for ages 9-14 (mature topics)"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["body image"]),
            template="Test",
            min_age=9,
            max_age=14
        )

        assert template.is_appropriate_for_age(8) is False
        assert template.is_appropriate_for_age(9) is True
        assert template.is_appropriate_for_age(14) is True

    def test_age_10_14_template(self):
        """Test template appropriate for ages 10-14 (complex topics)"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["assertiveness"]),
            template="Test",
            min_age=10,
            max_age=14
        )

        assert template.is_appropriate_for_age(9) is False
        assert template.is_appropriate_for_age(10) is True
        assert template.is_appropriate_for_age(14) is True


class TestSelfConfidenceTemplateFriendshipLevels:
    """Test friendship level requirements"""

    def test_friendship_level_3_template(self):
        """Test template available at friendship level 3+"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["not good at"]),
            template="Test",
            min_friendship_level=3
        )

        assert template.is_available_at_friendship_level(2) is False
        assert template.is_available_at_friendship_level(3) is True
        assert template.is_available_at_friendship_level(5) is True

    def test_friendship_level_4_template(self):
        """Test template available at friendship level 4+"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["compare"]),
            template="Test",
            min_friendship_level=4
        )

        assert template.is_available_at_friendship_level(3) is False
        assert template.is_available_at_friendship_level(4) is True
        assert template.is_available_at_friendship_level(10) is True

    def test_friendship_level_5_template(self):
        """Test template available at friendship level 5+"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["body image", "not good enough"]),
            template="Test",
            min_friendship_level=5
        )

        assert template.is_available_at_friendship_level(4) is False
        assert template.is_available_at_friendship_level(5) is True
        assert template.is_available_at_friendship_level(10) is True


class TestSelfConfidenceTemplateTones:
    """Test template tone assignments"""

    def test_encouraging_tone_template(self):
        """Test template with encouraging tone"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["not good at"]),
            template="Test",
            tone="encouraging"
        )

        assert template.tone == "encouraging"

    def test_validating_tone_template(self):
        """Test template with validating tone"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["compare"]),
            template="Test",
            tone="validating"
        )

        assert template.tone == "validating"

    def test_gentle_tone_template(self):
        """Test template with gentle tone"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["body image"]),
            template="Test",
            tone="gentle"
        )

        assert template.tone == "gentle"

    def test_empathetic_tone_template(self):
        """Test template with empathetic tone"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["picked last"]),
            template="Test",
            tone="empathetic"
        )

        assert template.tone == "empathetic"

    def test_supportive_tone_template(self):
        """Test template with supportive tone"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["mistakes"]),
            template="Test",
            tone="supportive"
        )

        assert template.tone == "supportive"


class TestSelfConfidenceTemplateResponseStyles:
    """Test template response style assignments"""

    def test_supportive_response_style(self):
        """Test template with supportive response style"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["not good at"]),
            template="Test",
            response_style="supportive"
        )

        assert template.response_style == "supportive"

    def test_encouraging_response_style(self):
        """Test template with encouraging response style"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["compare"]),
            template="Test",
            response_style="encouraging"
        )

        assert template.response_style == "encouraging"

    def test_validating_response_style(self):
        """Test template with validating response style"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["body image"]),
            template="Test",
            response_style="validating"
        )

        assert template.response_style == "validating"

    def test_direct_response_style(self):
        """Test template with direct response style"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["trying new things"]),
            template="Test",
            response_style="direct"
        )

        assert template.response_style == "direct"


class TestSelfConfidenceTemplateUseCases:
    """Test real-world use cases for self confidence templates"""

    def test_general_self_doubt_use_case(self):
        """Test general self-doubt template use case"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["not good at", "bad at", "everyone else", "I can't"]),
            template="Hey {name}, everyone is good at different things!",
            min_friendship_level=3,
            min_age=8,
            max_age=14,
            tone="encouraging",
            response_style="supportive",
            expert_reviewed=True
        )

        formatted = template.format_advice(name="Jordan")
        assert "Jordan" in formatted
        assert "everyone is good at different things" in formatted
        assert template.is_appropriate_for_age(10) is True
        assert template.is_available_at_friendship_level(3) is True

    def test_body_image_use_case(self):
        """Test body image template use case"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["ugly", "look bad", "appearance", "body"]),
            template="How you feel about your appearance is really personal, {name}.",
            min_friendship_level=5,
            min_age=9,
            max_age=14,
            tone="gentle",
            response_style="validating",
            expert_reviewed=True
        )

        assert template.min_friendship_level == 5
        assert template.min_age == 9
        assert template.tone == "gentle"
        assert template.is_available_at_friendship_level(5) is True

    def test_academic_abilities_use_case(self):
        """Test academic abilities template use case"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["not smart", "dumb", "stupid", "bad at school"]),
            template="I hear you feeling down about school, {name}.",
            min_friendship_level=3,
            min_age=8,
            max_age=14,
            tone="encouraging",
            response_style="validating",
            expert_reviewed=True
        )

        assert template.tone == "encouraging"
        assert template.response_style == "validating"
        assert template.is_appropriate_for_age(12) is True

    def test_standing_up_for_yourself_use_case(self):
        """Test standing up for yourself template use case"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["can't stand up", "scared to speak", "pushover"]),
            template="Learning to stand up for yourself takes practice and courage, {name}.",
            min_friendship_level=4,
            min_age=10,
            max_age=14,
            tone="encouraging",
            response_style="direct",
            expert_reviewed=True
        )

        assert template.min_age == 10
        assert template.is_appropriate_for_age(10) is True
        assert template.is_appropriate_for_age(9) is False


class TestSelfConfidenceTemplateExpertReview:
    """Test expert review status"""

    def test_all_self_confidence_templates_expert_reviewed(self):
        """Test that self confidence templates are marked as expert reviewed"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["not good at"]),
            template="Test",
            expert_reviewed=True
        )

        assert template.expert_reviewed is True

    def test_query_expert_reviewed_self_confidence_templates(self):
        """Test querying only expert-reviewed self confidence templates"""
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
            category="emotional"
        )

        assert mock_db.query.called


class TestSelfConfidenceTemplateToDictSerialization:
    """Test serialization of self confidence templates"""

    def test_to_dict_includes_subcategory(self):
        """Test that to_dict includes subcategory field"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["not good at", "bad at"]),
            template="Hey {name}, everyone is good at different things!",
            min_friendship_level=3,
            min_age=8,
            max_age=14,
            tone="encouraging",
            response_style="supportive",
            expert_reviewed=True,
            context_tags=json.dumps(["self_confidence", "self_doubt", "abilities"])
        )

        result = template.to_dict()

        assert result["category"] == "emotional"
        assert result["subcategory"] == "self_confidence"
        assert isinstance(result["keywords"], list)
        assert isinstance(result["context_tags"], list)
        assert result["tone"] == "encouraging"
        assert result["response_style"] == "supportive"
        assert result["expert_reviewed"] is True
        assert result["min_age"] == 8
        assert result["max_age"] == 14

    def test_to_dict_with_all_fields(self):
        """Test that to_dict includes all fields properly"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["compare", "better than me"]),
            template="Comparing yourself to others is a tough habit, {name}.",
            min_friendship_level=4,
            min_age=8,
            max_age=14,
            tone="validating",
            response_style="encouraging",
            expert_reviewed=True,
            context_tags=json.dumps(["self_confidence", "comparison", "self_worth"])
        )

        result = template.to_dict()

        assert result["min_friendship_level"] == 4
        assert result["min_age"] == 8
        assert result["max_age"] == 14
        assert "compare" in result["keywords"]
        assert "self_confidence" in result["context_tags"]


class TestSelfConfidenceTemplateContextMatching:
    """Test context-based template matching"""

    def test_body_image_keywords_match(self):
        """Test that body image keywords match appropriately"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["ugly", "look bad", "appearance", "body", "fat", "skinny"]),
            template="Test"
        )

        keywords = template.get_keywords()
        assert "ugly" in keywords
        assert "body" in keywords
        assert "appearance" in keywords

    def test_academic_keywords_match(self):
        """Test that academic keywords match appropriately"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["not smart", "dumb", "stupid", "bad at school"]),
            template="Test"
        )

        keywords = template.get_keywords()
        assert "not smart" in keywords
        assert "bad at school" in keywords

    def test_social_keywords_match(self):
        """Test that social keywords match appropriately"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="self_confidence",
            keywords=json.dumps(["don't fit in", "weird", "awkward", "no friends"]),
            template="Test"
        )

        keywords = template.get_keywords()
        assert "don't fit in" in keywords
        assert "weird" in keywords
        assert "no friends" in keywords
