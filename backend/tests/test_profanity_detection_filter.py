"""
Tests for Profanity Detection Filter Service
Comprehensive tests for profanity detection and educational responses
"""

import pytest
from services.profanity_detection_filter import (
    ProfanityDetectionFilter,
    profanity_detection_filter,
    check_message,
    get_educational_alternatives,
    reset_user_violations,
    get_user_violation_count,
    should_notify_parent,
    get_filter_stats,
)


class TestFilterInitialization:
    """Test filter initialization"""

    def test_filter_initialized(self):
        """Test that filter is properly initialized"""
        filter_service = ProfanityDetectionFilter()

        assert filter_service.word_list is not None
        assert hasattr(filter_service, "enabled")
        assert hasattr(filter_service, "user_violations")

    def test_filter_enabled_by_default(self):
        """Test that filter is enabled by default"""
        filter_service = ProfanityDetectionFilter()

        assert filter_service.enabled is True


class TestCheckMessageClean:
    """Test check_message with clean messages"""

    def test_clean_message_passes(self):
        """Test that clean messages pass through"""
        result = check_message("Hello, how are you today?")

        assert result["contains_profanity"] is False
        assert len(result["profanity_words"]) == 0
        assert result["highest_severity"] == "none"
        assert result["allow_message"] is True
        assert result["censored_message"] == "Hello, how are you today?"

    def test_multiple_clean_messages(self):
        """Test multiple clean messages"""
        clean_messages = [
            "I love learning!",
            "Can you help me with my homework?",
            "This is really interesting!",
            "Tell me about science",
        ]

        for message in clean_messages:
            result = check_message(message)
            assert result["contains_profanity"] is False
            assert result["allow_message"] is True


class TestCheckMessageMild:
    """Test check_message with mild profanity"""

    def test_mild_profanity_detected(self):
        """Test that mild profanity is detected"""
        result = check_message("That's so stupid")

        assert result["contains_profanity"] is True
        assert len(result["profanity_words"]) > 0
        assert result["highest_severity"] == "mild"
        assert result["allow_message"] is True  # Mild allows through
        assert "***" in result["censored_message"]

    def test_mild_profanity_educates(self):
        """Test that mild profanity triggers educational response"""
        result = check_message("You're so dumb")

        assert result["action"] == "gentle_educate"
        assert len(result["response_message"]) > 0
        assert "respectful" in result["response_message"].lower() or "nice" in result["response_message"].lower()

    def test_multiple_mild_words(self):
        """Test detection of multiple mild words"""
        result = check_message("That's damn stupid")

        assert result["contains_profanity"] is True
        # Should find multiple words
        assert len(result["profanity_words"]) >= 2


class TestCheckMessageModerate:
    """Test check_message with moderate profanity"""

    def test_moderate_profanity_detected(self):
        """Test that moderate profanity is detected"""
        result = check_message("You're such an ass")

        assert result["contains_profanity"] is True
        assert result["highest_severity"] == "moderate"

    def test_moderate_profanity_first_offense(self):
        """Test moderate profanity on first offense"""
        result = check_message("That's such an ass move", user_id=1001)

        assert result["action"] == "educate"
        assert result["allow_message"] is True  # First offense allows

    def test_moderate_profanity_repeated(self):
        """Test moderate profanity after repeated offenses"""
        filter_service = ProfanityDetectionFilter()

        # First two offenses
        filter_service.check_message("You're an ass", user_id=2001)
        filter_service.check_message("That's an ass thing", user_id=2001)

        # Third offense - should escalate
        result = filter_service.check_message("This is pissed off", user_id=2001)

        assert result["action"] == "warn_and_limit"
        assert result["allow_message"] is False  # Block after repeated


class TestCheckMessageSevere:
    """Test check_message with severe profanity"""

    def test_severe_profanity_detected(self):
        """Test that severe profanity is detected"""
        result = check_message("What the fuck")

        assert result["contains_profanity"] is True
        assert result["highest_severity"] == "severe"

    def test_severe_profanity_blocked(self):
        """Test that severe profanity is blocked"""
        result = check_message("This is fucking stupid")

        assert result["action"] == "block_and_educate"
        assert result["allow_message"] is False

    def test_severe_profanity_response(self):
        """Test that severe profanity gets appropriate response"""
        result = check_message("Shit happens")

        assert len(result["response_message"]) > 0
        assert "appropriate" in result["response_message"].lower()
        assert "respectful" in result["response_message"].lower()


