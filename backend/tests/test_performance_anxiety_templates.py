"""
Tests for Performance Anxiety Advice Templates
Verifies that performance anxiety templates are properly structured and functional
"""

import pytest
from unittest.mock import Mock
import json

from models.safety import AdviceTemplate


class TestPerformanceAnxietyTemplateStructure:
    """Test performance anxiety template structure and fields"""

    def test_performance_anxiety_templates_exist(self):
        """Test that performance_anxiety subcategory templates can be queried"""
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
            subcategory="performance_anxiety"
        )

        # Verify query was called
        assert mock_db.query.called

    def test_performance_anxiety_template_has_required_fields(self):
        """Test that performance anxiety templates have all required fields"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["nervous", "scared", "presentation"]),
            template="Being nervous is normal, {name}.",
            min_friendship_level=2,
            min_age=8,
            max_age=14,
            tone="encouraging",
            response_style="supportive",
            expert_reviewed=True,
            context_tags=json.dumps(["anxiety", "performance"])
        )

        assert template.category == "emotional"
        assert template.subcategory == "performance_anxiety"
        assert template.min_age == 8
        assert template.max_age == 14
        assert template.expert_reviewed is True
        assert template.tone == "encouraging"
        assert template.response_style == "supportive"

    def test_performance_anxiety_template_keywords_are_valid(self):
        """Test that performance anxiety template keywords can be parsed"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["nervous", "anxious", "presentation", "test"]),
            template="Test template"
        )

        keywords = template.get_keywords()
        assert isinstance(keywords, list)
        assert "nervous" in keywords
        assert "anxious" in keywords
        assert len(keywords) == 4

    def test_performance_anxiety_template_context_tags_are_valid(self):
        """Test that performance anxiety template context tags can be parsed"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["nervous"]),
            template="Test",
            context_tags=json.dumps(["anxiety", "performance", "stress"])
        )

        tags = template.get_context_tags()
        assert isinstance(tags, list)
        assert "anxiety" in tags
        assert "performance" in tags
        assert len(tags) == 3


class TestPerformanceAnxietyScenarios:
    """Test different performance anxiety scenarios"""

    def test_presentations_public_speaking_template(self):
        """Test presentations and public speaking template"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["nervous", "presentation", "public speaking"]),
            template="Being nervous is normal, {name}.",
            min_friendship_level=2,
            min_age=8,
            max_age=14,
            tone="encouraging",
            response_style="supportive",
            expert_reviewed=True
        )

        assert template.subcategory == "performance_anxiety"
        assert template.is_available_at_friendship_level(2) is True
        assert template.is_appropriate_for_age(10) is True

    def test_test_anxiety_template(self):
        """Test test anxiety template"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["test", "exam", "quiz", "anxious"]),
            template="Test anxiety is common, {name}.",
            min_friendship_level=2,
            min_age=8,
            max_age=14,
            tone="supportive",
            response_style="practical",
            expert_reviewed=True
        )

        assert template.tone == "supportive"
        assert template.response_style == "practical"

    def test_sports_performance_template(self):
        """Test sports performance anxiety template"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["sports", "game", "match", "nervous"]),
            template="Feeling nervous before a game is normal, {name}.",
            min_friendship_level=3,
            min_age=8,
            max_age=14,
            tone="encouraging",
            response_style="direct",
            expert_reviewed=True
        )

        assert template.tone == "encouraging"
        assert template.response_style == "direct"

    def test_musical_artistic_performance_template(self):
        """Test musical/artistic performance template"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["recital", "concert", "stage fright"]),
            template="Stage fright is normal, {name}.",
            min_friendship_level=3,
            min_age=8,
            max_age=14,
            tone="encouraging",
            response_style="supportive",
            expert_reviewed=True
        )

        assert template.is_available_at_friendship_level(3) is True

    def test_tryouts_auditions_template(self):
        """Test tryouts and auditions template"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["tryout", "audition", "making the team"]),
            template="Tryouts can feel like pressure, {name}.",
            min_friendship_level=3,
            min_age=9,
            max_age=14,
            tone="encouraging",
            response_style="validating",
            expert_reviewed=True
        )

        assert template.is_appropriate_for_age(9) is True
        assert template.is_appropriate_for_age(8) is False

    def test_speaking_in_class_template(self):
        """Test speaking in class template"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["raise hand", "answer", "speaking", "class"]),
            template="Being nervous to speak up is common, {name}.",
            min_friendship_level=2,
            min_age=8,
            max_age=14,
            tone="encouraging",
            response_style="gentle",
            expert_reviewed=True
        )

        assert template.response_style == "gentle"

    def test_fear_of_failure_template(self):
        """Test fear of failure template"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["fail", "failure", "not good enough"]),
            template="Fear of failure is common, {name}.",
            min_friendship_level=4,
            min_age=9,
            max_age=14,
            tone="encouraging",
            response_style="validating",
            expert_reviewed=True
        )

        assert template.is_available_at_friendship_level(4) is True
        assert template.is_available_at_friendship_level(3) is False

    def test_perfectionism_template(self):
        """Test perfectionism template"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["perfect", "perfectionist", "mistake"]),
            template="Perfectionism can hold you back, {name}.",
            min_friendship_level=4,
            min_age=10,
            max_age=14,
            tone="empathetic",
            response_style="validating",
            expert_reviewed=True
        )

        assert template.tone == "empathetic"
        assert template.is_appropriate_for_age(10) is True
        assert template.is_appropriate_for_age(9) is False

    def test_competition_nerves_template(self):
        """Test competition nerves template"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["competition", "compete", "tournament"]),
            template="Competition nerves are normal, {name}.",
            min_friendship_level=3,
            min_age=9,
            max_age=14,
            tone="encouraging",
            response_style="direct",
            expert_reviewed=True
        )

        assert template.is_appropriate_for_age(12) is True

    def test_overthinking_template(self):
        """Test overthinking template"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["overthinking", "thinking too much", "what if"]),
            template="Overthinking makes things worse, {name}.",
            min_friendship_level=3,
            min_age=10,
            max_age=14,
            tone="practical",
            response_style="direct",
            expert_reviewed=True
        )

        assert template.tone == "practical"
        assert template.is_appropriate_for_age(10) is True


class TestPerformanceAnxietyTemplateFormatting:
    """Test template formatting with placeholders"""

    def test_format_with_name_placeholder(self):
        """Test formatting template with name placeholder"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["nervous"]),
            template="Being nervous is normal, {name}."
        )

        formatted = template.format_advice(name="Alex")
        assert "Alex" in formatted
        assert "{name}" not in formatted

    def test_format_with_multiple_placeholders(self):
        """Test formatting template with multiple placeholders"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["nervous"]),
            template="Hi {name}! Your {activity} performance will be great."
        )

        formatted = template.format_advice(name="Jordan", activity="music")
        assert "Jordan" in formatted
        assert "music" in formatted
        assert "{name}" not in formatted
        assert "{activity}" not in formatted


class TestPerformanceAnxietyAgeAppropriateness:
    """Test age appropriateness of performance anxiety templates"""

    def test_age_8_14_template(self):
        """Test template appropriate for ages 8-14"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["nervous"]),
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
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["nervous"]),
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
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["nervous"]),
            template="Test",
            min_age=10,
            max_age=14
        )

        assert template.is_appropriate_for_age(9) is False
        assert template.is_appropriate_for_age(10) is True
        assert template.is_appropriate_for_age(14) is True


