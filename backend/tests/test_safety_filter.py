"""
Tests for SafetyFilter - Comprehensive safety orchestration layer
Tests integration of all specialized services
"""

import pytest
from services.safety_filter import SafetyFilter, safety_filter


class TestSafetyFilterIntegration:
    """Test SafetyFilter integration with all specialized services"""

    def setup_method(self):
        """Set up test fixtures"""
        self.filter = SafetyFilter()

    def test_initialization(self):
        """Test that SafetyFilter initializes all services correctly"""
        assert self.filter.crisis_detector is not None
        assert self.filter.profanity_filter is not None
        assert self.filter.inappropriate_detector is not None
        assert self.filter.word_list is not None
        assert self.filter.bullying_detector is not None
        # Verify crisis detector has keyword lists
        assert len(self.filter.crisis_detector.suicide_keywords) > 0
        assert len(self.filter.crisis_detector.self_harm_keywords) > 0
        assert len(self.filter.crisis_detector.abuse_physical_keywords) > 0
        # Verify bullying detector has keyword lists
        assert len(self.filter.bullying_detector.physical_bullying_keywords) > 0
        assert len(self.filter.bullying_detector.verbal_bullying_keywords) > 0
        assert len(self.filter.bullying_detector.social_exclusion_keywords) > 0

    def test_crisis_detection_highest_priority(self):
        """Test that crisis detection has highest priority"""
        result = self.filter.check_message("I want to kill myself")

        assert result["safe"] is False
        assert "crisis" in result["flags"]
        assert result["severity"] == "critical"
        assert result["action"] == "crisis_response"
        assert result["notify_parent"] is True
        assert "988" in result["response_message"]
        assert "crisis" in result["details"]

    def test_abuse_detection_via_crisis_detector(self):
        """Test that abuse detection works via crisis detector"""
        result = self.filter.check_message("My dad hits me every day")

        assert result["safe"] is False
        assert "abuse" in result["flags"]
        assert result["severity"] == "critical"
        assert result["action"] == "crisis_response"
        assert result["notify_parent"] is True
        assert result["details"]["crisis"]["detected"] is True
        assert result["details"]["crisis"]["primary_category"] == "abuse_physical"
        assert "Childhelp" in result["response_message"]

    def test_inappropriate_request_detection(self):
        """Test inappropriate request detection integration"""
        # Test violence pattern
        result = self.filter.check_message("How to make a bomb?")

        assert result["safe"] is False
        assert "inappropriate_request" in result["flags"]
        assert result["severity"] in ["high", "critical"]
        assert result["notify_parent"] is True
        assert "inappropriate_request" in result["details"]

    def test_profanity_detection_integration(self):
        """Test profanity detection service integration"""
        # Test severe profanity
        result = self.filter.check_message("This is fucking stupid", user_id=1)

        assert result["safe"] is False  # Severe profanity is blocked
        assert "profanity" in result["flags"]
        assert result["severity"] == "high"  # Severe maps to high
        assert "profanity" in result["details"]
        assert result["details"]["profanity"]["contains_profanity"] is True

    def test_bullying_detection(self):
        """Test bullying keyword detection with categories"""
        result = self.filter.check_message("Everyone at school is bullying me")

        assert "bullying" in result["flags"]
        assert result["severity"] == "medium"
        assert result["action"] == "supportive_response"
        assert "bullying" in result["details"]
        assert result["details"]["bullying"]["detected"] is True
        assert result["details"]["bullying"]["primary_category"] == "physical_bullying"
        assert len(result["details"]["bullying"]["keywords_found"]) > 0

    def test_priority_order_crisis_over_profanity(self):
        """Test that crisis detection overrides profanity detection"""
        result = self.filter.check_message("I want to kill myself, this is shit")

        # Crisis should be detected, not profanity
        assert "crisis" in result["flags"]
        assert "profanity" not in result["flags"]
        assert result["severity"] == "critical"

    def test_priority_order_abuse_over_inappropriate(self):
        """Test that abuse detection overrides inappropriate request detection"""
        result = self.filter.check_message("My teacher hits me and how to steal")

        # Abuse should be detected
        assert "abuse" in result["flags"]
        assert result["severity"] == "critical"

    def test_safe_message(self):
        """Test that safe messages pass through"""
        result = self.filter.check_message("Can you help me with my math homework?")

        assert result["safe"] is True
        assert len(result["flags"]) == 0
        assert result["severity"] == "none"
        assert result["action"] == "allow"
        assert result["notify_parent"] is False

    def test_mild_profanity_allowed(self):
        """Test that mild profanity is detected but allowed"""
        result = self.filter.check_message("This homework is stupid", user_id=1)

        # Mild profanity is detected but message is allowed
        assert result["severity"] == "low"
        assert "profanity" in result["flags"]
        # Low severity doesn't trigger parent notification
        assert result["notify_parent"] is False

    def test_parent_notification_logic(self):
        """Test parent notification for different severity levels"""
        # Critical - notify
        result_critical = self.filter.check_message("I want to die")
        assert result_critical["notify_parent"] is True

        # High - notify
        result_high = self.filter.check_message("fuck you", user_id=1)
        assert result_high["notify_parent"] is True

        # Medium - don't notify
        result_medium = self.filter.check_message("I'm being bullied")
        assert result_medium["notify_parent"] is False

        # Low - don't notify
        result_low = self.filter.check_message("This is stupid", user_id=1)
        assert result_low["notify_parent"] is False

    def test_user_violation_tracking(self):
        """Test that user violations are tracked across messages"""
        user_id = 999

        # First violation
        result1 = self.filter.check_message("damn it", user_id=user_id)
        assert "profanity" in result1["flags"]

        # Second violation
        result2 = self.filter.check_message("this sucks", user_id=user_id)
        assert "profanity" in result2["flags"]

        # Profanity filter tracks violations internally
        # This is tested in test_profanity_detection_filter.py

    def test_response_messages(self):
        """Test that appropriate response messages are returned"""
        # Crisis response
        result_crisis = self.filter.check_message("I want to kill myself")
        assert "988" in result_crisis["response_message"]
        assert "Crisis Text Line" in result_crisis["response_message"]

        # Abuse response
        result_abuse = self.filter.check_message("My dad hits me")
        assert "Childhelp" in result_abuse["response_message"]

        # Bullying response
        result_bullying = self.filter.check_message("I'm being bullied at school")
        assert "Bullying" in result_bullying["response_message"] or "sorry" in result_bullying["response_message"]

    def test_details_structure(self):
        """Test that details dictionary contains correct information"""
        result = self.filter.check_message("How to steal from a store", user_id=1)

        assert "details" in result
        assert isinstance(result["details"], dict)
        # Should have inappropriate_request details
        assert "inappropriate_request" in result["details"]

    def test_multiple_keywords_same_category(self):
        """Test detection when multiple keywords from same category present"""
        result = self.filter.check_message("I want to kill myself and end it all")

        assert result["severity"] == "critical"
        assert "crisis" in result["flags"]
        # Details should show multiple keywords found
        assert len(result["details"]["crisis"]["keywords_found"]) >= 2

    def test_get_service_stats(self):
        """Test getting statistics from all services"""
        stats = self.filter.get_service_stats()

        assert "crisis_keyword_list" in stats
        assert "profanity_word_list" in stats
        assert "profanity_filter" in stats
        assert "inappropriate_detector" in stats
        assert "bullying_keyword_list" in stats

        # Verify crisis keyword list stats
        crisis_stats = stats["crisis_keyword_list"]
        assert crisis_stats["suicide_keywords"] > 5
        assert crisis_stats["self_harm_keywords"] > 5
        assert crisis_stats["abuse_physical_keywords"] > 5
        assert crisis_stats["total_keywords"] > 50

        # Verify bullying keyword list stats
        bullying_stats = stats["bullying_keyword_list"]
        assert bullying_stats["physical_bullying_keywords"] > 5
        assert bullying_stats["verbal_bullying_keywords"] > 5
        assert bullying_stats["social_exclusion_keywords"] > 5
        assert bullying_stats["total_keywords"] > 30

    def test_reset_user_violations(self):
        """Test resetting user violations"""
        user_id = 123

        # Create some violations
        self.filter.check_message("damn", user_id=user_id)
        self.filter.check_message("crap", user_id=user_id)

        # Reset violations
        self.filter.reset_user_violations(user_id)

        # After reset, violations should be cleared
        # (Actual violation count is tracked in profanity_filter)
        assert self.filter.profanity_filter.user_violations.get(user_id, 0) == 0