class TestSeverityDetection:
    """Test severity level detection"""

    def test_highest_severity_wins(self):
        """Test that highest severity is reported"""
        # Message with mild and severe profanity
        result = check_message("This damn shit is stupid")

        # Should report severe (highest)
        assert result["highest_severity"] == "severe"

    def test_severity_order(self):
        """Test that severity is correctly ordered"""
        mild_result = check_message("That's stupid")
        moderate_result = check_message("You're an ass")
        severe_result = check_message("What the fuck")

        assert mild_result["highest_severity"] == "mild"
        assert moderate_result["highest_severity"] == "moderate"
        assert severe_result["highest_severity"] == "severe"


class TestCensoring:
    """Test message censoring"""

    def test_profanity_censored(self):
        """Test that profanity is censored in output"""
        result = check_message("This is damn good")

        assert "damn" not in result["censored_message"].lower()
        assert "***" in result["censored_message"]

    def test_multiple_words_censored(self):
        """Test that multiple profanity words are censored"""
        result = check_message("This damn stupid thing")

        censored = result["censored_message"]
        assert "damn" not in censored.lower()
        assert "stupid" not in censored.lower()
        assert censored.count("***") >= 2

    def test_clean_text_not_censored(self):
        """Test that clean text is not modified"""
        message = "This is a great day"
        result = check_message(message)

        assert result["censored_message"] == message


class TestViolationTracking:
    """Test user violation tracking"""

    def test_violation_count_increases(self):
        """Test that violation count increases"""
        filter_service = ProfanityDetectionFilter()

        filter_service.check_message("That's stupid", user_id=3001)
        count1 = filter_service.get_user_violation_count(3001)

        filter_service.check_message("This is dumb", user_id=3001)
        count2 = filter_service.get_user_violation_count(3001)

        assert count2 > count1
        assert count2 == 2

    def test_different_users_tracked_separately(self):
        """Test that different users are tracked separately"""
        filter_service = ProfanityDetectionFilter()

        filter_service.check_message("Stupid", user_id=4001)
        filter_service.check_message("Stupid", user_id=4001)
        filter_service.check_message("Stupid", user_id=4002)

        count_user1 = filter_service.get_user_violation_count(4001)
        count_user2 = filter_service.get_user_violation_count(4002)

        assert count_user1 == 2
        assert count_user2 == 1

    def test_reset_violations(self):
        """Test resetting user violations"""
        filter_service = ProfanityDetectionFilter()

        # Create violations
        filter_service.check_message("Stupid", user_id=5001)
        filter_service.check_message("Dumb", user_id=5001)

        assert filter_service.get_user_violation_count(5001) == 2

        # Reset
        filter_service.reset_user_violations(5001)

        assert filter_service.get_user_violation_count(5001) == 0


class TestEducationalResponses:
    """Test educational response messages"""

    def test_mild_response_structure(self):
        """Test mild profanity response structure"""
        filter_service = ProfanityDetectionFilter()
        response = filter_service.get_mild_profanity_response()

        assert len(response) > 0
        assert "respectful" in response.lower() or "nice" in response.lower()

    def test_moderate_response_structure(self):
        """Test moderate profanity response structure"""
        filter_service = ProfanityDetectionFilter()
        response = filter_service.get_moderate_profanity_response()

        assert len(response) > 0
        assert "appropriate" in response.lower() or "respectful" in response.lower()

    def test_severe_response_structure(self):
        """Test severe profanity response structure"""
        filter_service = ProfanityDetectionFilter()
        response = filter_service.get_severe_profanity_response()

        assert len(response) > 0
        assert "appropriate" in response.lower()
        assert "respectful" in response.lower()

    def test_repeated_violation_response(self):
        """Test repeated violation response"""
        filter_service = ProfanityDetectionFilter()
        response = filter_service.get_repeated_violation_response()

        assert len(response) > 0
        assert "respectful" in response.lower()

    def test_repeated_mild_response(self):
        """Test repeated mild violation response"""
        filter_service = ProfanityDetectionFilter()
        response = filter_service.get_repeated_mild_response()

        assert len(response) > 0


class TestEducationalAlternatives:
    """Test educational alternative suggestions"""

    def test_mild_alternatives(self):
        """Test alternatives for mild profanity"""
        alternatives = get_educational_alternatives("mild")

        assert len(alternatives) > 0
        assert any("instead" in alt.lower() for alt in alternatives)

    def test_moderate_alternatives(self):
        """Test alternatives for moderate profanity"""
        alternatives = get_educational_alternatives("moderate")

        assert len(alternatives) > 0

    def test_severe_alternatives(self):
        """Test alternatives for severe profanity"""
        alternatives = get_educational_alternatives("severe")

        assert len(alternatives) > 0

    def test_invalid_severity_alternatives(self):
        """Test alternatives for invalid severity"""
        alternatives = get_educational_alternatives("invalid")

        assert isinstance(alternatives, list)


