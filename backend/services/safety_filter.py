"""
Safety Filter Service
Comprehensive content filtering and crisis detection for chatbot safety

Integrates multiple specialized services:
- CrisisKeywordList: Comprehensive crisis keyword detection (suicide, self-harm, abuse)
- ProfanityWordList: Comprehensive profanity word database
- ProfanityDetectionFilter: Profanity detection with educational responses
- InappropriateRequestDetector: Pattern-based inappropriate request detection
- BullyingKeywordList: Comprehensive bullying detection (physical, verbal, social, cyber)
- SeverityScorer: Centralized severity scoring and classification
"""

from typing import Dict, List, Optional
import logging
from datetime import datetime

from sqlalchemy.orm import Session
from models.safety import SafetyFlag
from utils.config import settings

# Import specialized safety services
from services.crisis_keyword_list import crisis_keyword_list
from services.profanity_word_list import profanity_word_list
from services.profanity_detection_filter import ProfanityDetectionFilter
from services.inappropriate_request_detector import inappropriate_request_detector
from services.bullying_keyword_list import bullying_keyword_list
from services.severity_scorer import severity_scorer

logger = logging.getLogger("chatbot.safety_filter")


class SafetyFilter:
    """
    Safety Filter - Comprehensive safety orchestration layer

    Architecture:
    This is the main safety orchestration layer that coordinates all safety checks.
    It integrates multiple specialized services to provide comprehensive protection:

    1. Crisis Detection (HIGHEST PRIORITY - CRITICAL)
       - Suicide, self-harm, and abuse keywords via CrisisKeywordList service
       - Categorized detection: suicide, self_harm, abuse_physical, abuse_emotional, abuse_sexual
       - Immediate crisis response with resources (988, Crisis Text Line, Childhelp)

    2. Inappropriate Request Detection (MEDIUM to CRITICAL)
       - Violence, sexual content, illegal activities
       - Manipulation attempts, safety bypass attempts
       - Uses pattern matching with context awareness

    3. Profanity Detection (LOW to SEVERE)
       - Multi-level severity (mild, moderate, severe)
       - Educational responses with escalation
       - Violation tracking per user

    4. Bullying Detection (MEDIUM)
       - Bullying indicators in user messages
       - Supportive responses with resources

    All checks are logged to database for parent monitoring and safety analytics.
    """

    def __init__(self):
        """Initialize SafetyFilter with all specialized services"""

        # Initialize specialized services
        self.crisis_detector = crisis_keyword_list
        self.profanity_filter = ProfanityDetectionFilter()
        self.inappropriate_detector = inappropriate_request_detector
        self.word_list = profanity_word_list
        self.bullying_detector = bullying_keyword_list
        self.severity_scorer = severity_scorer

        logger.info("SafetyFilter initialized with all specialized services")

    def check_message(
        self, message: str, user_id: Optional[int] = None
    ) -> Dict:
        """
        Comprehensive safety check integrating all services

        This is the main orchestration method that runs all safety checks
        in priority order and combines results.

        Args:
            message: The message to check
            user_id: Optional user ID for violation tracking

        Returns:
            Dictionary with comprehensive safety check results:
            {
                'safe': bool,                    # Overall safety status
                'flags': List[str],              # All flag types found
                'severity': str,                 # Highest severity: 'none', 'low', 'medium', 'high', 'critical'
                'action': str,                   # Recommended action
                'original_message': str,         # Original message text
                'response_message': str,         # Recommended response to user
                'notify_parent': bool,           # Whether to notify parent
                'details': Dict,                 # Detailed results from each service
            }

        Check Priority (highest to lowest):
        1. Crisis keywords (suicide, self-harm, abuse) -> CRITICAL
        2. Inappropriate requests (violence, sexual, illegal) -> MEDIUM to CRITICAL
        3. Profanity -> LOW to SEVERE
        4. Bullying -> MEDIUM
        """
        if not settings.ENABLE_SAFETY_FILTER:
            # Safety filter disabled (not recommended!)
            return {
                "safe": True,
                "flags": [],
                "severity": "none",
                "action": "allow",
                "original_message": message,
                "response_message": "",
                "notify_parent": False,
                "details": {},
            }

        flags = []
        severity = "none"
        action = "allow"
        response_message = ""
        details = {}

        message_lower = message.lower()

        # ============================================================
        # PRIORITY 1: Crisis Detection (CRITICAL - HIGHEST PRIORITY)
        # ============================================================
        # Check for crisis keywords using specialized detector
        if self.crisis_detector.contains_crisis_keywords(message):
            crisis_keywords_found = self.crisis_detector.find_crisis_keywords(message)
            crisis_category = self.crisis_detector.get_category(message)
            all_categories = self.crisis_detector.get_all_categories(message)

            # Determine which flag to use based on category
            if crisis_category in ["suicide", "self_harm"]:
                flags.append("crisis")
                response_message = self.get_crisis_response()
            elif crisis_category in ["abuse_physical", "abuse_emotional", "abuse_sexual"]:
                flags.append("abuse")
                response_message = self.get_abuse_response()
            else:
                # Fallback (shouldn't happen)
                flags.append("crisis")
                response_message = self.get_crisis_response()

            # Score severity using SeverityScorer
            severity = self.severity_scorer.score_crisis_detection(crisis_category)
            action = self.severity_scorer.get_action_recommendation(severity)
            details["crisis"] = {
                "detected": True,
                "primary_category": crisis_category,
                "all_categories": all_categories,
                "keywords_found": crisis_keywords_found,
            }

        # ============================================================
        # PRIORITY 2: Inappropriate Request Detection (MEDIUM to CRITICAL)
        # ============================================================
        else:
            # Check for inappropriate requests using specialized detector
            inappropriate_result = self.inappropriate_detector.check_message(message)
            details["inappropriate_request"] = inappropriate_result

            if inappropriate_result["is_inappropriate"]:
                flags.append("inappropriate_request")
                # Score severity using SeverityScorer
                detector_severity = inappropriate_result["severity"]
                detector_categories = inappropriate_result.get("categories", [])
                severity = self.severity_scorer.score_inappropriate_request(
                    detector_severity, detector_categories
                )
                action = self.severity_scorer.get_action_recommendation(severity)
                response_message = inappropriate_result["response_message"]

            # ============================================================
            # PRIORITY 3: Profanity Detection (LOW to SEVERE)
            # ============================================================
            # Only check profanity if no inappropriate request found
            if not flags:
                profanity_result = self.profanity_filter.check_message(
                    message, user_id
                )
                details["profanity"] = profanity_result

                if profanity_result["contains_profanity"]:
                    flags.append("profanity")
                    # Score severity using SeverityScorer
                    profanity_severity = profanity_result["highest_severity"]
                    violation_count = self.profanity_filter.user_violations.get(user_id, 1) if user_id else 1
                    severity = self.severity_scorer.score_profanity_detection(
                        profanity_severity, violation_count
                    )
                    action = profanity_result["action"]
                    response_message = profanity_result["response_message"]

            # ============================================================
            # PRIORITY 4: Bullying Detection (MEDIUM)
            # ============================================================
            # Check for bullying if no other issues found
            if not flags and self.bullying_detector.contains_bullying_keywords(message):
                bullying_keywords_found = self.bullying_detector.find_bullying_keywords(message)
                bullying_category = self.bullying_detector.get_category(message)
                all_bullying_categories = self.bullying_detector.get_all_categories(message)

                flags.append("bullying")
                # Score severity using SeverityScorer
                severity = self.severity_scorer.score_bullying_detection(
                    bullying_category, len(all_bullying_categories)
                )
                action = self.severity_scorer.get_action_recommendation(severity)
                response_message = self.get_bullying_response()
                details["bullying"] = {
                    "detected": True,
                    "primary_category": bullying_category,
                    "all_categories": all_bullying_categories,
                    "keywords_found": bullying_keywords_found,
                }

        # Determine if message is safe (allow through) using SeverityScorer
        safe = self.severity_scorer.is_safe_message(severity)

        # Determine if parent should be notified using SeverityScorer
        notify_parent = self.severity_scorer.should_notify_parent(severity)

        return {
            "safe": safe,
            "flags": flags,
            "severity": severity,
            "action": action,
            "original_message": message,
            "response_message": response_message,
            "notify_parent": notify_parent,
            "details": details,
        }

    def get_crisis_response(self) -> str:
        """
        Get the crisis response message for self-harm/suicide

        Returns:
            Crisis response text with resources
        """
        return """I'm really worried about what you just said, and I want to help. What you're feeling is really important, but I'm not able to help with something this serious.

Please talk to a trusted adult right away - like your parents, a teacher, or school counselor. They care about you and can really help.

If you need to talk to someone right now:
- National Suicide Prevention Lifeline: 988 (call or text)
- Crisis Text Line: Text HOME to 741741

You matter, and there are people who want to help you feel better. Please reach out to them. 💙"""

    def get_abuse_response(self) -> str:
        """
        Get the abuse response message

        Returns:
            Abuse response text with resources
        """
        return """I'm really concerned about what you just told me. What you described sounds serious, and I want to make sure you're safe.

Please talk to a trusted adult right away - this could be:
- A parent or family member you trust
- A teacher or school counselor
- A coach or mentor

If you're not sure who to talk to or if you're in immediate danger:
- Call 911 if you're in danger right now
- Childhelp National Child Abuse Hotline: 1-800-422-4453 (available 24/7)

What you told me is important, and there are people who can help keep you safe. Please reach out to them. 💙"""

    def get_bullying_response(self, user_name: str = "friend") -> str:
        """
        Get supportive response for bullying

        Args:
            user_name: User's name for personalization

        Returns:
            Supportive response text
        """
        return f"""I'm really sorry you're dealing with that, {user_name}. Bullying is never okay, and what you're feeling is completely valid.

Here's what might help:
1. Talk to a trusted adult (parent, teacher, school counselor) - they can help stop this
2. Try to stay with friends who make you feel good
3. Remember that bullies often have their own problems - this isn't about you

You deserve to feel safe and respected. Please talk to an adult who can help make this better. I'm here to listen, but they can actually help change things. 💙"""

    def get_inappropriate_decline(self) -> str:
        """
        Get polite decline for inappropriate requests

        Returns:
            Polite decline message
        """
        return """I can't help with that - it wouldn't be good for either of us!

How about we talk about something more fun instead? I'd love to hear about your interests, help with homework, or just chat about your day. What sounds good to you?"""

    def log_safety_event(
        self, db: Session, user_id: int, check_result: Dict, message_id: Optional[int] = None
    ) -> SafetyFlag:
        """
        Log a safety event to the database

        Args:
            db: Database session
            user_id: User ID
            check_result: Result from check_message()
            message_id: Optional message ID

        Returns:
            Created SafetyFlag object
        """
        # Get content snippet (first 100 chars)
        content_snippet = check_result["original_message"][:100]

        # Create safety flag
        flag = SafetyFlag(
            user_id=user_id,
            message_id=message_id,
            flag_type=",".join(check_result["flags"]) if check_result["flags"] else "none",
            severity=check_result["severity"],
            content_snippet=content_snippet,
            action_taken=check_result["action"],
            timestamp=datetime.now(),
            parent_notified=False,  # Will be updated if parent is notified
        )

        db.add(flag)
        db.commit()
        db.refresh(flag)

        if settings.LOG_SAFETY_EVENTS:
            logger.info(
                f"Safety event logged: user={user_id}, "
                f"severity={flag.severity}, flags={flag.flag_type}"
            )

        return flag

    def should_notify_parent(self, severity: str) -> bool:
        """
        Determine if parent should be notified

        Args:
            severity: Severity level

        Returns:
            True if parent should be notified
        """
        # Delegate to SeverityScorer for consistent logic
        return self.severity_scorer.should_notify_parent(severity)

    def get_service_stats(self) -> Dict:
        """
        Get statistics from all integrated services

        Returns:
            Dictionary with stats from each service
        """
        stats = {
            "crisis_keyword_list": self.crisis_detector.get_stats(),
            "profanity_word_list": self.word_list.get_stats(),
            "profanity_filter": self.profanity_filter.get_filter_stats(),
            "inappropriate_detector": self.inappropriate_detector.get_stats(),
            "bullying_keyword_list": self.bullying_detector.get_stats(),
            "severity_scorer": self.severity_scorer.get_stats(),
        }
        return stats

    def reset_user_violations(self, user_id: int) -> None:
        """
        Reset violation tracking for a user

        Args:
            user_id: User ID to reset
        """
        self.profanity_filter.reset_user_violations(user_id)
        logger.info(f"Reset violation tracking for user {user_id}")


# Global instance
safety_filter = SafetyFilter()


# Convenience functions
def check_message(message: str, user_id: Optional[int] = None) -> Dict:
    """
    Check a message for safety concerns

    Args:
        message: Message to check
        user_id: Optional user ID for violation tracking

    Returns:
        Comprehensive safety check result dictionary
    """
    return safety_filter.check_message(message, user_id)


def get_crisis_response() -> str:
    """Get crisis response message"""
    return safety_filter.get_crisis_response()


def get_bullying_response(user_name: str = "friend") -> str:
    """Get bullying support response"""
    return safety_filter.get_bullying_response(user_name)


def log_safety_event(
    db: Session, user_id: int, check_result: Dict, message_id: Optional[int] = None
) -> SafetyFlag:
    """Log a safety event"""
    return safety_filter.log_safety_event(db, user_id, check_result, message_id)


def get_abuse_response() -> str:
    """Get abuse response message"""
    return safety_filter.get_abuse_response()


def get_service_stats() -> Dict:
    """Get statistics from all integrated services"""
    return safety_filter.get_service_stats()


def reset_user_violations(user_id: int) -> None:
    """Reset violation tracking for a user"""
    return safety_filter.reset_user_violations(user_id)
