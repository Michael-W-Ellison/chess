"""
Tests for Crisis Response Templates Service
Comprehensive test coverage for crisis response template generation
"""

import pytest
from services.crisis_response_templates import (
    CrisisResponseTemplates,
    crisis_response_templates,
    get_response,
    get_suicide_response,
    get_self_harm_response,
    get_physical_abuse_response,
    get_emotional_abuse_response,
    get_sexual_abuse_response,
    get_resources_for_category,
    get_all_resources,
    get_stats,
)


class TestCrisisResponseTemplatesInitialization:
    """Test CrisisResponseTemplates initialization"""

    def test_initialization(self):
        """Test service initializes correctly"""
        service = CrisisResponseTemplates()
        assert service is not None
        assert hasattr(service, "concern_openings")
        assert hasattr(service, "validation_messages")
        assert hasattr(service, "crisis_resources")
        assert hasattr(service, "trusted_adults_guidance")
        assert hasattr(service, "closing_messages")

    def test_has_all_crisis_categories(self):
        """Test service has all required crisis categories"""
        service = CrisisResponseTemplates()
        expected_categories = ["suicide", "self_harm", "abuse_physical", "abuse_emotional", "abuse_sexual"]

        for category in expected_categories:
            assert category in service.concern_openings
            assert category in service.validation_messages
            assert category in service.crisis_resources
            assert category in service.closing_messages

    def test_global_instance(self):
        """Test global instance is available"""
        assert crisis_response_templates is not None


class TestSuicideResponses:
    """Test suicide crisis responses"""

    def test_get_suicide_response(self):
        """Test getting suicide response"""
        response = crisis_response_templates.get_suicide_response()
        assert response is not None
        assert len(response) > 0

    def test_suicide_response_contains_988(self):
        """Test suicide response contains 988 hotline"""
        response = crisis_response_templates.get_suicide_response()
        assert "988" in response

    def test_suicide_response_contains_crisis_text_line(self):
        """Test suicide response contains Crisis Text Line"""
        response = crisis_response_templates.get_suicide_response()
        assert "741741" in response

    def test_suicide_response_has_concern_opening(self):
        """Test suicide response starts with concern"""
        response = crisis_response_templates.get_suicide_response()
        assert "worried" in response.lower() or "concerned" in response.lower()

    def test_suicide_response_has_trusted_adults_guidance(self):
        """Test suicide response mentions trusted adults"""
        response = crisis_response_templates.get_suicide_response()
        assert "parent" in response.lower() or "teacher" in response.lower()

    def test_suicide_response_has_closing_message(self):
        """Test suicide response has supportive closing"""
        response = crisis_response_templates.get_suicide_response()
        assert "💙" in response


class TestSelfHarmResponses:
    """Test self-harm crisis responses"""

    def test_get_self_harm_response(self):
        """Test getting self-harm response"""
        response = crisis_response_templates.get_self_harm_response()
        assert response is not None
        assert len(response) > 0

    def test_self_harm_response_contains_crisis_text_line(self):
        """Test self-harm response contains Crisis Text Line as primary"""
        response = crisis_response_templates.get_self_harm_response()
        assert "741741" in response

    def test_self_harm_response_contains_988(self):
        """Test self-harm response contains 988 as secondary"""
        response = crisis_response_templates.get_self_harm_response()
        assert "988" in response

    def test_self_harm_response_has_validation(self):
        """Test self-harm response validates user feelings"""
        response = crisis_response_templates.get_self_harm_response()
        assert "feeling" in response.lower() or "care" in response.lower()


class TestPhysicalAbuseResponses:
    """Test physical abuse crisis responses"""

    def test_get_physical_abuse_response(self):
        """Test getting physical abuse response"""
        response = crisis_response_templates.get_physical_abuse_response()
        assert response is not None
        assert len(response) > 0

    def test_physical_abuse_response_contains_childhelp(self):
        """Test physical abuse response contains Childhelp hotline"""
        response = crisis_response_templates.get_physical_abuse_response()
        assert "1-800-422-4453" in response or "Childhelp" in response

    def test_physical_abuse_response_contains_911(self):
        """Test physical abuse response contains 911"""
        response = crisis_response_templates.get_physical_abuse_response()
        assert "911" in response

    def test_physical_abuse_response_has_safety_focus(self):
        """Test physical abuse response focuses on safety"""
        response = crisis_response_templates.get_physical_abuse_response()
        assert "safe" in response.lower()

    def test_physical_abuse_response_has_danger_guidance(self):
        """Test physical abuse response mentions immediate danger"""
        response = crisis_response_templates.get_physical_abuse_response()
        assert "danger" in response.lower() or "immediate" in response.lower()


