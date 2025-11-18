"""
Severity Scorer Service
Centralized severity scoring and classification for safety filter

This service provides consistent severity determination across all safety checks.
"""

from typing import Dict, List, Optional
from enum import IntEnum
import logging

logger = logging.getLogger("chatbot.severity_scorer")


class SeverityLevel(IntEnum):
    """
    Severity levels with numeric scores for comparison

    Lower numbers = less severe, Higher numbers = more severe
    """
    NONE = 0      # No issues detected
    LOW = 1       # Minor issues (mild profanity)
    MEDIUM = 2    # Moderate issues (bullying, moderate profanity, medium inappropriate requests)
    HIGH = 3      # Serious issues (severe profanity, high-severity inappropriate requests)
    CRITICAL = 4  # Immediate concern (crisis, abuse, critical inappropriate requests)


class SeverityScorer:
    """
    Severity Scorer - Centralized severity scoring and classification

    Features:
    - Consistent severity levels across all safety checks
    - Numeric scoring for easy comparison
    - Parent notification thresholds
    - Message blocking thresholds
    - Severity combination logic
    - Human-readable descriptions

    Severity Levels:
    - NONE (0): No safety concerns
    - LOW (1): Minor profanity, educational opportunity
    - MEDIUM (2): Bullying, moderate profanity, medium inappropriate requests
    - HIGH (3): Severe profanity, high-severity inappropriate requests
    - CRITICAL (4): Crisis, abuse, critical safety concerns
    """

    def __init__(self):
        """Initialize SeverityScorer"""

        # Severity level mapping
        self.severity_levels = {
            "none": SeverityLevel.NONE,
            "low": SeverityLevel.LOW,
            "medium": SeverityLevel.MEDIUM,
            "high": SeverityLevel.HIGH,
            "critical": SeverityLevel.CRITICAL,
        }

        # Reverse mapping
        self.level_names = {
            SeverityLevel.NONE: "none",
            SeverityLevel.LOW: "low",
            SeverityLevel.MEDIUM: "medium",
            SeverityLevel.HIGH: "high",
            SeverityLevel.CRITICAL: "critical",
        }

        # Severity descriptions
        self.descriptions = {
            "none": "No safety concerns detected",
            "low": "Minor issue - educational opportunity",
            "medium": "Moderate concern - supportive response needed",
            "high": "Serious issue - immediate intervention required",
            "critical": "Critical safety concern - emergency response required",
        }

        # Parent notification threshold (notify for HIGH and CRITICAL)
        self.parent_notification_threshold = SeverityLevel.HIGH

        # Message blocking threshold (block for HIGH and CRITICAL)
        self.message_blocking_threshold = SeverityLevel.HIGH

        logger.info("SeverityScorer initialized")

    def get_severity_score(self, severity: str) -> int:
        """
        Get numeric score for a severity level

        Args:
            severity: Severity level string ('none', 'low', 'medium', 'high', 'critical')

        Returns:
            Numeric severity score (0-4)
        """
        severity_lower = severity.lower()
        if severity_lower not in self.severity_levels:
            logger.warning(f"Unknown severity level: {severity}, defaulting to NONE")
            return SeverityLevel.NONE

        return self.severity_levels[severity_lower]

    def get_severity_name(self, score: int) -> str:
        """
        Get severity name from numeric score

        Args:
            score: Numeric severity score (0-4)

        Returns:
            Severity level string ('none', 'low', 'medium', 'high', 'critical')
        """
        if score not in self.level_names:
            logger.warning(f"Unknown severity score: {score}, defaulting to none")
            return "none"

        return self.level_names[score]

    def get_highest_severity(self, severities: List[str]) -> str:
        """
        Get the highest severity from a list of severities

        Args:
            severities: List of severity strings

        Returns:
            Highest severity level string
        """
        if not severities:
            return "none"

        # Convert to scores, find max, convert back to name
        scores = [self.get_severity_score(s) for s in severities]
        max_score = max(scores)
        return self.get_severity_name(max_score)

    def should_notify_parent(self, severity: str) -> bool:
        """
        Determine if parent should be notified based on severity

        Args:
            severity: Severity level string

        Returns:
            True if parent should be notified
        """
        score = self.get_severity_score(severity)
        return score >= self.parent_notification_threshold

    def should_block_message(self, severity: str) -> bool:
        """
        Determine if message should be blocked based on severity

        Args:
            severity: Severity level string

        Returns:
            True if message should be blocked
        """
        score = self.get_severity_score(severity)
        return score >= self.message_blocking_threshold

    def get_description(self, severity: str) -> str:
        """
        Get human-readable description of severity level

        Args:
            severity: Severity level string

        Returns:
            Description of the severity level
        """
        severity_lower = severity.lower()
        if severity_lower not in self.descriptions:
            return "Unknown severity level"

        return self.descriptions[severity_lower]

    def score_crisis_detection(self, crisis_category: str) -> str:
        """
        Score crisis detection results

        Args:
            crisis_category: Crisis category from CrisisKeywordList
                           (suicide, self_harm, abuse_physical, abuse_emotional, abuse_sexual)

        Returns:
            Severity level string (always 'critical' for crisis)
        """
        # All crisis categories are CRITICAL
        return "critical"

    def score_profanity_detection(self, profanity_severity: str, violation_count: int = 1) -> str:
        """
        Score profanity detection results

        Args:
            profanity_severity: Profanity severity from ProfanityDetectionFilter
                              (mild, moderate, severe)
            violation_count: Number of violations by user (for escalation)

        Returns:
            Severity level string
        """
        profanity_lower = profanity_severity.lower()

        if profanity_lower == "severe":
            # Severe profanity is always HIGH
            return "high"
        elif profanity_lower == "moderate":
            # Moderate profanity is MEDIUM, but escalates to HIGH after 3 violations
            if violation_count >= 3:
                return "high"
            return "medium"
        elif profanity_lower == "mild":
            # Mild profanity is LOW
            return "low"
        else:
            return "none"

    def score_inappropriate_request(self, request_severity: str, categories: List[str]) -> str:
        """
        Score inappropriate request detection results

        Args:
            request_severity: Severity from InappropriateRequestDetector
                            (medium, high, critical)
            categories: Categories detected (violence, sexual, illegal, etc.)

        Returns:
            Severity level string
        """
        severity_lower = request_severity.lower()

        # Map detector severities to our severity levels
        if severity_lower == "critical":
            return "critical"
        elif severity_lower == "high":
            return "high"
        elif severity_lower == "medium":
            return "medium"
        else:
            return "none"

    def score_bullying_detection(self, bullying_category: str, categories_count: int = 1) -> str:
        """
        Score bullying detection results

        Args:
            bullying_category: Primary bullying category from BullyingKeywordList
            categories_count: Number of bullying categories detected

        Returns:
            Severity level string (always 'medium' for bullying)
        """
        # All bullying is MEDIUM severity
        # Even if multiple categories, still MEDIUM (supportive, not blocking)
        return "medium"

    def combine_severities(self, severity_scores: Dict[str, str]) -> Dict[str, any]:
        """
        Combine multiple severity scores from different detectors

        Args:
            severity_scores: Dictionary mapping detector name to severity
                           e.g., {'crisis': 'critical', 'profanity': 'low'}

        Returns:
            Dictionary with combined results:
            {
                'overall_severity': str,     # Highest severity detected
                'severities': Dict[str, str], # Input severities
                'notify_parent': bool,        # Whether to notify parent
                'block_message': bool,        # Whether to block message
                'description': str,           # Description of overall severity
            }
        """
        # Get highest severity
        severities = list(severity_scores.values())
        overall_severity = self.get_highest_severity(severities)

        return {
            "overall_severity": overall_severity,
            "severities": severity_scores,
            "notify_parent": self.should_notify_parent(overall_severity),
            "block_message": self.should_block_message(overall_severity),
            "description": self.get_description(overall_severity),
        }

    def get_action_recommendation(self, severity: str) -> str:
        """
        Get recommended action based on severity

        Args:
            severity: Severity level string

        Returns:
            Recommended action string
        """
        severity_lower = severity.lower()

        action_map = {
            "none": "allow",
            "low": "filter_and_educate",
            "medium": "supportive_response",
            "high": "block_with_education",
            "critical": "crisis_response",
        }

        return action_map.get(severity_lower, "allow")

    def is_safe_message(self, severity: str) -> bool:
        """
        Determine if message is safe (can be allowed through)

        Args:
            severity: Severity level string

        Returns:
            True if message is safe, False if it should be blocked
        """
        # Safe if severity is LOW or MEDIUM (educational/supportive)
        # Not safe if HIGH or CRITICAL (blocking required)
        score = self.get_severity_score(severity)
        return score < self.message_blocking_threshold

    def get_stats(self) -> Dict:
        """
        Get statistics about severity scoring

        Returns:
            Dictionary with severity scoring configuration
        """
        return {
            "severity_levels": list(self.severity_levels.keys()),
            "parent_notification_threshold": self.get_severity_name(
                self.parent_notification_threshold
            ),
            "message_blocking_threshold": self.get_severity_name(
                self.message_blocking_threshold
            ),
            "total_levels": len(self.severity_levels),
        }


