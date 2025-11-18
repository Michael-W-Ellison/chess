"""
Tests for Family Issues Advice Templates
Verifies that family issues templates are properly structured and functional
"""

import pytest
from unittest.mock import Mock
import json

from models.safety import AdviceTemplate


class TestFamilyIssuesTemplateStructure:
    """Test family issues template structure and fields"""

    def test_family_issues_templates_exist(self):
        """Test that family_issues subcategory templates can be queried"""
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
            category="family",
            friendship_level=4,
            subcategory="family_issues"
        )

        # Verify query was called
        assert mock_db.query.called

    def test_family_issues_template_has_required_fields(self):
        """Test that family issues templates have all required fields"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["siblings", "fighting", "arguing"]),
            template="Hey {name}, sibling fights are super common - you're not alone in this!",
            min_friendship_level=3,
            min_age=8,
            max_age=14,
            tone="empathetic",
            response_style="supportive",
            expert_reviewed=True,
            context_tags=json.dumps(["family", "siblings", "conflict"])
        )

        assert template.category == "family"
        assert template.subcategory == "family_issues"
        assert template.min_age == 8
        assert template.max_age == 14
        assert template.expert_reviewed is True
        assert template.tone == "empathetic"
        assert template.response_style == "supportive"

    def test_family_issues_template_keywords_are_valid(self):
        """Test that family issues template keywords can be parsed"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["siblings", "fighting", "arguing", "annoying"]),
            template="Test template"
        )

        keywords = template.get_keywords()
        assert isinstance(keywords, list)
        assert "siblings" in keywords
        assert len(keywords) == 4

    def test_family_issues_template_context_tags_are_valid(self):
        """Test that family issues template context tags can be parsed"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["siblings"]),
            template="Test",
            context_tags=json.dumps(["family", "siblings", "conflict", "rivalry"])
        )

        tags = template.get_context_tags()
        assert isinstance(tags, list)
        assert "family" in tags
        assert "siblings" in tags
        assert len(tags) == 4


class TestFamilyIssuesTemplateScenarios:
    """Test different family issue scenarios"""

    def test_general_family_conflict_template(self):
        """Test general family conflict template"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["family", "conflict", "fighting", "arguing", "tension"]),
            template="Family conflict is really hard, {name}.",
            min_friendship_level=4,
            min_age=8,
            max_age=14,
            tone="empathetic",
            response_style="gentle"
        )

        assert template.category == "family"
        assert template.subcategory == "family_issues"
        assert template.min_friendship_level == 4
        assert template.tone == "empathetic"

    def test_sibling_rivalry_template(self):
        """Test sibling rivalry template"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["siblings", "fighting", "arguing", "annoying"]),
            template="Hey {name}, sibling fights are super common!",
            min_friendship_level=3,
            min_age=8,
            max_age=14,
            tone="empathetic",
            response_style="supportive"
        )

        assert template.subcategory == "family_issues"
        assert template.min_friendship_level == 3
        assert template.is_appropriate_for_age(10)

    def test_parents_fighting_template(self):
        """Test parents fighting template"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["parents", "fighting", "arguing", "yelling", "scared"]),
            template="When parents fight, it can be really scary, {name}.",
            min_friendship_level=5,
            min_age=8,
            max_age=14,
            tone="gentle",
            response_style="validating"
        )

        assert template.min_friendship_level == 5
        assert template.tone == "gentle"
        assert template.response_style == "validating"

    def test_feeling_misunderstood_template(self):
        """Test feeling misunderstood by family template"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["misunderstood", "don't understand", "don't get me", "listen"]),
            template="Feeling like your family doesn't understand you is tough, {name}.",
            min_friendship_level=4,
            min_age=9,
            max_age=14,
            tone="empathetic",
            response_style="validating"
        )

        assert template.min_age == 9
        assert template.is_appropriate_for_age(9)
        assert template.is_appropriate_for_age(8) is False

    def test_unfair_rules_template(self):
        """Test unfair rules template"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["unfair", "rules", "strict", "not fair"]),
            template="When rules feel unfair, it's really frustrating, {name}.",
            min_friendship_level=3,
            min_age=9,
            max_age=14,
            tone="validating",
            response_style="practical"
        )

        assert template.tone == "validating"
        assert template.response_style == "practical"

    def test_divorce_separation_template(self):
        """Test divorce and separation template"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["divorce", "separation", "splitting up", "breaking up"]),
            template="I'm really sorry you're going through this, {name}.",
            min_friendship_level=5,
            min_age=9,
            max_age=14,
            tone="gentle",
            response_style="supportive"
        )

        assert template.min_friendship_level == 5
        assert template.min_age == 9
        assert template.tone == "gentle"

    def test_blended_families_template(self):
        """Test blended families template"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["stepparent", "step-parent", "blended family", "new family"]),
            template="Adjusting to a blended family takes time, {name}.",
            min_friendship_level=5,
            min_age=9,
            max_age=14,
            tone="empathetic",
            response_style="validating"
        )

        assert template.subcategory == "family_issues"
        assert template.min_friendship_level == 5

    def test_parent_expectations_template(self):
        """Test parent expectations and pressure template"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["pressure", "expectations", "grades", "perfect", "disappoint"]),
            template="Feeling pressure from your parents is really hard, {name}.",
            min_friendship_level=4,
            min_age=10,
            max_age=14,
            tone="empathetic",
            response_style="validating"
        )

        assert template.min_age == 10
        assert template.is_appropriate_for_age(10)
        assert template.is_appropriate_for_age(9) is False

    def test_cant_talk_to_parents_template(self):
        """Test can't talk to parents template"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["can't talk", "won't listen", "don't care", "busy"]),
            template="When it feels like you can't talk to your parents, that's really isolating, {name}.",
            min_friendship_level=5,
            min_age=9,
            max_age=14,
            tone="empathetic",
            response_style="supportive"
        )

        assert template.min_friendship_level == 5
        assert template.tone == "empathetic"

    def test_comparing_to_siblings_template(self):
        """Test comparing to siblings template"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["favorite", "compare", "better", "sibling", "unfair"]),
            template="Being compared to your siblings hurts, {name}.",
            min_friendship_level=5,
            min_age=9,
            max_age=14,
            tone="validating",
            response_style="empathetic"
        )

        assert template.min_friendship_level == 5
        assert template.response_style == "empathetic"

    def test_privacy_boundaries_template(self):
        """Test privacy and boundaries template"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["privacy", "room", "space", "boundaries", "respect"]),
            template="Wanting privacy doesn't mean you're hiding something, {name}.",
            min_friendship_level=4,
            min_age=10,
            max_age=14,
            tone="supportive",
            response_style="direct"
        )

        assert template.min_age == 10
        assert template.response_style == "direct"


