"""
Tests for Friend Conflict Advice Templates
Verifies that friend conflict templates are properly structured and functional
"""

import pytest
from unittest.mock import Mock
import json

from models.safety import AdviceTemplate


class TestFriendConflictTemplateStructure:
    """Test friend conflict template structure and fields"""

    def test_friend_conflict_templates_exist(self):
        """Test that friend_conflict subcategory templates can be queried"""
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
            category="friendship",
            friendship_level=3,
            subcategory="friend_conflict"
        )

        # Verify query was called
        assert mock_db.query.called

    def test_friend_conflict_template_has_required_fields(self):
        """Test that friend conflict templates have all required fields"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend", "argument", "fight"]),
            template="Friend arguments are tough, {name}.",
            min_friendship_level=3,
            min_age=8,
            max_age=14,
            tone="empathetic",
            response_style="validating",
            expert_reviewed=True,
            context_tags=json.dumps(["friendship", "conflict"])
        )

        assert template.category == "friendship"
        assert template.subcategory == "friend_conflict"
        assert template.min_age == 8
        assert template.max_age == 14
        assert template.expert_reviewed is True
        assert template.tone == "empathetic"
        assert template.response_style == "validating"

    def test_friend_conflict_template_keywords_are_valid(self):
        """Test that friend conflict template keywords can be parsed"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend", "argument", "fight", "mad at me"]),
            template="Test template"
        )

        keywords = template.get_keywords()
        assert isinstance(keywords, list)
        assert "friend" in keywords
        assert "argument" in keywords
        assert len(keywords) == 4

    def test_friend_conflict_template_context_tags_are_valid(self):
        """Test that friend conflict template context tags can be parsed"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend"]),
            template="Test",
            context_tags=json.dumps(["friendship", "conflict", "communication"])
        )

        tags = template.get_context_tags()
        assert isinstance(tags, list)
        assert "friendship" in tags
        assert "conflict" in tags
        assert len(tags) == 3


class TestFriendConflictScenarios:
    """Test different friend conflict scenarios"""

    def test_arguments_and_fights_template(self):
        """Test arguments and fights template"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend", "argument", "fight", "mad at me"]),
            template="Friend arguments are really tough, {name}.",
            min_friendship_level=3,
            min_age=8,
            max_age=14,
            tone="empathetic",
            response_style="validating",
            expert_reviewed=True
        )

        assert template.subcategory == "friend_conflict"
        assert template.is_available_at_friendship_level(3) is True
        assert template.is_appropriate_for_age(10) is True

    def test_being_excluded_template(self):
        """Test being excluded template"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["left out", "excluded", "ignored"]),
            template="Feeling left out really stings, {name}.",
            min_friendship_level=4,
            min_age=8,
            max_age=14,
            tone="empathetic",
            response_style="supportive",
            expert_reviewed=True
        )

        assert template.is_available_at_friendship_level(4) is True
        assert template.tone == "empathetic"

    def test_betrayal_and_gossip_template(self):
        """Test betrayal and gossip template"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend", "told", "secret", "gossip", "betrayed"]),
            template="Having a friend share your secret really hurts, {name}.",
            min_friendship_level=5,
            min_age=9,
            max_age=14,
            tone="empathetic",
            response_style="validating",
            expert_reviewed=True
        )

        assert template.is_available_at_friendship_level(5) is True
        assert template.is_appropriate_for_age(9) is True
        assert template.is_appropriate_for_age(8) is False

    def test_jealousy_template(self):
        """Test jealousy template"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["jealous", "envy", "friend", "other friends"]),
            template="Jealousy in friendships is normal, {name}.",
            min_friendship_level=4,
            min_age=9,
            max_age=14,
            tone="empathetic",
            response_style="gentle",
            expert_reviewed=True
        )

        assert template.tone == "empathetic"
        assert template.response_style == "gentle"

    def test_making_new_friends_template(self):
        """Test making new friends template"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend", "new friend", "replacing"]),
            template="When your friend makes new friends, it can feel scary, {name}.",
            min_friendship_level=3,
            min_age=8,
            max_age=14,
            tone="supportive",
            response_style="encouraging",
            expert_reviewed=True
        )

        assert template.tone == "supportive"
        assert template.response_style == "encouraging"

    def test_apologizing_template(self):
        """Test apologizing template"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["sorry", "apologize", "my fault", "I messed up"]),
            template="It takes courage to apologize, {name}.",
            min_friendship_level=3,
            min_age=8,
            max_age=14,
            tone="encouraging",
            response_style="direct",
            expert_reviewed=True
        )

        assert template.tone == "encouraging"
        assert template.response_style == "direct"

    def test_forgiving_template(self):
        """Test forgiving template"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["forgive", "friend hurt me", "should I forgive"]),
            template="Forgiveness is tricky, {name}.",
            min_friendship_level=5,
            min_age=9,
            max_age=14,
            tone="empathetic",
            response_style="questioning",
            expert_reviewed=True
        )

        assert template.response_style == "questioning"
        assert template.is_available_at_friendship_level(5) is True

    def test_peer_pressure_template(self):
        """Test peer pressure from friends template"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend", "pressure", "make me", "want me to"]),
            template="Real friends don't pressure you, {name}.",
            min_friendship_level=4,
            min_age=9,
            max_age=14,
            tone="supportive",
            response_style="direct",
            expert_reviewed=True
        )

        assert template.tone == "supportive"
        assert template.response_style == "direct"

    def test_friend_moving_away_template(self):
        """Test friend moving away template"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend", "moving", "moving away", "leaving"]),
            template="Having a friend move away is hard, {name}.",
            min_friendship_level=4,
            min_age=8,
            max_age=14,
            tone="empathetic",
            response_style="supportive",
            expert_reviewed=True
        )

        assert template.tone == "empathetic"
        assert template.is_appropriate_for_age(10) is True

    def test_growing_apart_template(self):
        """Test growing apart template"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend", "different", "changed", "growing apart"]),
            template="Sometimes friendships change, {name}.",
            min_friendship_level=5,
            min_age=10,
            max_age=14,
            tone="empathetic",
            response_style="validating",
            expert_reviewed=True
        )

        assert template.is_appropriate_for_age(10) is True
        assert template.is_appropriate_for_age(9) is False

    def test_one_sided_friendship_template(self):
        """Test one-sided friendship template"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend", "one-sided", "always me", "effort"]),
            template="It's exhausting when you're always the one reaching out, {name}.",
            min_friendship_level=4,
            min_age=10,
            max_age=14,
            tone="validating",
            response_style="direct",
            expert_reviewed=True
        )

        assert template.tone == "validating"
        assert template.is_appropriate_for_age(12) is True