# Global instance
severity_scorer = SeverityScorer()


# Convenience functions
def get_severity_score(severity: str) -> int:
    """Get numeric score for severity level"""
    return severity_scorer.get_severity_score(severity)


def get_severity_name(score: int) -> str:
    """Get severity name from numeric score"""
    return severity_scorer.get_severity_name(score)


def get_highest_severity(severities: List[str]) -> str:
    """Get highest severity from list"""
    return severity_scorer.get_highest_severity(severities)


def should_notify_parent(severity: str) -> bool:
    """Determine if parent should be notified"""
    return severity_scorer.should_notify_parent(severity)


def should_block_message(severity: str) -> bool:
    """Determine if message should be blocked"""
    return severity_scorer.should_block_message(severity)


def get_description(severity: str) -> str:
    """Get human-readable description of severity"""
    return severity_scorer.get_description(severity)


def score_crisis_detection(crisis_category: str) -> str:
    """Score crisis detection results"""
    return severity_scorer.score_crisis_detection(crisis_category)


def score_profanity_detection(profanity_severity: str, violation_count: int = 1) -> str:
    """Score profanity detection results"""
    return severity_scorer.score_profanity_detection(profanity_severity, violation_count)


def score_inappropriate_request(request_severity: str, categories: List[str]) -> str:
    """Score inappropriate request detection results"""
    return severity_scorer.score_inappropriate_request(request_severity, categories)


def score_bullying_detection(bullying_category: str, categories_count: int = 1) -> str:
    """Score bullying detection results"""
    return severity_scorer.score_bullying_detection(bullying_category, categories_count)


def combine_severities(severity_scores: Dict[str, str]) -> Dict:
    """Combine multiple severity scores"""
    return severity_scorer.combine_severities(severity_scores)


def get_action_recommendation(severity: str) -> str:
    """Get recommended action based on severity"""
    return severity_scorer.get_action_recommendation(severity)


def is_safe_message(severity: str) -> bool:
    """Determine if message is safe"""
    return severity_scorer.is_safe_message(severity)


def get_stats() -> Dict:
    """Get severity scoring statistics"""
    return severity_scorer.get_stats()