class TestParentNotification:
    """Test parent notification logic"""

    def test_notify_for_severe(self):
        """Test that severe profanity triggers parent notification"""
        assert should_notify_parent("severe", 1) is True

    def test_notify_for_repeated_moderate(self):
        """Test that repeated moderate profanity triggers notification"""
        assert should_notify_parent("moderate", 3) is True
        assert should_notify_parent("moderate", 5) is True

    def test_no_notify_for_single_moderate(self):
        """Test that single moderate doesn't trigger notification"""
        assert should_notify_parent("moderate", 1) is False
        assert should_notify_parent("moderate", 2) is False

    def test_notify_for_many_mild(self):
        """Test that many mild violations trigger notification"""
        assert should_notify_parent("mild", 10) is True
        assert should_notify_parent("mild", 15) is True

    def test_no_notify_for_few_mild(self):
        """Test that few mild violations don't trigger notification"""
        assert should_notify_parent("mild", 1) is False
        assert should_notify_parent("mild", 5) is False


class TestContextAnalysis:
    """Test context analysis functionality"""

    def test_analyze_question(self):
        """Test analyzing question context"""
        filter_service = ProfanityDetectionFilter()
        analysis = filter_service.analyze_context("What the hell?")

        assert analysis["is_question"] is True

    def test_analyze_exclamation(self):
        """Test analyzing exclamation context"""
        filter_service = ProfanityDetectionFilter()
        analysis = filter_service.analyze_context("Damn it!")

        assert analysis["is_exclamation"] is True

    def test_profanity_ratio(self):
        """Test profanity ratio calculation"""
        filter_service = ProfanityDetectionFilter()

        # High ratio
        heavy = filter_service.analyze_context("fuck shit damn")
        assert heavy["profanity_ratio"] > 0.5

        # Low ratio
        light = filter_service.analyze_context("This is a stupid thing to say honestly")
        assert light["profanity_ratio"] < 0.5

    def test_context_type_classification(self):
        """Test context type classification"""
        filter_service = ProfanityDetectionFilter()

        # Heavily profane
        heavy = filter_service.analyze_context("fuck shit damn")
        assert heavy["context_type"] == "heavily_profane"

        # Outburst (single word profanity has ratio 1.0, so it's heavily_profane)
        outburst = filter_service.analyze_context("Damn!")
        assert outburst["context_type"] in ["outburst", "casual_usage", "heavily_profane"]


class TestFilterStats:
    """Test filter statistics"""

    def test_stats_structure(self):
        """Test that stats returns correct structure"""
        stats = get_filter_stats()

        assert "enabled" in stats
        assert "total_words" in stats
        assert "mild_words" in stats
        assert "moderate_words" in stats
        assert "severe_words" in stats
        assert "active_users_tracked" in stats
        assert "total_violations_tracked" in stats

    def test_stats_values(self):
        """Test that stats values are reasonable"""
        stats = get_filter_stats()

        assert stats["total_words"] > 0
        assert stats["mild_words"] > 0
        assert stats["moderate_words"] > 0
        assert stats["severe_words"] > 0
        assert stats["active_users_tracked"] >= 0
        assert stats["total_violations_tracked"] >= 0

    def test_stats_track_violations(self):
        """Test that stats track violations"""
        filter_service = ProfanityDetectionFilter()

        # Create some violations
        filter_service.check_message("Stupid", user_id=6001)
        filter_service.check_message("Dumb", user_id=6001)
        filter_service.check_message("Idiot", user_id=6002)

        stats = filter_service.get_filter_stats()

        assert stats["active_users_tracked"] >= 2
        assert stats["total_violations_tracked"] >= 3


