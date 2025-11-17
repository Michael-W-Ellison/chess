"""
Profanity Detection Filter Service
Comprehensive profanity detection and educational response system
"""

from typing import Dict, List, Optional
import logging
from datetime import datetime

from services.profanity_word_list import profanity_word_list
from utils.config import settings

logger = logging.getLogger("chatbot.profanity_detection_filter")


class ProfanityDetectionFilter:
    """
    Profanity Detection Filter - Detects and handles profanity appropriately

    Features:
    - Multi-level severity detection (mild, moderate, severe)
    - Contextual analysis
    - Educational responses
    - Age-appropriate handling
    - Detailed reporting

    Designed for educational chatbot for kids 8-14.
    """

    def __init__(self):
        self.word_list = profanity_word_list
        self.enabled = getattr(settings, "ENABLE_PROFANITY_FILTER", True)

        # Track consecutive violations for escalation
        self.user_violations = {}  # user_id -> count

        logger.info("Profanity detection filter initialized")

    def check_message(self, message: str, user_id: Optional[int] = None) -> Dict:
        """
        Check a message for profanity

        Args:
            message: Message text to check
            user_id: Optional user ID for tracking violations

        Returns:
            Dictionary with detection results:
            {
                'contains_profanity': bool,
                'profanity_words': List[Dict],  # [{word, severity}]
                'highest_severity': str,         # 'mild', 'moderate', 'severe', 'none'
                'censored_message': str,         # Message with profanity censored
                'action': str,                   # Recommended action
                'response_message': str,         # Educational response
                'allow_message': bool,           # Whether to allow message through
            }
        """
        if not self.enabled:
            return {
                "contains_profanity": False,
                "profanity_words": [],
                "highest_severity": "none",
                "censored_message": message,
                "action": "allow",
                "response_message": "",
                "allow_message": True,
            }

        # Find all profanity in message
        profanity_words = self.word_list.find_profanity_words(message)

        if not profanity_words:
            # No profanity found
            return {
                "contains_profanity": False,
                "profanity_words": [],
                "highest_severity": "none",
                "censored_message": message,
                "action": "allow",
                "response_message": "",
                "allow_message": True,
            }

        # Determine highest severity
        severity_order = {"mild": 1, "moderate": 2, "severe": 3}
        highest_severity = max(
            profanity_words, key=lambda x: severity_order.get(x["severity"], 0)
        )["severity"]

        # Censor the message
        censored_message = self.word_list.censor_text(message)

        # Track violations if user_id provided
        if user_id is not None:
            self.user_violations[user_id] = self.user_violations.get(user_id, 0) + 1
            violation_count = self.user_violations[user_id]
        else:
            violation_count = 1

        # Determine action and response based on severity and violation count
        action, response_message, allow = self._determine_response(
            highest_severity, profanity_words, violation_count
        )

        return {
            "contains_profanity": True,
            "profanity_words": profanity_words,
            "highest_severity": highest_severity,
            "censored_message": censored_message,
            "action": action,
            "response_message": response_message,
            "allow_message": allow,
        }

    def _determine_response(
        self, severity: str, profanity_words: List[Dict], violation_count: int
    ) -> tuple:
        """
        Determine appropriate response based on severity and violation count

        Args:
            severity: Highest severity found
            profanity_words: List of profanity words found
            violation_count: Number of violations by this user

        Returns:
            Tuple of (action, response_message, allow_message)
        """
        if severity == "severe":
            # Severe profanity - block and educate
            return (
                "block_and_educate",
                self.get_severe_profanity_response(),
                False,
            )

        elif severity == "moderate":
            if violation_count >= 3:
                # Multiple moderate violations - escalate
                return (
                    "warn_and_limit",
                    self.get_repeated_violation_response(),
                    False,
                )
            else:
                # First/second moderate violation - educate
                return (
                    "educate",
                    self.get_moderate_profanity_response(),
                    True,  # Allow but educate
                )

        elif severity == "mild":
            if violation_count >= 5:
                # Many mild violations - gentle reminder
                return (
                    "gentle_reminder",
                    self.get_repeated_mild_response(),
                    True,
                )
            else:
                # Mild violation - gentle education
                return (
                    "gentle_educate",
                    self.get_mild_profanity_response(),
                    True,
                )

        # Default - allow
        return ("allow", "", True)

    def get_mild_profanity_response(self) -> str:
        """
        Get response for mild profanity

        Returns:
            Educational response message
        """
        return """I noticed you used some words that aren't very nice. Let's try to use more respectful language together!

Instead of words like "stupid" or "dumb," we can say things like:
- "I disagree with that"
- "That's confusing"
- "I don't understand"

Using kind words helps everyone feel respected. What did you want to talk about?"""

    def get_moderate_profanity_response(self) -> str:
        """
        Get response for moderate profanity

        Returns:
            Educational response message
        """
        return """Whoa, let's pause for a second. Those words aren't appropriate for our conversations.

I know sometimes we get frustrated or upset, but using respectful language is really important. It helps create a safe space for both of us!

If you're feeling frustrated or angry, I'm here to listen. Want to tell me what's bothering you in a different way?"""

    def get_severe_profanity_response(self) -> str:
        """
        Get response for severe profanity

        Returns:
            Educational response message
        """
        return """I can't respond to messages with that kind of language. Those words aren't appropriate for anyone to use, especially in our conversations.

I'm here to help and support you, but I need you to use respectful language. If you're feeling really upset or frustrated, I understand - but let's talk about it in a way that's respectful to both of us.

Can you rephrase what you wanted to say using more appropriate words?"""

    def get_repeated_violation_response(self) -> str:
        """
        Get response for repeated violations

        Returns:
            Escalated response message
        """
        return """I've noticed you've been using inappropriate language a few times now. This is really important:

Using respectful language is a key part of having good conversations. When we use inappropriate words repeatedly, it makes it hard to have meaningful discussions.

I really want to help you and be here for you, but I need you to commit to using respectful language. Can we make a fresh start and focus on using kind, appropriate words?

If you're feeling frustrated or having a tough time, I genuinely want to hear about it - just in a respectful way. Sound good?"""

    def get_repeated_mild_response(self) -> str:
        """
        Get response for repeated mild violations

        Returns:
            Gentle reminder message
        """
        return """Hey, I've noticed you're using words like "stupid" or "dumb" pretty often. Let's work on using more positive language together!

Words matter, and using kind, respectful language makes our conversations better. Instead of putting things down, let's focus on what we think or feel:
- "I don't like that"
- "That's confusing to me"
- "I disagree because..."

I know you can do this! What's on your mind?"""

    def analyze_context(self, message: str) -> Dict:
        """
        Analyze the context around profanity usage

        Args:
            message: Message text

        Returns:
            Dictionary with context analysis
        """
        analysis = {
            "is_question": "?" in message,
            "is_exclamation": "!" in message,
            "word_count": len(message.split()),
            "profanity_ratio": 0.0,
            "context_type": "neutral",
        }

        # Calculate profanity ratio
        words = message.split()
        if len(words) > 0:
            profanity_count = len(self.word_list.find_profanity_words(message))
            analysis["profanity_ratio"] = profanity_count / len(words)

        # Determine context type
        if analysis["profanity_ratio"] > 0.5:
            analysis["context_type"] = "heavily_profane"
        elif analysis["profanity_ratio"] > 0.2:
            analysis["context_type"] = "moderately_profane"
        elif analysis["is_exclamation"] and analysis["word_count"] < 5:
            analysis["context_type"] = "outburst"
        else:
            analysis["context_type"] = "casual_usage"

        return analysis

    def get_educational_alternatives(self, severity: str) -> List[str]:
        """
        Get educational alternatives for profanity

        Args:
            severity: Severity level

        Returns:
            List of alternative phrases
        """
        alternatives = {
            "mild": [
                "Instead of 'stupid': try 'I don't understand' or 'That doesn't make sense to me'",
                "Instead of 'dumb': try 'I disagree' or 'I see it differently'",
                "Instead of 'shut up': try 'I'd like to share my thoughts' or 'Can I speak?'",
                "Instead of 'idiot': try 'I think they made a mistake' or 'That wasn't a good choice'",
            ],
            "moderate": [
                "Express frustration: 'I'm really frustrated about this'",
                "Show disagreement: 'I completely disagree with that'",
                "Share feelings: 'That makes me feel upset'",
                "Be direct: 'I don't like how that went'",
            ],
            "severe": [
                "Use appropriate language to express strong feelings",
                "Take a moment to calm down before responding",
                "Talk to a trusted adult if you're really upset",
                "Remember: words have impact, choose them carefully",
            ],
        }

        return alternatives.get(severity, [])

    def reset_user_violations(self, user_id: int):
        """
        Reset violation count for a user

        Args:
            user_id: User ID
        """
        if user_id in self.user_violations:
            del self.user_violations[user_id]
            logger.info(f"Reset profanity violations for user {user_id}")

    def get_user_violation_count(self, user_id: int) -> int:
        """
        Get violation count for a user

        Args:
            user_id: User ID

        Returns:
            Number of violations
        """
        return self.user_violations.get(user_id, 0)

    def should_notify_parent(self, severity: str, violation_count: int) -> bool:
        """
        Determine if parent should be notified

        Args:
            severity: Severity level
            violation_count: Number of violations

        Returns:
            True if parent should be notified
        """
        # Notify parent for severe profanity or repeated moderate violations
        if severity == "severe":
            return True
        elif severity == "moderate" and violation_count >= 3:
            return True
        elif violation_count >= 10:  # Many mild violations
            return True

        return False

    def get_filter_stats(self) -> Dict:
        """
        Get filter statistics

        Returns:
            Dictionary with filter stats
        """
        word_list_stats = self.word_list.get_stats()

        return {
            "enabled": self.enabled,
            "total_words": word_list_stats["total"],
            "mild_words": word_list_stats["mild"],
            "moderate_words": word_list_stats["moderate"],
            "severe_words": word_list_stats["severe"],
            "active_users_tracked": len(self.user_violations),
            "total_violations_tracked": sum(self.user_violations.values()),
        }


# Global instance
profanity_detection_filter = ProfanityDetectionFilter()


# Convenience functions
def check_message(message: str, user_id: Optional[int] = None) -> Dict:
    """
    Check a message for profanity

    Args:
        message: Message text
        user_id: Optional user ID

    Returns:
        Detection result dictionary
    """
    return profanity_detection_filter.check_message(message, user_id)


def get_educational_alternatives(severity: str) -> List[str]:
    """Get educational alternatives for profanity"""
    return profanity_detection_filter.get_educational_alternatives(severity)


def reset_user_violations(user_id: int):
    """Reset violation count for user"""
    profanity_detection_filter.reset_user_violations(user_id)


def get_user_violation_count(user_id: int) -> int:
    """Get violation count for user"""
    return profanity_detection_filter.get_user_violation_count(user_id)


def should_notify_parent(severity: str, violation_count: int) -> bool:
    """Determine if parent should be notified"""
    return profanity_detection_filter.should_notify_parent(severity, violation_count)


def get_filter_stats() -> Dict:
    """Get filter statistics"""
    return profanity_detection_filter.get_filter_stats()