class TestPerformanceAnxietyFriendshipLevels:
    """Test friendship level requirements"""

    def test_friendship_level_2_template(self):
        """Test template available at friendship level 2+"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["nervous"]),
            template="Test",
            min_friendship_level=2
        )

        assert template.is_available_at_friendship_level(1) is False
        assert template.is_available_at_friendship_level(2) is True
        assert template.is_available_at_friendship_level(5) is True

    def test_friendship_level_3_template(self):
        """Test template available at friendship level 3+"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["nervous"]),
            template="Test",
            min_friendship_level=3
        )

        assert template.is_available_at_friendship_level(2) is False
        assert template.is_available_at_friendship_level(3) is True
        assert template.is_available_at_friendship_level(10) is True

    def test_friendship_level_4_template(self):
        """Test template available at friendship level 4+"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["nervous"]),
            template="Test",
            min_friendship_level=4
        )

        assert template.is_available_at_friendship_level(3) is False
        assert template.is_available_at_friendship_level(4) is True
        assert template.is_available_at_friendship_level(10) is True


class TestPerformanceAnxietyTemplateTones:
    """Test template tone assignments"""

    def test_encouraging_tone_template(self):
        """Test template with encouraging tone"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["nervous"]),
            template="Test",
            tone="encouraging"
        )

        assert template.tone == "encouraging"

    def test_supportive_tone_template(self):
        """Test template with supportive tone"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["nervous"]),
            template="Test",
            tone="supportive"
        )

        assert template.tone == "supportive"

    def test_empathetic_tone_template(self):
        """Test template with empathetic tone"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["nervous"]),
            template="Test",
            tone="empathetic"
        )

        assert template.tone == "empathetic"

    def test_practical_tone_template(self):
        """Test template with practical tone"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["nervous"]),
            template="Test",
            tone="practical"
        )

        assert template.tone == "practical"


class TestPerformanceAnxietyTemplateResponseStyles:
    """Test template response style assignments"""

    def test_supportive_response_style(self):
        """Test template with supportive response style"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["nervous"]),
            template="Test",
            response_style="supportive"
        )

        assert template.response_style == "supportive"

    def test_practical_response_style(self):
        """Test template with practical response style"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["nervous"]),
            template="Test",
            response_style="practical"
        )

        assert template.response_style == "practical"

    def test_direct_response_style(self):
        """Test template with direct response style"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["nervous"]),
            template="Test",
            response_style="direct"
        )

        assert template.response_style == "direct"

    def test_validating_response_style(self):
        """Test template with validating response style"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["nervous"]),
            template="Test",
            response_style="validating"
        )

        assert template.response_style == "validating"

    def test_gentle_response_style(self):
        """Test template with gentle response style"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["nervous"]),
            template="Test",
            response_style="gentle"
        )

        assert template.response_style == "gentle"