class TestConvenienceFunctions:
    """Test convenience wrapper functions"""

    def test_check_message_convenience(self):
        """Test check_message convenience function"""
        result = check_message("This is stupid")

        assert "contains_profanity" in result
        assert result["contains_profanity"] is True

    def test_reset_violations_convenience(self):
        """Test reset_user_violations convenience function"""
        # Create violation
        check_message("Stupid", user_id=7001)

        # Reset
        reset_user_violations(7001)

        # Should be 0
        count = get_user_violation_count(7001)
        assert count == 0

    def test_get_violation_count_convenience(self):
        """Test get_user_violation_count convenience function"""
        check_message("Stupid", user_id=8001)
        check_message("Dumb", user_id=8001)

        count = get_user_violation_count(8001)
        assert count == 2

    def test_convenience_matches_class_methods(self):
        """Test that convenience functions match class methods"""
        filter_service = ProfanityDetectionFilter()

        message = "This is stupid"
        conv_result = check_message(message)
        class_result = filter_service.check_message(message)

        # Should have same structure
        assert conv_result["contains_profanity"] == class_result["contains_profanity"]
        assert conv_result["highest_severity"] == class_result["highest_severity"]


class TestEdgeCases:
    """Test edge cases"""

    def test_empty_message(self):
        """Test with empty message"""
        result = check_message("")

        assert result["contains_profanity"] is False
        assert result["allow_message"] is True

    def test_very_long_message(self):
        """Test with very long message"""
        long_message = "hello " * 1000 + "stupid" + " world" * 1000

        result = check_message(long_message)

        assert result["contains_profanity"] is True

    def test_unicode_message(self):
        """Test with unicode characters"""
        result = check_message("This is stupid 你好")

        assert result["contains_profanity"] is True

    def test_special_characters(self):
        """Test with special characters"""
        result = check_message("@#$% stupid &*()")

        assert result["contains_profanity"] is True

    def test_mixed_case(self):
        """Test with mixed case profanity"""
        result = check_message("That's STUPID")

        assert result["contains_profanity"] is True


class TestRepeatedViolations:
    """Test repeated violation handling"""

    def test_mild_escalation(self):
        """Test that many mild violations trigger reminder"""
        filter_service = ProfanityDetectionFilter()

        # Create 5 mild violations
        for i in range(5):
            filter_service.check_message("That's stupid", user_id=9001)

        # 6th should trigger reminder
        result = filter_service.check_message("That's dumb", user_id=9001)

        assert result["action"] == "gentle_reminder"
        assert result["allow_message"] is True

    def test_moderate_escalation(self):
        """Test that moderate violations escalate"""
        filter_service = ProfanityDetectionFilter()

        # First two are allowed with education (using actual moderate words)
        result1 = filter_service.check_message("You're such an ass", user_id=9002)
        result2 = filter_service.check_message("That really sucks", user_id=9002)

        assert result1["allow_message"] is True
        assert result2["allow_message"] is True

        # Third should block
        result3 = filter_service.check_message("This is pissed me off", user_id=9002)

        assert result3["action"] == "warn_and_limit"
        assert result3["allow_message"] is False


class TestIntegration:
    """Test integration scenarios"""

    def test_full_workflow_mild(self):
        """Test full workflow with mild profanity"""
        message = "That's so stupid"
        result = check_message(message, user_id=10001)

        # Should detect
        assert result["contains_profanity"] is True

        # Should be mild
        assert result["highest_severity"] == "mild"

        # Should allow with education
        assert result["allow_message"] is True
        assert len(result["response_message"]) > 0

        # Should censor
        assert "***" in result["censored_message"]

        # Should not notify parent on first offense
        should_notify = should_notify_parent(
            result["highest_severity"],
            get_user_violation_count(10001)
        )
        assert should_notify is False

    def test_full_workflow_severe(self):
        """Test full workflow with severe profanity"""
        message = "This is fucking stupid"
        result = check_message(message, user_id=10002)

        # Should detect
        assert result["contains_profanity"] is True

        # Should be severe
        assert result["highest_severity"] == "severe"

        # Should block
        assert result["allow_message"] is False
        assert len(result["response_message"]) > 0

        # Should notify parent
        should_notify = should_notify_parent(
            result["highest_severity"],
            get_user_violation_count(10002)
        )
        assert should_notify is True

    def test_progression_from_mild_to_severe(self):
        """Test progression from mild to severe profanity"""
        filter_service = ProfanityDetectionFilter()
        user_id = 10003

        # Start with mild
        mild_result = filter_service.check_message("That's stupid", user_id=user_id)
        assert mild_result["allow_message"] is True

        # Escalate to moderate
        mod_result = filter_service.check_message("You're such an ass", user_id=user_id)
        assert mod_result["allow_message"] is True

        # Severe blocks immediately
        severe_result = filter_service.check_message("This is shit", user_id=user_id)
        assert severe_result["allow_message"] is False