class TestEmotionalAbuseResponses:
    """Test emotional abuse crisis responses"""

    def test_get_emotional_abuse_response(self):
        """Test getting emotional abuse response"""
        response = crisis_response_templates.get_emotional_abuse_response()
        assert response is not None
        assert len(response) > 0

    def test_emotional_abuse_response_contains_childhelp(self):
        """Test emotional abuse response contains Childhelp"""
        response = crisis_response_templates.get_emotional_abuse_response()
        assert "1-800-422-4453" in response or "Childhelp" in response

    def test_emotional_abuse_response_contains_crisis_text_line(self):
        """Test emotional abuse response contains Crisis Text Line as secondary"""
        response = crisis_response_templates.get_emotional_abuse_response()
        assert "741741" in response

    def test_emotional_abuse_response_validates_experience(self):
        """Test emotional abuse response validates user experience"""
        response = crisis_response_templates.get_emotional_abuse_response()
        assert "not okay" in response.lower() or "deserve" in response.lower()


class TestSexualAbuseResponses:
    """Test sexual abuse crisis responses"""

    def test_get_sexual_abuse_response(self):
        """Test getting sexual abuse response"""
        response = crisis_response_templates.get_sexual_abuse_response()
        assert response is not None
        assert len(response) > 0

    def test_sexual_abuse_response_contains_childhelp(self):
        """Test sexual abuse response contains Childhelp"""
        response = crisis_response_templates.get_sexual_abuse_response()
        assert "1-800-422-4453" in response or "Childhelp" in response

    def test_sexual_abuse_response_contains_rainn(self):
        """Test sexual abuse response contains RAINN hotline"""
        response = crisis_response_templates.get_sexual_abuse_response()
        assert "1-800-656-4673" in response or "RAINN" in response

    def test_sexual_abuse_response_emphasizes_not_fault(self):
        """Test sexual abuse response emphasizes not user's fault"""
        response = crisis_response_templates.get_sexual_abuse_response()
        assert "not your fault" in response.lower()

    def test_sexual_abuse_response_has_safety_message(self):
        """Test sexual abuse response mentions safety"""
        response = crisis_response_templates.get_sexual_abuse_response()
        assert "safe" in response.lower()


class TestGenericResponse:
    """Test generic crisis response"""

    def test_get_response_with_unknown_category(self):
        """Test generic response for unknown category"""
        response = crisis_response_templates.get_response("unknown_category")
        assert response is not None
        assert len(response) > 0

    def test_generic_response_has_resources(self):
        """Test generic response includes crisis resources"""
        response = crisis_response_templates.get_response("unknown_category")
        assert "741741" in response or "988" in response


class TestResponseStructure:
    """Test response structure and components"""

    def test_response_has_multiple_sections(self):
        """Test response has multiple sections (concern, validation, guidance, resources, closing)"""
        response = crisis_response_templates.get_suicide_response()
        # Should have multiple paragraphs/sections
        sections = response.split("\n\n")
        assert len(sections) >= 3

    def test_response_uses_age_appropriate_language(self):
        """Test response uses age-appropriate language"""
        response = crisis_response_templates.get_suicide_response()
        # Should not use overly clinical or complex language
        assert "parent" in response.lower() or "teacher" in response.lower()
        # Should be supportive
        assert "help" in response.lower()

    def test_all_responses_have_closing_emoji(self):
        """Test all responses have supportive emoji"""
        categories = ["suicide", "self_harm", "abuse_physical", "abuse_emotional", "abuse_sexual"]
        for category in categories:
            response = crisis_response_templates.get_response(category)
            assert "💙" in response

    def test_abuse_responses_have_trusted_adults_list(self):
        """Test abuse responses have trusted adults list"""
        abuse_categories = ["abuse_physical", "abuse_emotional", "abuse_sexual"]
        for category in abuse_categories:
            response = crisis_response_templates.get_response(category)
            # Should have bullet points with trusted adults
            assert "- " in response