class TestCrisisDetectionCategories:
    """Test crisis detection with categorization"""

    def setup_method(self):
        """Set up test fixtures"""
        self.filter = SafetyFilter()

    def test_suicide_category_detection(self):
        """Test detection of suicide category"""
        test_messages = [
            "I want to kill myself",
            "I'm thinking about suicide",
            "I want to die",
            "There's no reason to live",
        ]

        for message in test_messages:
            result = self.filter.check_message(message)
            assert result["severity"] == "critical"
            assert "crisis" in result["flags"]
            assert result["details"]["crisis"]["primary_category"] == "suicide"
            assert "988" in result["response_message"]

    def test_self_harm_category_detection(self):
        """Test detection of self-harm category"""
        test_messages = [
            "I cut myself last night",
            "I want to hurt myself",
            "I've been burning myself",
        ]

        for message in test_messages:
            result = self.filter.check_message(message)
            assert result["severity"] == "critical"
            assert "crisis" in result["flags"]
            assert result["details"]["crisis"]["primary_category"] == "self_harm"
            assert "988" in result["response_message"]

    def test_physical_abuse_category_detection(self):
        """Test detection of physical abuse category"""
        test_messages = [
            "My dad hits me every day",
            "My mom beats me when I get bad grades",
            "He kicks me and punches me",
        ]

        for message in test_messages:
            result = self.filter.check_message(message)
            assert result["severity"] == "critical"
            assert "abuse" in result["flags"]
            assert result["details"]["crisis"]["primary_category"] == "abuse_physical"
            assert "Childhelp" in result["response_message"]

    def test_emotional_abuse_category_detection(self):
        """Test detection of emotional abuse category"""
        test_messages = [
            "My dad threatens me all the time",
            "My mom screams at me and makes me scared",
            "They won't let me eat dinner",
        ]

        for message in test_messages:
            result = self.filter.check_message(message)
            assert result["severity"] == "critical"
            assert "abuse" in result["flags"]
            assert result["details"]["crisis"]["primary_category"] == "abuse_emotional"
            assert "Childhelp" in result["response_message"]

    def test_sexual_abuse_category_detection(self):
        """Test detection of sexual abuse category"""
        test_messages = [
            "Someone touched me inappropriately",
            "My uncle touched my private parts",
            "He told me not to tell anyone",
        ]

        for message in test_messages:
            result = self.filter.check_message(message)
            assert result["severity"] == "critical"
            assert "abuse" in result["flags"]
            assert result["details"]["crisis"]["primary_category"] == "abuse_sexual"
            assert "Childhelp" in result["response_message"]

    def test_multiple_crisis_categories(self):
        """Test detection of multiple crisis categories in one message"""
        message = "I want to kill myself and I cut myself and my dad hits me"
        result = self.filter.check_message(message)

        assert result["severity"] == "critical"
        assert "crisis" in result["flags"] or "abuse" in result["flags"]
        # Should detect multiple categories
        all_categories = result["details"]["crisis"]["all_categories"]
        assert len(all_categories) >= 2
        # Should include suicide, self_harm, and abuse_physical
        assert "suicide" in all_categories
        assert "self_harm" in all_categories
        assert "abuse_physical" in all_categories

    def test_crisis_category_priority(self):
        """Test that crisis categories follow priority order"""
        # Suicide should have priority over self-harm
        result1 = self.filter.check_message("I want to kill myself and I cut myself")
        assert result1["details"]["crisis"]["primary_category"] == "suicide"

        # Self-harm should have priority over abuse
        result2 = self.filter.check_message("I cut myself and my dad hits me")
        assert result2["details"]["crisis"]["primary_category"] == "self_harm"

        # Sexual abuse should have priority among abuse types
        result3 = self.filter.check_message("My dad hits me and touched me inappropriately")
        assert result3["details"]["crisis"]["primary_category"] == "abuse_sexual"

    def test_crisis_keywords_found_details(self):
        """Test that specific keywords found are reported"""
        result = self.filter.check_message("I want to kill myself because there's no reason to live")

        assert "crisis" in result["flags"]
        keywords_found = result["details"]["crisis"]["keywords_found"]
        assert len(keywords_found) > 0
        # Each keyword should have category and severity
        for kw in keywords_found:
            assert "keyword" in kw
            assert "category" in kw
            assert "severity" in kw
            assert kw["severity"] == "critical"