class TestFamilyIssuesTemplateFormatting:
    """Test template formatting with placeholders"""

    def test_format_with_name_placeholder(self):
        """Test formatting template with name placeholder"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["siblings", "fighting"]),
            template="Hey {name}, sibling fights are super common - you're not alone in this!"
        )

        formatted = template.format_advice(name="Jordan")
        assert "Jordan" in formatted
        assert "{name}" not in formatted

    def test_format_with_multiple_placeholders(self):
        """Test formatting template with multiple placeholders"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["siblings"]),
            template="Hi {name}! Talk to {sibling_name} when you're both calm."
        )

        formatted = template.format_advice(name="Alex", sibling_name="Sam")
        assert "Alex" in formatted
        assert "Sam" in formatted
        assert "{name}" not in formatted
        assert "{sibling_name}" not in formatted


class TestFamilyIssuesTemplateAgeAppropriateness:
    """Test age appropriateness of family issues templates"""

    def test_age_8_14_template(self):
        """Test template appropriate for ages 8-14"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["siblings"]),
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
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["divorce"]),
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
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["expectations", "pressure"]),
            template="Test",
            min_age=10,
            max_age=14
        )

        assert template.is_appropriate_for_age(9) is False
        assert template.is_appropriate_for_age(10) is True
        assert template.is_appropriate_for_age(14) is True


class TestFamilyIssuesTemplateFriendshipLevels:
    """Test friendship level requirements"""

    def test_friendship_level_3_template(self):
        """Test template available at friendship level 3+ (less sensitive)"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["siblings", "rules"]),
            template="Test",
            min_friendship_level=3
        )

        assert template.is_available_at_friendship_level(2) is False
        assert template.is_available_at_friendship_level(3) is True
        assert template.is_available_at_friendship_level(5) is True

    def test_friendship_level_4_template(self):
        """Test template available at friendship level 4+ (moderately sensitive)"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["conflict", "misunderstood"]),
            template="Test",
            min_friendship_level=4
        )

        assert template.is_available_at_friendship_level(3) is False
        assert template.is_available_at_friendship_level(4) is True
        assert template.is_available_at_friendship_level(10) is True

    def test_friendship_level_5_template(self):
        """Test template available at friendship level 5+ (very sensitive)"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["divorce", "parents fighting", "favoritism"]),
            template="Test",
            min_friendship_level=5
        )

        assert template.is_available_at_friendship_level(4) is False
        assert template.is_available_at_friendship_level(5) is True
        assert template.is_available_at_friendship_level(10) is True


