"""
Tests for SeverityScorer - Severity scoring and classification service
Tests comprehensive severity determination across all safety categories
"""

import pytest
from services.severity_scorer import SeverityScorer, SeverityLevel, severity_scorer


class TestSeverityLevelEnum:
    """Test SeverityLevel enum"""

    def test_severity_levels_values(self):
        """Test that severity levels have correct numeric values"""
        assert SeverityLevel.NONE == 0
        assert SeverityLevel.LOW == 1
        assert SeverityLevel.MEDIUM == 2
        assert SeverityLevel.HIGH == 3
        assert SeverityLevel.CRITICAL == 4

    def test_severity_levels_comparable(self):
        """Test that severity levels can be compared"""
        assert SeverityLevel.LOW < SeverityLevel.MEDIUM
        assert SeverityLevel.MEDIUM < SeverityLevel.HIGH
        assert SeverityLevel.HIGH < SeverityLevel.CRITICAL
        assert SeverityLevel.CRITICAL > SeverityLevel.NONE


class TestSeverityScorerBasics:
    """Test basic functionality of SeverityScorer"""

    def setup_method(self):
        """Set up test fixtures"""
        self.scorer = SeverityScorer()

    def test_initialization(self):
        """Test that SeverityScorer initializes correctly"""
        assert len(self.scorer.severity_levels) == 5
        assert len(self.scorer.level_names) == 5
        assert len(self.scorer.descriptions) == 5
        assert self.scorer.parent_notification_threshold == SeverityLevel.HIGH
        assert self.scorer.message_blocking_threshold == SeverityLevel.HIGH

    def test_get_severity_score(self):
        """Test getting numeric score from severity name"""
        assert self.scorer.get_severity_score("none") == 0
        assert self.scorer.get_severity_score("low") == 1
        assert self.scorer.get_severity_score("medium") == 2
        assert self.scorer.get_severity_score("high") == 3
        assert self.scorer.get_severity_score("critical") == 4

    def test_get_severity_score_case_insensitive(self):
        """Test that severity score is case insensitive"""
        assert self.scorer.get_severity_score("NONE") == 0
        assert self.scorer.get_severity_score("Low") == 1
        assert self.scorer.get_severity_score("MEDIUM") == 2
        assert self.scorer.get_severity_score("HiGh") == 3
        assert self.scorer.get_severity_score("CRITICAL") == 4

    def test_get_severity_score_unknown(self):
        """Test that unknown severity defaults to NONE"""
        assert self.scorer.get_severity_score("unknown") == 0
        assert self.scorer.get_severity_score("invalid") == 0

    def test_get_severity_name(self):
        """Test getting severity name from numeric score"""
        assert self.scorer.get_severity_name(0) == "none"
        assert self.scorer.get_severity_name(1) == "low"
        assert self.scorer.get_severity_name(2) == "medium"
        assert self.scorer.get_severity_name(3) == "high"
        assert self.scorer.get_severity_name(4) == "critical"

    def test_get_severity_name_invalid(self):
        """Test that invalid score defaults to none"""
        assert self.scorer.get_severity_name(5) == "none"
        assert self.scorer.get_severity_name(-1) == "none"


class TestGetHighestSeverity:
    """Test getting highest severity from list"""

    def setup_method(self):
        """Set up test fixtures"""
        self.scorer = SeverityScorer()

    def test_empty_list(self):
        """Test with empty list"""
        assert self.scorer.get_highest_severity([]) == "none"

    def test_single_severity(self):
        """Test with single severity"""
        assert self.scorer.get_highest_severity(["low"]) == "low"
        assert self.scorer.get_highest_severity(["critical"]) == "critical"

    def test_multiple_severities(self):
        """Test with multiple severities"""
        assert self.scorer.get_highest_severity(["low", "medium"]) == "medium"
        assert self.scorer.get_highest_severity(["low", "medium", "high"]) == "high"
        assert self.scorer.get_highest_severity(["low", "critical", "medium"]) == "critical"

    def test_duplicate_severities(self):
        """Test with duplicate severities"""
        assert self.scorer.get_highest_severity(["low", "low", "low"]) == "low"
        assert self.scorer.get_highest_severity(["medium", "low", "medium"]) == "medium"

    def test_with_none(self):
        """Test with none included"""
        assert self.scorer.get_highest_severity(["none", "low"]) == "low"
        assert self.scorer.get_highest_severity(["none", "none"]) == "none"