class TestConvenienceFunctions:
    """Test module-level convenience functions"""

    def test_check_message_convenience(self):
        """Test convenience function for check_message"""
        from services.safety_filter import check_message

        result = check_message("Hello, how are you?")
        assert result["safe"] is True
        assert result["severity"] == "none"

    def test_get_crisis_response_convenience(self):
        """Test convenience function for crisis response"""
        from services.safety_filter import get_crisis_response

        response = get_crisis_response()
        assert "988" in response
        assert "Crisis Text Line" in response

    def test_get_abuse_response_convenience(self):
        """Test convenience function for abuse response"""
        from services.safety_filter import get_abuse_response

        response = get_abuse_response()
        assert "Childhelp" in response

    def test_get_bullying_response_convenience(self):
        """Test convenience function for bullying response"""
        from services.safety_filter import get_bullying_response

        response = get_bullying_response("Alice")
        assert "Alice" in response
        assert "Bullying" in response or "sorry" in response

    def test_get_service_stats_convenience(self):
        """Test convenience function for service stats"""
        from services.safety_filter import get_service_stats

        stats = get_service_stats()
        assert "profanity_word_list" in stats

    def test_reset_user_violations_convenience(self):
        """Test convenience function for resetting violations"""
        from services.safety_filter import reset_user_violations

        # Should not raise any errors
        reset_user_violations(123)


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def setup_method(self):
        """Set up test fixtures"""
        self.filter = SafetyFilter()

    def test_empty_message(self):
        """Test empty message handling"""
        result = self.filter.check_message("")
        assert result["safe"] is True
        assert result["severity"] == "none"

    def test_whitespace_only_message(self):
        """Test whitespace-only message"""
        result = self.filter.check_message("   \n\t  ")
        assert result["safe"] is True

    def test_very_long_message(self):
        """Test very long message"""
        long_message = "This is a safe message. " * 1000
        result = self.filter.check_message(long_message)
        assert result["safe"] is True

    def test_case_insensitivity(self):
        """Test that detection is case insensitive"""
        # Crisis keywords should be detected regardless of case
        result1 = self.filter.check_message("I WANT TO KILL MYSELF")
        result2 = self.filter.check_message("i want to kill myself")
        result3 = self.filter.check_message("I Want To Kill Myself")

        assert result1["severity"] == "critical"
        assert result2["severity"] == "critical"
        assert result3["severity"] == "critical"

    def test_keywords_in_context(self):
        """Test keywords detected in sentence context"""
        # Should still detect even with surrounding words
        result = self.filter.check_message(
            "Sometimes I feel like I want to kill myself but I know I shouldn't"
        )
        assert "crisis" in result["flags"]

    def test_unicode_characters(self):
        """Test handling of unicode characters"""
        result = self.filter.check_message("Hello 你好 مرحبا")
        assert result["safe"] is True

    def test_special_characters(self):
        """Test handling of special characters"""
        result = self.filter.check_message("Hello!!! How are you??? :) :D <3")
        assert result["safe"] is True