class TestResourceRetrieval:
    """Test resource retrieval methods"""

    def test_get_resources_for_suicide(self):
        """Test getting resources for suicide category"""
        resources = crisis_response_templates.get_resources_for_category("suicide")
        assert "primary" in resources
        assert "secondary" in resources
        assert resources["primary"]["contact"] == "988 (call or text)"

    def test_get_resources_for_self_harm(self):
        """Test getting resources for self-harm category"""
        resources = crisis_response_templates.get_resources_for_category("self_harm")
        assert "primary" in resources
        assert "secondary" in resources
        assert "741741" in resources["primary"]["contact"]

    def test_get_resources_for_physical_abuse(self):
        """Test getting resources for physical abuse category"""
        resources = crisis_response_templates.get_resources_for_category("abuse_physical")
        assert "primary" in resources
        assert "secondary" in resources
        assert "1-800-422-4453" in resources["primary"]["contact"]

    def test_get_resources_for_emotional_abuse(self):
        """Test getting resources for emotional abuse category"""
        resources = crisis_response_templates.get_resources_for_category("abuse_emotional")
        assert "primary" in resources
        assert "1-800-422-4453" in resources["primary"]["contact"]

    def test_get_resources_for_sexual_abuse(self):
        """Test getting resources for sexual abuse category"""
        resources = crisis_response_templates.get_resources_for_category("abuse_sexual")
        assert "primary" in resources
        assert "secondary" in resources
        # Should have both Childhelp and RAINN
        primary_contact = resources["primary"]["contact"]
        secondary_contact = resources["secondary"]["contact"]
        assert "1-800-422-4453" in primary_contact or "1-800-656-4673" in primary_contact

    def test_get_resources_for_unknown_category(self):
        """Test getting resources for unknown category returns generic resources"""
        resources = crisis_response_templates.get_resources_for_category("unknown")
        assert "primary" in resources
        assert "secondary" in resources

    def test_get_all_resources(self):
        """Test getting all resources"""
        all_resources = crisis_response_templates.get_all_resources()
        assert len(all_resources) == 5
        assert "suicide" in all_resources
        assert "self_harm" in all_resources
        assert "abuse_physical" in all_resources
        assert "abuse_emotional" in all_resources
        assert "abuse_sexual" in all_resources

    def test_resources_have_required_fields(self):
        """Test all resources have required fields (name, contact, description)"""
        all_resources = crisis_response_templates.get_all_resources()
        for category, resources in all_resources.items():
            assert "primary" in resources
            assert "secondary" in resources

            primary = resources["primary"]
            assert "name" in primary
            assert "contact" in primary
            assert "description" in primary

            secondary = resources["secondary"]
            assert "name" in secondary
            assert "contact" in secondary
            assert "description" in secondary


class TestStatistics:
    """Test statistics methods"""

    def test_get_stats(self):
        """Test getting statistics"""
        stats = crisis_response_templates.get_stats()
        assert "total_categories" in stats
        assert "categories" in stats
        assert "total_resources" in stats
        assert "resource_categories" in stats

    def test_stats_has_correct_category_count(self):
        """Test stats has correct number of categories"""
        stats = crisis_response_templates.get_stats()
        assert stats["total_categories"] == 5

    def test_stats_lists_all_categories(self):
        """Test stats lists all categories"""
        stats = crisis_response_templates.get_stats()
        expected_categories = ["suicide", "self_harm", "abuse_physical", "abuse_emotional", "abuse_sexual"]
        for category in expected_categories:
            assert category in stats["categories"]