class TestParentNotification:
    """Test parent notification logic"""

    def setup_method(self):
        """Set up test fixtures"""
        self.scorer = SeverityScorer()

    def test_should_notify_parent(self):
        """Test parent notification for different severities"""
        # Should NOT notify for low severity
        assert self.scorer.should_notify_parent("none") is False
        assert self.scorer.should_notify_parent("low") is False
        assert self.scorer.should_notify_parent("medium") is False

        # SHOULD notify for high and critical
        assert self.scorer.should_notify_parent("high") is True
        assert self.scorer.should_notify_parent("critical") is True


class TestMessageBlocking:
    """Test message blocking logic"""

    def setup_method(self):
        """Set up test fixtures"""
        self.scorer = SeverityScorer()

    def test_should_block_message(self):
        """Test message blocking for different severities"""
        # Should NOT block for low and medium severity
        assert self.scorer.should_block_message("none") is False
        assert self.scorer.should_block_message("low") is False
        assert self.scorer.should_block_message("medium") is False

        # SHOULD block for high and critical
        assert self.scorer.should_block_message("high") is True
        assert self.scorer.should_block_message("critical") is True

    def test_is_safe_message(self):
        """Test message safety determination"""
        # Safe if LOW or MEDIUM (educational/supportive)
        assert self.scorer.is_safe_message("none") is True
        assert self.scorer.is_safe_message("low") is True
        assert self.scorer.is_safe_message("medium") is True

        # NOT safe if HIGH or CRITICAL (requires blocking)
        assert self.scorer.is_safe_message("high") is False
        assert self.scorer.is_safe_message("critical") is False


class TestDescriptions:
    """Test severity descriptions"""

    def setup_method(self):
        """Set up test fixtures"""
        self.scorer = SeverityScorer()

    def test_get_description(self):
        """Test getting descriptions for all severities"""
        assert len(self.scorer.get_description("none")) > 0
        assert len(self.scorer.get_description("low")) > 0
        assert len(self.scorer.get_description("medium")) > 0
        assert len(self.scorer.get_description("high")) > 0
        assert len(self.scorer.get_description("critical")) > 0

    def test_description_content(self):
        """Test that descriptions are appropriate"""
        assert "concern" in self.scorer.get_description("none").lower()
        assert "educational" in self.scorer.get_description("low").lower()
        assert "supportive" in self.scorer.get_description("medium").lower()
        assert "serious" in self.scorer.get_description("high").lower()
        assert "critical" in self.scorer.get_description("critical").lower()

    def test_unknown_description(self):
        """Test description for unknown severity"""
        assert self.scorer.get_description("unknown") == "Unknown severity level"


class TestCrisisDetectionScoring:
    """Test crisis detection severity scoring"""

    def setup_method(self):
        """Set up test fixtures"""
        self.scorer = SeverityScorer()

    def test_score_crisis_detection(self):
        """Test that all crisis categories score as critical"""
        crisis_categories = [
            "suicide",
            "self_harm",
            "abuse_physical",
            "abuse_emotional",
            "abuse_sexual",
        ]

        for category in crisis_categories:
            assert self.scorer.score_crisis_detection(category) == "critical"


class TestProfanityDetectionScoring:
    """Test profanity detection severity scoring"""

    def setup_method(self):
        """Set up test fixtures"""
        self.scorer = SeverityScorer()

    def test_severe_profanity(self):
        """Test that severe profanity always scores high"""
        assert self.scorer.score_profanity_detection("severe") == "high"
        assert self.scorer.score_profanity_detection("severe", 1) == "high"
        assert self.scorer.score_profanity_detection("severe", 10) == "high"

    def test_moderate_profanity(self):
        """Test moderate profanity scoring"""
        # First violation is MEDIUM
        assert self.scorer.score_profanity_detection("moderate", 1) == "medium"
        assert self.scorer.score_profanity_detection("moderate", 2) == "medium"

        # After 3 violations, escalates to HIGH
        assert self.scorer.score_profanity_detection("moderate", 3) == "high"
        assert self.scorer.score_profanity_detection("moderate", 5) == "high"

    def test_mild_profanity(self):
        """Test that mild profanity always scores low"""
        assert self.scorer.score_profanity_detection("mild") == "low"
        assert self.scorer.score_profanity_detection("mild", 1) == "low"
        assert self.scorer.score_profanity_detection("mild", 10) == "low"

    def test_no_profanity(self):
        """Test no profanity scoring"""
        assert self.scorer.score_profanity_detection("none") == "none"
        assert self.scorer.score_profanity_detection("") == "none"