class TestFriendConflictTemplateFormatting:
    """Test template formatting with placeholders"""

    def test_format_with_name_placeholder(self):
        """Test formatting template with name placeholder"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend"]),
            template="Friend arguments are tough, {name}."
        )

        formatted = template.format_advice(name="Alex")
        assert "Alex" in formatted
        assert "{name}" not in formatted

    def test_format_with_multiple_placeholders(self):
        """Test formatting template with multiple placeholders"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend"]),
            template="Hi {name}! Talk to {friend_name} about your feelings."
        )

        formatted = template.format_advice(name="Jordan", friend_name="Sam")
        assert "Jordan" in formatted
        assert "Sam" in formatted
        assert "{name}" not in formatted
        assert "{friend_name}" not in formatted


class TestFriendConflictAgeAppropriateness:
    """Test age appropriateness of friend conflict templates"""

    def test_age_8_14_template(self):
        """Test template appropriate for ages 8-14"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend"]),
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
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend"]),
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
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend"]),
            template="Test",
            min_age=10,
            max_age=14
        )

        assert template.is_appropriate_for_age(9) is False
        assert template.is_appropriate_for_age(10) is True
        assert template.is_appropriate_for_age(14) is True


class TestFriendConflictFriendshipLevels:
    """Test friendship level requirements"""

    def test_friendship_level_3_template(self):
        """Test template available at friendship level 3+"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend"]),
            template="Test",
            min_friendship_level=3
        )

        assert template.is_available_at_friendship_level(2) is False
        assert template.is_available_at_friendship_level(3) is True
        assert template.is_available_at_friendship_level(5) is True

    def test_friendship_level_4_template(self):
        """Test template available at friendship level 4+"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend"]),
            template="Test",
            min_friendship_level=4
        )

        assert template.is_available_at_friendship_level(3) is False
        assert template.is_available_at_friendship_level(4) is True
        assert template.is_available_at_friendship_level(10) is True

    def test_friendship_level_5_template(self):
        """Test template available at friendship level 5+"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend"]),
            template="Test",
            min_friendship_level=5
        )

        assert template.is_available_at_friendship_level(4) is False
        assert template.is_available_at_friendship_level(5) is True
        assert template.is_available_at_friendship_level(10) is True