class TestIntegrationScenarios:
    """Test realistic integration scenarios"""

    def setup_method(self):
        """Set up test fixtures"""
        self.filter = SafetyFilter()

    def test_student_homework_help(self):
        """Test normal student homework interaction"""
        messages = [
            "Can you help me with my algebra homework?",
            "What's the capital of France?",
            "How do I write a good essay?",
        ]

        for message in messages:
            result = self.filter.check_message(message)
            assert result["safe"] is True
            assert result["severity"] == "none"

    def test_student_frustrated_with_homework(self):
        """Test student expressing frustration (mild profanity)"""
        result = self.filter.check_message(
            "This math homework is so stupid and hard!", user_id=1
        )

        # Should detect mild profanity but allow message
        assert "profanity" in result["flags"]
        assert result["severity"] == "low"
        # Should get educational response
        assert result["response_message"] != ""

    def test_student_seeking_inappropriate_help(self):
        """Test student trying to get help with cheating"""
        result = self.filter.check_message(
            "How can I cheat on my test without getting caught?"
        )

        assert result["safe"] is False
        assert "inappropriate_request" in result["flags"]
        assert result["severity"] in ["medium", "high"]

    def test_student_in_crisis(self):
        """Test student expressing self-harm thoughts"""
        result = self.filter.check_message(
            "I failed my test and now I feel like I want to hurt myself"
        )

        assert result["safe"] is False
        assert "crisis" in result["flags"]
        assert result["severity"] == "critical"
        assert result["notify_parent"] is True
        # Should provide crisis resources
        assert "988" in result["response_message"]

    def test_student_reporting_bullying(self):
        """Test student reporting being bullied"""
        result = self.filter.check_message(
            "The kids at school keep bullying me and making fun of me"
        )

        assert "bullying" in result["flags"]
        assert result["severity"] == "medium"
        assert result["action"] == "supportive_response"
        # Should provide supportive response
        assert len(result["response_message"]) > 0

    def test_escalating_profanity(self):
        """Test escalation with repeated profanity violations"""
        user_id = 456

        # First mild violation
        result1 = self.filter.check_message("damn it", user_id=user_id)
        assert result1["severity"] == "low"

        # Second violation
        result2 = self.filter.check_message("this sucks", user_id=user_id)
        assert result2["severity"] in ["low", "medium"]

        # Severe profanity should always be blocked
        result3 = self.filter.check_message("fuck this", user_id=user_id)
        assert result3["severity"] == "high"
        assert result3["safe"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