class TestInappropriateRequestScoring:
    """Test inappropriate request severity scoring"""

    def setup_method(self):
        """Set up test fixtures"""
        self.scorer = SeverityScorer()

    def test_critical_requests(self):
        """Test critical severity requests"""
        assert self.scorer.score_inappropriate_request("critical", ["sexual"]) == "critical"
        assert self.scorer.score_inappropriate_request("critical", ["violence"]) == "critical"

    def test_high_requests(self):
        """Test high severity requests"""
        assert self.scorer.score_inappropriate_request("high", ["violence"]) == "high"
        assert self.scorer.score_inappropriate_request("high", ["illegal"]) == "high"

    def test_medium_requests(self):
        """Test medium severity requests"""
        assert self.scorer.score_inappropriate_request("medium", ["manipulation"]) == "medium"
        assert self.scorer.score_inappropriate_request("medium", []) == "medium"

    def test_no_requests(self):
        """Test no inappropriate request"""
        assert self.scorer.score_inappropriate_request("none", []) == "none"


class TestBullyingDetectionScoring:
    """Test bullying detection severity scoring"""

    def setup_method(self):
        """Set up test fixtures"""
        self.scorer = SeverityScorer()

    def test_single_category_bullying(self):
        """Test bullying with single category"""
        assert self.scorer.score_bullying_detection("physical_bullying", 1) == "medium"
        assert self.scorer.score_bullying_detection("verbal_bullying", 1) == "medium"
        assert self.scorer.score_bullying_detection("social_exclusion", 1) == "medium"

    def test_multiple_category_bullying(self):
        """Test bullying with multiple categories"""
        # Even multiple categories still MEDIUM (supportive, not blocking)
        assert self.scorer.score_bullying_detection("physical_bullying", 3) == "medium"
        assert self.scorer.score_bullying_detection("verbal_bullying", 5) == "medium"


class TestCombineSeverities:
    """Test combining multiple severity scores"""

    def setup_method(self):
        """Set up test fixtures"""
        self.scorer = SeverityScorer()

    def test_single_detector(self):
        """Test combining with single detector"""
        result = self.scorer.combine_severities({"profanity": "low"})

        assert result["overall_severity"] == "low"
        assert result["severities"] == {"profanity": "low"}
        assert result["notify_parent"] is False
        assert result["block_message"] is False
        assert len(result["description"]) > 0

    def test_multiple_detectors(self):
        """Test combining multiple detectors"""
        result = self.scorer.combine_severities({
            "profanity": "low",
            "bullying": "medium",
        })

        assert result["overall_severity"] == "medium"
        assert result["notify_parent"] is False
        assert result["block_message"] is False

    def test_critical_overrides_all(self):
        """Test that critical severity overrides all others"""
        result = self.scorer.combine_severities({
            "crisis": "critical",
            "profanity": "low",
            "bullying": "medium",
        })

        assert result["overall_severity"] == "critical"
        assert result["notify_parent"] is True
        assert result["block_message"] is True

    def test_high_overrides_medium_low(self):
        """Test that high severity overrides medium and low"""
        result = self.scorer.combine_severities({
            "inappropriate_request": "high",
            "profanity": "low",
            "bullying": "medium",
        })

        assert result["overall_severity"] == "high"
        assert result["notify_parent"] is True
        assert result["block_message"] is True


class TestActionRecommendations:
    """Test action recommendations"""

    def setup_method(self):
        """Set up test fixtures"""
        self.scorer = SeverityScorer()

    def test_action_recommendations(self):
        """Test action recommendations for all severities"""
        assert self.scorer.get_action_recommendation("none") == "allow"
        assert self.scorer.get_action_recommendation("low") == "filter_and_educate"
        assert self.scorer.get_action_recommendation("medium") == "supportive_response"
        assert self.scorer.get_action_recommendation("high") == "block_with_education"
        assert self.scorer.get_action_recommendation("critical") == "crisis_response"

    def test_unknown_action(self):
        """Test action for unknown severity"""
        assert self.scorer.get_action_recommendation("unknown") == "allow"