class TestFriendConflictTemplateTones:
    """Test template tone assignments"""

    def test_empathetic_tone_template(self):
        """Test template with empathetic tone"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend"]),
            template="Test",
            tone="empathetic"
        )

        assert template.tone == "empathetic"

    def test_supportive_tone_template(self):
        """Test template with supportive tone"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend"]),
            template="Test",
            tone="supportive"
        )

        assert template.tone == "supportive"

    def test_encouraging_tone_template(self):
        """Test template with encouraging tone"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend"]),
            template="Test",
            tone="encouraging"
        )

        assert template.tone == "encouraging"

    def test_validating_tone_template(self):
        """Test template with validating tone"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend"]),
            template="Test",
            tone="validating"
        )

        assert template.tone == "validating"


class TestFriendConflictTemplateResponseStyles:
    """Test template response style assignments"""

    def test_validating_response_style(self):
        """Test template with validating response style"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend"]),
            template="Test",
            response_style="validating"
        )

        assert template.response_style == "validating"

    def test_supportive_response_style(self):
        """Test template with supportive response style"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend"]),
            template="Test",
            response_style="supportive"
        )

        assert template.response_style == "supportive"

    def test_gentle_response_style(self):
        """Test template with gentle response style"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend"]),
            template="Test",
            response_style="gentle"
        )

        assert template.response_style == "gentle"

    def test_encouraging_response_style(self):
        """Test template with encouraging response style"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend"]),
            template="Test",
            response_style="encouraging"
        )

        assert template.response_style == "encouraging"

    def test_direct_response_style(self):
        """Test template with direct response style"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend"]),
            template="Test",
            response_style="direct"
        )

        assert template.response_style == "direct"

    def test_questioning_response_style(self):
        """Test template with questioning response style"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend"]),
            template="Test",
            response_style="questioning"
        )

        assert template.response_style == "questioning"


class TestFriendConflictExpertReview:
    """Test expert review status"""

    def test_all_friend_conflict_templates_expert_reviewed(self):
        """Test that friend conflict templates are marked as expert reviewed"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend"]),
            template="Test",
            expert_reviewed=True
        )

        assert template.expert_reviewed is True

    def test_query_expert_reviewed_friend_conflict_templates(self):
        """Test querying only expert-reviewed friend conflict templates"""
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

        assert mock_db.query.called


class TestFriendConflictToDictSerialization:
    """Test serialization of friend conflict templates"""

    def test_to_dict_includes_subcategory(self):
        """Test that to_dict includes subcategory field"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend", "argument"]),
            template="Friend arguments are tough, {name}.",
            min_friendship_level=3,
            min_age=8,
            max_age=14,
            tone="empathetic",
            response_style="validating",
            expert_reviewed=True,
            context_tags=json.dumps(["friendship", "conflict"])
        )

        result = template.to_dict()

        assert result["category"] == "friendship"
        assert result["subcategory"] == "friend_conflict"
        assert isinstance(result["keywords"], list)
        assert isinstance(result["context_tags"], list)
        assert result["tone"] == "empathetic"
        assert result["response_style"] == "validating"
        assert result["expert_reviewed"] is True
        assert result["min_age"] == 8
        assert result["max_age"] == 14


class TestFriendConflictRealWorldScenarios:
    """Test real-world usage scenarios for friend conflict templates"""

    def test_argument_scenario_with_personalization(self):
        """Test argument scenario with name personalization"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["friend", "argument", "fight"]),
            template="Friend arguments are really tough, {name}. Here's something that might help: try to see it from their perspective too.",
            min_friendship_level=3,
            min_age=8,
            max_age=14,
            tone="empathetic",
            response_style="validating",
            expert_reviewed=True
        )

        formatted = template.format_advice(name="Jordan")
        assert "Jordan" in formatted
        assert "perspective" in formatted
        assert template.is_available_at_friendship_level(4) is True

    def test_betrayal_scenario_requires_higher_friendship(self):
        """Test that betrayal templates require higher friendship level"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["betrayed", "secret", "gossip"]),
            template="Having a friend share your secret really hurts, {name}.",
            min_friendship_level=5,
            min_age=9,
            max_age=14,
            tone="empathetic",
            response_style="validating",
            expert_reviewed=True
        )

        # Should require friendship level 5
        assert template.is_available_at_friendship_level(4) is False
        assert template.is_available_at_friendship_level(5) is True

    def test_growing_apart_requires_maturity(self):
        """Test that growing apart template requires older age"""
        template = AdviceTemplate(
            category="friendship",
            subcategory="friend_conflict",
            keywords=json.dumps(["growing apart", "different"]),
            template="Sometimes friendships change as people grow, {name}.",
            min_friendship_level=5,
            min_age=10,
            max_age=14,
            tone="empathetic",
            response_style="validating",
            expert_reviewed=True
        )

        # Should require age 10+
        assert template.is_appropriate_for_age(9) is False
        assert template.is_appropriate_for_age(10) is True