class TestPerformanceAnxietyExpertReview:
    """Test expert review status"""

    def test_all_performance_anxiety_templates_expert_reviewed(self):
        """Test that performance anxiety templates are marked as expert reviewed"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["nervous"]),
            template="Test",
            expert_reviewed=True
        )

        assert template.expert_reviewed is True

    def test_query_expert_reviewed_performance_anxiety_templates(self):
        """Test querying only expert-reviewed performance anxiety templates"""
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


class TestPerformanceAnxietyToDictSerialization:
    """Test serialization of performance anxiety templates"""

    def test_to_dict_includes_subcategory(self):
        """Test that to_dict includes subcategory field"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["nervous", "presentation"]),
            template="Being nervous is normal, {name}.",
            min_friendship_level=2,
            min_age=8,
            max_age=14,
            tone="encouraging",
            response_style="supportive",
            expert_reviewed=True,
            context_tags=json.dumps(["anxiety", "performance"])
        )

        result = template.to_dict()

        assert result["category"] == "emotional"
        assert result["subcategory"] == "performance_anxiety"
        assert isinstance(result["keywords"], list)
        assert isinstance(result["context_tags"], list)
        assert result["tone"] == "encouraging"
        assert result["response_style"] == "supportive"
        assert result["expert_reviewed"] is True
        assert result["min_age"] == 8
        assert result["max_age"] == 14


class TestPerformanceAnxietyRealWorldScenarios:
    """Test real-world usage scenarios for performance anxiety templates"""

    def test_test_anxiety_scenario_with_personalization(self):
        """Test test anxiety scenario with name personalization"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["test", "exam", "anxious"]),
            template="Test anxiety is SO common, {name}. Your brain is trying to protect you!",
            min_friendship_level=2,
            min_age=8,
            max_age=14,
            tone="supportive",
            response_style="practical",
            expert_reviewed=True
        )

        formatted = template.format_advice(name="Jordan")
        assert "Jordan" in formatted
        assert "protect" in formatted
        assert template.is_available_at_friendship_level(3) is True

    def test_perfectionism_requires_higher_friendship(self):
        """Test that perfectionism templates require higher friendship level"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["perfect", "perfectionist"]),
            template="Perfectionism can hold you back, {name}.",
            min_friendship_level=4,
            min_age=10,
            max_age=14,
            tone="empathetic",
            response_style="validating",
            expert_reviewed=True
        )

        # Should require friendship level 4
        assert template.is_available_at_friendship_level(3) is False
        assert template.is_available_at_friendship_level(4) is True

    def test_overthinking_requires_maturity(self):
        """Test that overthinking template requires older age"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["overthinking", "what if"]),
            template="When you're overthinking, {name}...",
            min_friendship_level=3,
            min_age=10,
            max_age=14,
            tone="practical",
            response_style="direct",
            expert_reviewed=True
        )

        # Should require age 10+
        assert template.is_appropriate_for_age(9) is False
        assert template.is_appropriate_for_age(10) is True

    def test_sports_performance_practical_advice(self):
        """Test sports performance template has practical content"""
        template = AdviceTemplate(
            category="emotional",
            subcategory="performance_anxiety",
            keywords=json.dumps(["sports", "game", "nervous"]),
            template="Feeling nervous before a game is your body getting ready, {name}! Channel that energy: visualize success, focus on preparation.",
            min_friendship_level=3,
            min_age=8,
            max_age=14,
            tone="encouraging",
            response_style="direct",
            expert_reviewed=True
        )

        formatted = template.format_advice(name="Alex")
        assert "Alex" in formatted
        assert "visualize" in formatted or "preparation" in formatted