class TestFamilyIssuesTemplateTones:
    """Test template tone assignments"""

    def test_empathetic_tone_template(self):
        """Test template with empathetic tone"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["family"]),
            template="Test",
            tone="empathetic"
        )

        assert template.tone == "empathetic"

    def test_gentle_tone_template(self):
        """Test template with gentle tone"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["parents fighting"]),
            template="Test",
            tone="gentle"
        )

        assert template.tone == "gentle"

    def test_validating_tone_template(self):
        """Test template with validating tone"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["unfair"]),
            template="Test",
            tone="validating"
        )

        assert template.tone == "validating"

    def test_supportive_tone_template(self):
        """Test template with supportive tone"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["privacy"]),
            template="Test",
            tone="supportive"
        )

        assert template.tone == "supportive"


class TestFamilyIssuesTemplateResponseStyles:
    """Test template response style assignments"""

    def test_gentle_response_style(self):
        """Test template with gentle response style"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["conflict"]),
            template="Test",
            response_style="gentle"
        )

        assert template.response_style == "gentle"

    def test_supportive_response_style(self):
        """Test template with supportive response style"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["siblings"]),
            template="Test",
            response_style="supportive"
        )

        assert template.response_style == "supportive"

    def test_validating_response_style(self):
        """Test template with validating response style"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["misunderstood"]),
            template="Test",
            response_style="validating"
        )

        assert template.response_style == "validating"

    def test_practical_response_style(self):
        """Test template with practical response style"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["rules"]),
            template="Test",
            response_style="practical"
        )

        assert template.response_style == "practical"

    def test_direct_response_style(self):
        """Test template with direct response style"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["privacy"]),
            template="Test",
            response_style="direct"
        )

        assert template.response_style == "direct"

    def test_empathetic_response_style(self):
        """Test template with empathetic response style"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["favoritism"]),
            template="Test",
            response_style="empathetic"
        )

        assert template.response_style == "empathetic"