class TestConvenienceFunctions:
    """Test module-level convenience functions"""

    def test_get_response_function(self):
        """Test get_response convenience function"""
        response = get_response("suicide")
        assert response is not None
        assert "988" in response

    def test_get_suicide_response_function(self):
        """Test get_suicide_response convenience function"""
        response = get_suicide_response()
        assert response is not None
        assert "988" in response

    def test_get_self_harm_response_function(self):
        """Test get_self_harm_response convenience function"""
        response = get_self_harm_response()
        assert response is not None
        assert "741741" in response

    def test_get_physical_abuse_response_function(self):
        """Test get_physical_abuse_response convenience function"""
        response = get_physical_abuse_response()
        assert response is not None
        assert "1-800-422-4453" in response

    def test_get_emotional_abuse_response_function(self):
        """Test get_emotional_abuse_response convenience function"""
        response = get_emotional_abuse_response()
        assert response is not None
        assert "1-800-422-4453" in response

    def test_get_sexual_abuse_response_function(self):
        """Test get_sexual_abuse_response convenience function"""
        response = get_sexual_abuse_response()
        assert response is not None
        assert "1-800-656-4673" in response

    def test_get_resources_for_category_function(self):
        """Test get_resources_for_category convenience function"""
        resources = get_resources_for_category("suicide")
        assert "primary" in resources
        assert "988" in resources["primary"]["contact"]

    def test_get_all_resources_function(self):
        """Test get_all_resources convenience function"""
        all_resources = get_all_resources()
        assert len(all_resources) == 5

    def test_get_stats_function(self):
        """Test get_stats convenience function"""
        stats = get_stats()
        assert stats["total_categories"] == 5


class TestCaseInsensitivity:
    """Test case insensitivity for category names"""

    def test_get_response_uppercase_category(self):
        """Test get_response with uppercase category"""
        response_lower = crisis_response_templates.get_response("suicide")
        response_upper = crisis_response_templates.get_response("SUICIDE")
        assert response_lower == response_upper

    def test_get_response_mixed_case_category(self):
        """Test get_response with mixed case category"""
        response_lower = crisis_response_templates.get_response("abuse_physical")
        response_mixed = crisis_response_templates.get_response("Abuse_Physical")
        assert response_lower == response_mixed

    def test_get_resources_case_insensitive(self):
        """Test get_resources_for_category is case insensitive"""
        resources_lower = crisis_response_templates.get_resources_for_category("suicide")
        resources_upper = crisis_response_templates.get_resources_for_category("SUICIDE")
        assert resources_lower == resources_upper


class TestResponseContent:
    """Test specific response content requirements"""

    def test_suicide_response_mentions_988_prominently(self):
        """Test suicide response mentions 988 (primary resource)"""
        response = crisis_response_templates.get_suicide_response()
        # 988 should appear before 741741 (primary vs secondary)
        pos_988 = response.find("988")
        pos_741741 = response.find("741741")
        assert pos_988 >= 0
        assert pos_741741 >= 0
        assert pos_988 < pos_741741

    def test_self_harm_response_mentions_crisis_text_line_prominently(self):
        """Test self-harm response mentions Crisis Text Line as primary"""
        response = crisis_response_templates.get_self_harm_response()
        # 741741 should appear before 988 (primary vs secondary)
        pos_741741 = response.find("741741")
        pos_988 = response.find("988")
        assert pos_741741 >= 0
        assert pos_988 >= 0
        assert pos_741741 < pos_988

    def test_physical_abuse_mentions_911_for_immediate_danger(self):
        """Test physical abuse response mentions 911 for immediate danger"""
        response = crisis_response_templates.get_physical_abuse_response()
        assert "911" in response
        assert "immediate" in response.lower() or "danger" in response.lower()

    def test_all_abuse_responses_mention_childhelp(self):
        """Test all abuse responses mention Childhelp"""
        abuse_categories = ["abuse_physical", "abuse_emotional", "abuse_sexual"]
        for category in abuse_categories:
            response = crisis_response_templates.get_response(category)
            assert "1-800-422-4453" in response or "Childhelp" in response

    def test_sexual_abuse_includes_rainn(self):
        """Test sexual abuse response includes RAINN hotline"""
        response = crisis_response_templates.get_sexual_abuse_response()
        assert "1-800-656-4673" in response or "RAINN" in response