class TestGetStats:
    """Test get_stats method"""

    def setup_method(self):
        """Set up test fixtures"""
        self.scorer = SeverityScorer()

    def test_get_stats(self):
        """Test getting stats"""
        stats = self.scorer.get_stats()

        assert "severity_levels" in stats
        assert "parent_notification_threshold" in stats
        assert "message_blocking_threshold" in stats
        assert "total_levels" in stats

        assert len(stats["severity_levels"]) == 5
        assert stats["parent_notification_threshold"] == "high"
        assert stats["message_blocking_threshold"] == "high"
        assert stats["total_levels"] == 5


class TestConvenienceFunctions:
    """Test module-level convenience functions"""

    def test_get_severity_score_function(self):
        """Test convenience function for get_severity_score"""
        from services.severity_scorer import get_severity_score

        assert get_severity_score("low") == 1
        assert get_severity_score("critical") == 4

    def test_get_severity_name_function(self):
        """Test convenience function for get_severity_name"""
        from services.severity_scorer import get_severity_name

        assert get_severity_name(1) == "low"
        assert get_severity_name(4) == "critical"

    def test_get_highest_severity_function(self):
        """Test convenience function for get_highest_severity"""
        from services.severity_scorer import get_highest_severity

        assert get_highest_severity(["low", "medium"]) == "medium"
        assert get_highest_severity(["low", "critical", "medium"]) == "critical"

    def test_should_notify_parent_function(self):
        """Test convenience function for should_notify_parent"""
        from services.severity_scorer import should_notify_parent

        assert should_notify_parent("low") is False
        assert should_notify_parent("high") is True

    def test_should_block_message_function(self):
        """Test convenience function for should_block_message"""
        from services.severity_scorer import should_block_message

        assert should_block_message("medium") is False
        assert should_block_message("high") is True

    def test_get_description_function(self):
        """Test convenience function for get_description"""
        from services.severity_scorer import get_description

        desc = get_description("low")
        assert len(desc) > 0

    def test_score_crisis_detection_function(self):
        """Test convenience function for score_crisis_detection"""
        from services.severity_scorer import score_crisis_detection

        assert score_crisis_detection("suicide") == "critical"

    def test_score_profanity_detection_function(self):
        """Test convenience function for score_profanity_detection"""
        from services.severity_scorer import score_profanity_detection

        assert score_profanity_detection("severe") == "high"

    def test_score_inappropriate_request_function(self):
        """Test convenience function for score_inappropriate_request"""
        from services.severity_scorer import score_inappropriate_request

        assert score_inappropriate_request("high", ["violence"]) == "high"

    def test_score_bullying_detection_function(self):
        """Test convenience function for score_bullying_detection"""
        from services.severity_scorer import score_bullying_detection

        assert score_bullying_detection("physical_bullying") == "medium"

    def test_combine_severities_function(self):
        """Test convenience function for combine_severities"""
        from services.severity_scorer import combine_severities

        result = combine_severities({"profanity": "low"})
        assert result["overall_severity"] == "low"

    def test_get_action_recommendation_function(self):
        """Test convenience function for get_action_recommendation"""
        from services.severity_scorer import get_action_recommendation

        assert get_action_recommendation("low") == "filter_and_educate"

    def test_is_safe_message_function(self):
        """Test convenience function for is_safe_message"""
        from services.severity_scorer import is_safe_message

        assert is_safe_message("low") is True
        assert is_safe_message("high") is False

    def test_get_stats_function(self):
        """Test convenience function for get_stats"""
        from services.severity_scorer import get_stats

        stats = get_stats()
        assert "severity_levels" in stats


class TestEdgeCases:
    """Test edge cases"""

    def setup_method(self):
        """Set up test fixtures"""
        self.scorer = SeverityScorer()

    def test_empty_string_severity(self):
        """Test empty string severity"""
        assert self.scorer.get_severity_score("") == 0
        assert self.scorer.get_description("") == "Unknown severity level"

    def test_whitespace_severity(self):
        """Test whitespace severity"""
        assert self.scorer.get_severity_score("  ") == 0

    def test_case_variations(self):
        """Test various case variations"""
        test_cases = ["LOW", "Low", "low", "lOw", "LoW"]
        for case in test_cases:
            assert self.scorer.get_severity_score(case) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