class TestFamilyIssuesTemplateUseCases:
    """Test real-world use cases for family issues templates"""

    def test_sibling_rivalry_use_case(self):
        """Test sibling rivalry template use case"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["siblings", "fighting", "arguing", "annoying", "brother", "sister"]),
            template="Hey {name}, sibling fights are super common - you're not alone in this!",
            min_friendship_level=3,
            min_age=8,
            max_age=14,
            tone="empathetic",
            response_style="supportive",
            expert_reviewed=True
        )

        formatted = template.format_advice(name="Taylor")
        assert "Taylor" in formatted
        assert "sibling fights" in formatted
        assert template.is_appropriate_for_age(10) is True
        assert template.is_available_at_friendship_level(3) is True

    def test_parents_fighting_use_case(self):
        """Test parents fighting template use case"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["parents", "fighting", "arguing", "yelling", "scared", "worried"]),
            template="When parents fight, it can be really scary, {name}.",
            min_friendship_level=5,
            min_age=8,
            max_age=14,
            tone="gentle",
            response_style="validating",
            expert_reviewed=True
        )

        assert template.min_friendship_level == 5
        assert template.tone == "gentle"
        assert template.response_style == "validating"
        assert template.is_available_at_friendship_level(5) is True

    def test_divorce_use_case(self):
        """Test divorce template use case"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["divorce", "separation", "splitting up", "breaking up", "moving out"]),
            template="I'm really sorry you're going through this, {name}.",
            min_friendship_level=5,
            min_age=9,
            max_age=14,
            tone="gentle",
            response_style="supportive",
            expert_reviewed=True
        )

        assert template.min_age == 9
        assert template.min_friendship_level == 5
        assert template.tone == "gentle"

    def test_parent_pressure_use_case(self):
        """Test parent pressure template use case"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["pressure", "expectations", "grades", "perfect", "disappoint", "live up to"]),
            template="Feeling pressure from your parents is really hard, {name}.",
            min_friendship_level=4,
            min_age=10,
            max_age=14,
            tone="empathetic",
            response_style="validating",
            expert_reviewed=True
        )

        assert template.min_age == 10
        assert template.is_appropriate_for_age(10) is True
        assert template.is_appropriate_for_age(9) is False


class TestFamilyIssuesTemplateExpertReview:
    """Test expert review status"""

    def test_all_family_issues_templates_expert_reviewed(self):
        """Test that family issues templates are marked as expert reviewed"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["siblings"]),
            template="Test",
            expert_reviewed=True
        )

        assert template.expert_reviewed is True

    def test_query_expert_reviewed_family_issues_templates(self):
        """Test querying only expert-reviewed family issues templates"""
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
            category="family"
        )

        assert mock_db.query.called


class TestFamilyIssuesTemplateToDictSerialization:
    """Test serialization of family issues templates"""

    def test_to_dict_includes_subcategory(self):
        """Test that to_dict includes subcategory field"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["siblings", "fighting", "arguing"]),
            template="Hey {name}, sibling fights are super common!",
            min_friendship_level=3,
            min_age=8,
            max_age=14,
            tone="empathetic",
            response_style="supportive",
            expert_reviewed=True,
            context_tags=json.dumps(["family", "siblings", "conflict", "rivalry"])
        )

        result = template.to_dict()

        assert result["category"] == "family"
        assert result["subcategory"] == "family_issues"
        assert isinstance(result["keywords"], list)
        assert isinstance(result["context_tags"], list)
        assert result["tone"] == "empathetic"
        assert result["response_style"] == "supportive"
        assert result["expert_reviewed"] is True
        assert result["min_age"] == 8
        assert result["max_age"] == 14

    def test_to_dict_with_all_fields(self):
        """Test that to_dict includes all fields properly"""
        template = AdviceTemplate(
            category="family",
            subcategory="family_issues",
            keywords=json.dumps(["divorce", "separation"]),
            template="I'm really sorry you're going through this, {name}.",
            min_friendship_level=5,
            min_age=9,
            max_age=14,
            tone="gentle",
            response_style="supportive",
            expert_reviewed=True,
            context_tags=json.dumps(["family", "divorce", "separation", "change"])
        )

        result = template.to_dict()

        assert result["min_friendship_level"] == 5
        assert result["min_age"] == 9
        assert result["max_age"] == 14
        assert "divorce" in result["keywords"]
        assert "family" in result["context_tags"]
