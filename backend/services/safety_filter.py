"""
Safety Filter Service
Content filtering and crisis detection for chatbot safety
"""

from typing import Dict, List, Optional
import logging
from datetime import datetime

from sqlalchemy.orm import Session
from models.safety import SafetyFlag
from utils.config import settings

logger = logging.getLogger("chatbot.safety_filter")


class SafetyFilter:
    """
    Safety Filter - detects and handles concerning content

    Monitors for:
    - Profanity
    - Crisis keywords (self-harm, suicide)
    - Bullying indicators
    - Abuse indicators
    - Inappropriate requests

    Returns structured safety check results with recommended actions.
    """

    def __init__(self):
        # Crisis keywords (CRITICAL severity)
        self.crisis_keywords = [
            "kill myself",
            "suicide",
            "want to die",
            "self harm",
            "self-harm",
            "cut myself",
            "hurt myself",
            "end it all",
            "better off dead",
            "no reason to live",
        ]

        # Bullying keywords (MEDIUM severity)
        self.bullying_keywords = [
            "bully",
            "bullied",
            "bullying",
            "teasing me",
            "making fun of me",
            "spreading rumors",
            "left me out",
            "exclude",
            "ignoring me",
            "nobody likes me",
        ]

        # Abuse keywords (CRITICAL severity)
        self.abuse_keywords = [
            "hit me",
            "hits me",
            "hurt me",
            "hurts me",
            "touched me inappropriately",
            "makes me scared",
            "threatens me",
            "afraid of",
            "won't let me",
        ]

        # Inappropriate request patterns (MEDIUM severity)
        self.inappropriate_patterns = [
            "how to hack",
            "how to steal",
            "how to cheat",
            "give me bad words",
            "tell me swear words",
            "how to hurt",
            "how to fight",
            "how to skip school",
        ]

        # Basic profanity list (LOW severity)
        # Note: In production, use a more comprehensive library like better-profanity
        self.profanity_list = [
            "damn",
            "hell",
            "crap",
            "stupid",
            "dumb",
            "idiot",
            "shut up",
            # Add more as needed, but keep age-appropriate focus
        ]

        # Load better-profanity if available
        try:
            from better_profanity import profanity

            profanity.load_censor_words()
            self.use_better_profanity = True
            logger.info("Using better-profanity for content filtering")
        except ImportError:
            self.use_better_profanity = False
            logger.info("better-profanity not available, using basic filter")

    def check_message(self, message: str) -> Dict:
        """
        Check a message for safety concerns

        Args:
            message: The message to check

        Returns:
            Dictionary with safety check results:
            {
                'safe': bool,
                'flags': List[str],  # List of flag types
                'severity': str,      # 'low', 'medium', 'high', 'critical'
                'action': str,        # Recommended action
                'original_message': str
            }
        """
        if not settings.ENABLE_SAFETY_FILTER:
            # Safety filter disabled (not recommended!)
            return {
                "safe": True,
                "flags": [],
                "severity": "none",
                "action": "allow",
                "original_message": message,
            }

        flags = []
        severity = "none"
        action = "allow"

        message_lower = message.lower()

        # Check for crisis keywords (HIGHEST PRIORITY)
        if self._contains_any(message_lower, self.crisis_keywords):
            flags.append("crisis")
            severity = "critical"
            action = "crisis_response"

        # Check for abuse keywords (CRITICAL)
        elif self._contains_any(message_lower, self.abuse_keywords):
            flags.append("abuse")
            severity = "critical"
            action = "crisis_response"

        # Check for bullying (MEDIUM)
        elif self._contains_any(message_lower, self.bullying_keywords):
            flags.append("bullying")
            severity = "medium"
            action = "supportive_response"

        # Check for inappropriate requests (MEDIUM)
        elif self._contains_any(message_lower, self.inappropriate_patterns):
            flags.append("inappropriate_request")
            severity = "medium"
            action = "polite_decline"

        # Check for profanity (LOW)
        elif self._check_profanity(message):
            flags.append("profanity")
            severity = "low"
            action = "filter_and_educate"

        # Determine if message is safe
        safe = severity not in ["critical", "high"]

        return {
            "safe": safe,
            "flags": flags,
            "severity": severity,
            "action": action,
            "original_message": message,
        }

    def _contains_any(self, text: str, keywords: List[str]) -> bool:
        """Check if text contains any of the keywords"""
        return any(keyword in text for keyword in keywords)

    def _check_profanity(self, text: str) -> bool:
        """Check for profanity using better-profanity or basic list"""
        if self.use_better_profanity:
            from better_profanity import profanity

            return profanity.contains_profanity(text)
        else:
            # Basic check
            text_lower = text.lower()
            return any(word in text_lower for word in self.profanity_list)

    def get_crisis_response(self) -> str:
        """
        Get the crisis response message

        Returns:
            Crisis response text with resources
        """
        return """I'm really worried about what you just said, and I want to help. What you're feeling is really important, but I'm not able to help with something this serious.

Please talk to a trusted adult right away - like your parents, a teacher, or school counselor. They care about you and can really help.

If you need to talk to someone right now:
- National Suicide Prevention Lifeline: 988 (call or text)
- Crisis Text Line: Text HOME to 741741

You matter, and there are people who want to help you feel better. Please reach out to them. 💙"""

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
        # Notify parent for critical and high severity events
        return severity in ["critical", "high"]


# Global instance
safety_filter = SafetyFilter()


# Convenience functions
def check_message(message: str) -> Dict:
    """
    Check a message for safety concerns

    Args:
        message: Message to check

    Returns:
        Safety check result dictionary
    """
    return safety_filter.check_message(message)


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
