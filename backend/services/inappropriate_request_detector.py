"""
Inappropriate Request Detector Service
Comprehensive detection of inappropriate requests for kid-friendly chatbot
"""

from typing import Dict, List, Optional
import logging
import re

logger = logging.getLogger("chatbot.inappropriate_request_detector")


class InappropriateRequestDetector:
    """
    Inappropriate Request Detector - Detects and handles inappropriate requests

    Features:
    - Multi-category detection (violence, sexual, illegal, manipulation, etc.)
    - Pattern matching with context awareness
    - Age-appropriate educational responses
    - Severity classification
    - Detailed reporting

    Designed for educational chatbot for kids 8-14.
    """

    def __init__(self):
        # VIOLENCE patterns (HIGH severity)
        self.violence_patterns = [
            # Physical harm
            r"\bhow to.{0,30}(hurt|harm|attack|fight|beat|punch|kick|hit)\b",
            r"\bhow to make (someone|people) (hurt|bleed|suffer)\b",
            r"\bways to (hurt|harm|attack|injure)\b",
            r"\bhow to.{0,20}(kill|murder)\b",
            r"\bweapon(s)? (to|for)\b",
            r"\bmake (a |an )?(bomb|weapon|knife|gun)\b",

            # School violence
            r"\battack (school|students|teacher)\b",
            r"\bbring (weapon|gun|knife) to school\b",
            r"\bshoot up\b",

            # Animal cruelty
            r"\bhow to (hurt|kill|torture) (animals?|pets?|dogs?|cats?)\b",
            r"\bmake (animals?|pets?) (suffer|hurt)\b",
        ]

        # SEXUAL patterns (CRITICAL severity)
        self.sexual_patterns = [
            # Sexual content requests
            r"\bshow me (naked|nude|sex)\b",
            r"\btell me about (sex|porn|pornography)\b",
            r"\bhow to (have sex|make out)\b",
            r"\b(naked|nude) (pictures?|photos?|images?)\b",
            r"\bsexual (content|stuff|things)\b",

            # Inappropriate body talk
            r"\btalk about (my|your) (private parts|genitals)\b",
            r"\b(describe|show) (your|my) body\b",

            # Dating manipulation
            r"\bhow to make (someone|them) (like|love|kiss) me\b",
            r"\btricks? to (get|make) (someone|them) (date|like|love)\b",
        ]

        # ILLEGAL ACTIVITIES patterns (HIGH severity)
        self.illegal_patterns = [
            # Theft/stealing
            r"\bhow to.{0,30}(steal|rob|shoplift)\b",
            r"\bways to (steal|rob|shoplift)\b",
            r"\b(steal|shoplift) (from|at)\b",
            r"\btake (money|stuff|things) without\b",

            # Hacking/cyber crime
            r"\bhow to hack\b",
            r"\bhack into (someone|account|computer|phone)\b",
            r"\bget (into|access) someone('s|s)? (account|phone|computer)\b",
            r"\bsteal (password|data|information)\b",

            # Vandalism
            r"\bhow to (vandalize|damage|destroy|break)\b",
            r"\bways to (damage|destroy|ruin)\b",

            # Drugs/alcohol
            r"\bhow to (get|buy|make) (drugs?|alcohol|beer|weed|marijuana)\b",
            r"\bwhere to (buy|get|find) (drugs?|alcohol)\b",

            # School cheating
            r"\bhow to cheat.{0,10}(test|exam|homework|assignment)\b",
            r"\bways to cheat\b",
            r"\bcheat (without|at)\b",
        ]

        # MANIPULATION patterns (MEDIUM severity)
        self.manipulation_patterns = [
            # Lying/deceiving
            r"\bhow to (lie|deceive|trick|fool)\b",
            r"\bways to (lie|deceive|trick|manipulate)\b",
            r"\blie to (parents?|teachers?|adults?)\b",

            # Evading rules
            r"\bhow to (skip|ditch|avoid) (school|class)\b",
            r"\bget out of (school|homework|chores?)\b",
            r"\bavoid (doing|going to)\b",

            # Sneaking
            r"\bsneak out (of|at)\b",
            r"\bhow to (sneak|hide)\b",

            # Getting others in trouble
            r"\bget (someone|them) in trouble\b",
            r"\bmake (someone|them) look bad\b",
            r"\bframe (someone|them) for\b",
        ]

        # BYPASS SAFETY patterns (HIGH severity)
        self.bypass_patterns = [
            # Jailbreak attempts
            r"\bignore.{0,20}(instructions?|rules?|guidelines?)\b",
            r"\bpretend you('re| are).{0,20}(not|without|unrestricted|evil|bad)\b",
            r"\bact like you (don't|dont) have\b",
            r"\bforget.{0,20}(rules?|guidelines?|restrictions?)\b",

            # Role-play manipulation
            r"\bpretend (to be|you('re| are)) (evil|bad|unrestricted)\b",
            r"\bin (this|the) (game|scenario|role-?play)\b.*\b(no rules|anything)\b",

            # Safety filter bypass
            r"\bhow to (bypass|avoid|trick|fool) (filter|safety|detection)\b",
            r"\bget around (the )?(filter|safety|rules)\b",

            # Profanity requests
            r"\b(tell|teach|give|show) me (bad|swear|curse|dirty) words?\b",
            r"\blist of (profanity|swear words?|curse words?)\b",
            r"\bsay (bad|swear|curse) words?\b",
        ]

        # HARMFUL ADVICE patterns (HIGH severity)
        self.harmful_advice_patterns = [
            # Self-harm (detected separately in safety_filter, but included for completeness)
            r"\bhow to (hurt|harm|cut|injure) myself\b",
            r"\bways to (hurt|harm) myself\b",

            # Bullying
            r"\bhow to (bully|tease|make fun of)\b",
            r"\bways to (bully|hurt|upset|embarrass) (someone|them|people)\b",
            r"\bmake (someone|them) (feel bad|cry|upset)\b",

            # Dangerous challenges
            r"\b(dangerous|risky|deadly) (challenge|trend|game)\b",
            r"\bhow to do (the )?\w+ challenge\b.*\b(hurt|dangerous)\b",
        ]

        # PERSONAL INFO REQUESTS patterns (MEDIUM severity)
        self.personal_info_patterns = [
            r"\b(what('s| is)|tell me) your (address|location|phone|number)\b",
            r"\bwhere (do you|are you) (live|located)\b",
            r"\bcan (we|i) meet (in person|irl)\b",
            r"\b(send|share) (your|a) (picture|photo|image)\b",
        ]

        # Compile all patterns
        self._compile_patterns()

        logger.info("Inappropriate request detector initialized")

    def _compile_patterns(self):
        """Compile regex patterns for efficiency"""
        self.violence_compiled = [re.compile(p, re.IGNORECASE) for p in self.violence_patterns]
        self.sexual_compiled = [re.compile(p, re.IGNORECASE) for p in self.sexual_patterns]
        self.illegal_compiled = [re.compile(p, re.IGNORECASE) for p in self.illegal_patterns]
        self.manipulation_compiled = [re.compile(p, re.IGNORECASE) for p in self.manipulation_patterns]
        self.bypass_compiled = [re.compile(p, re.IGNORECASE) for p in self.bypass_patterns]
        self.harmful_advice_compiled = [re.compile(p, re.IGNORECASE) for p in self.harmful_advice_patterns]
        self.personal_info_compiled = [re.compile(p, re.IGNORECASE) for p in self.personal_info_patterns]

    def check_message(self, message: str) -> Dict:
        """
        Check a message for inappropriate requests

        Args:
            message: Message text to check

        Returns:
            Dictionary with detection results:
            {
                'is_inappropriate': bool,
                'categories': List[str],        # Categories detected
                'highest_severity': str,        # 'medium', 'high', 'critical', 'none'
                'matched_patterns': List[str],  # Matched pattern descriptions
                'action': str,                  # Recommended action
                'response_message': str,        # Educational response
                'should_block': bool,           # Whether to block message
            }
        """
        categories = []
        matched_patterns = []
        severity_scores = []

        # Check each category
        if self._matches_patterns(message, self.violence_compiled):
            categories.append("violence")
            matched_patterns.append("violence-related request")
            severity_scores.append(3)  # HIGH

        if self._matches_patterns(message, self.sexual_compiled):
            categories.append("sexual")
            matched_patterns.append("sexual content request")
            severity_scores.append(4)  # CRITICAL

        if self._matches_patterns(message, self.illegal_compiled):
            categories.append("illegal")
            matched_patterns.append("illegal activity request")
            severity_scores.append(3)  # HIGH

        if self._matches_patterns(message, self.manipulation_compiled):
            categories.append("manipulation")
            matched_patterns.append("manipulation/deception request")
            severity_scores.append(2)  # MEDIUM

        if self._matches_patterns(message, self.bypass_compiled):
            categories.append("bypass_safety")
            matched_patterns.append("safety bypass attempt")
            severity_scores.append(3)  # HIGH

        if self._matches_patterns(message, self.harmful_advice_compiled):
            categories.append("harmful_advice")
            matched_patterns.append("harmful advice request")
            severity_scores.append(3)  # HIGH

        if self._matches_patterns(message, self.personal_info_compiled):
            categories.append("personal_info")
            matched_patterns.append("personal information request")
            severity_scores.append(2)  # MEDIUM

        # Determine severity
        if not severity_scores:
            highest_severity = "none"
            severity_level = 0
        else:
            severity_level = max(severity_scores)
            if severity_level >= 4:
                highest_severity = "critical"
            elif severity_level >= 3:
                highest_severity = "high"
            else:
                highest_severity = "medium"

        # Determine action and response
        action, response_message, should_block = self._determine_response(
            categories, highest_severity
        )

        return {
            "is_inappropriate": len(categories) > 0,
            "categories": categories,
            "highest_severity": highest_severity,
            "matched_patterns": matched_patterns,
            "action": action,
            "response_message": response_message,
            "should_block": should_block,
        }

    def _matches_patterns(self, message: str, compiled_patterns: List) -> bool:
        """Check if message matches any pattern in list"""
        return any(pattern.search(message) for pattern in compiled_patterns)

    def _determine_response(
        self, categories: List[str], severity: str
    ) -> tuple:
        """
        Determine appropriate response based on categories and severity

        Args:
            categories: List of detected categories
            severity: Severity level

        Returns:
            Tuple of (action, response_message, should_block)
        """
        if not categories:
            return ("allow", "", False)

        # Critical severity - block and respond strongly
        if severity == "critical":
            return (
                "block_and_educate",
                self.get_critical_response(categories),
                True,
            )

        # High severity - block and educate
        if severity == "high":
            return (
                "block_and_educate",
                self.get_high_severity_response(categories),
                True,
            )

        # Medium severity - educate but may allow
        if severity == "medium":
            return (
                "educate",
                self.get_medium_severity_response(categories),
                False,
            )

        # Default - allow
        return ("allow", "", False)

    def get_critical_response(self, categories: List[str]) -> str:
        """
        Get response for critical severity requests

        Args:
            categories: Detected categories

        Returns:
            Educational response message
        """
        if "sexual" in categories:
            return """I can't help with that kind of request. Those topics aren't appropriate for our conversations, and I'm designed to keep things safe and age-appropriate.

If you have questions about growing up or your body, please talk to a trusted adult like a parent, guardian, or school counselor. They can give you accurate, helpful information in a way that's right for you.

Let's talk about something else! What interests you? I'd love to help with homework, talk about hobbies, or just chat about your day."""

        # Default critical response
        return """I can't help with that request. That's not something I'm able to discuss or help with, and it wouldn't be safe or appropriate.

If you're curious about something or have questions, please talk to a trusted adult like a parent, teacher, or counselor. They can help you in ways I can't.

How about we talk about something more positive? I'm here to help with homework, chat about interests, or just listen to what's on your mind!"""

    def get_high_severity_response(self, categories: List[str]) -> str:
        """
        Get response for high severity requests

        Args:
            categories: Detected categories

        Returns:
            Educational response message
        """
        if "violence" in categories:
            return """I can't help with anything related to hurting people or violence. That's never okay, and it's not what I'm here for.

If you're feeling angry or upset, I understand those feelings are real - but hurting others is never the answer. If you're having trouble with someone or feeling frustrated, please talk to a trusted adult who can help you work through it safely.

Let's focus on something positive instead. Want to talk about what's bothering you, or chat about something fun?"""

        if "illegal" in categories:
            return """I can't help with that - that's asking about something illegal, and it wouldn't be right for either of us!

I know sometimes things might seem fun or exciting, but breaking rules or laws can have serious consequences. If you're curious about something or facing a tough situation, please talk to a trusted adult who can guide you.

How about we talk about something else? I'm happy to help with homework, discuss interests, or just chat!"""

        if "bypass_safety" in categories:
            return """I notice you're trying to get me to ignore my safety guidelines, but that's not going to work - and here's why: my guidelines exist to keep both of us safe and make sure our conversations are helpful and appropriate.

I'm designed to be a helpful, friendly chatbot for kids, and that means staying within certain boundaries. Those boundaries aren't meant to be mean - they're there to protect you!

Let's have a real conversation instead! What would you actually like to talk about or learn about today?"""

        if "harmful_advice" in categories:
            return """I can't and won't help with anything that could hurt you or others. Your safety and the safety of others is really important to me.

If you're thinking about doing something that could be harmful, please stop and talk to a trusted adult right away. They care about you and can help you work through whatever you're dealing with.

I'm here to support you in positive ways. Want to talk about what's going on, or switch to something more fun?"""

        # Default high severity response
        return """I can't help with that request. It's not appropriate, and it's not what I'm designed to help with.

If you have questions or concerns, please talk to a trusted adult like a parent, teacher, or counselor. They can provide the guidance and support you need.

Let's talk about something else! What's something positive we can discuss?"""

    def get_medium_severity_response(self, categories: List[str]) -> str:
        """
        Get response for medium severity requests

        Args:
            categories: Detected categories

        Returns:
            Educational response message
        """
        if "manipulation" in categories:
            return """I can't help with trying to trick, deceive, or manipulate people. Being honest and trustworthy is really important for building good relationships!

I understand that sometimes situations feel tricky, but deception usually makes things worse, not better. If you're facing a difficult situation, let's talk about honest ways to handle it, or you can talk to a trusted adult for advice.

Want to talk about what's really going on, or chat about something else?"""

        if "personal_info" in categories:
            return """I can't share personal information like that - it wouldn't be safe for either of us! Part of staying safe online is keeping personal details private.

Remember: never share personal information (like addresses, phone numbers, or exact locations) with people you meet online, including chatbots like me. It's an important safety rule!

Let's keep our conversation fun and safe! What would you like to talk about instead?"""

        # Default medium severity response
        return """I can't help with that particular request, but I'm happy to chat about lots of other things!

How about we talk about your interests, help with homework, discuss books or movies you like, or just chat about your day? I'm here to be helpful in positive ways!

What sounds good to you?"""

    def get_stats(self) -> Dict:
        """
        Get detector statistics

        Returns:
            Dictionary with detector stats
        """
        return {
            "violence_patterns": len(self.violence_patterns),
            "sexual_patterns": len(self.sexual_patterns),
            "illegal_patterns": len(self.illegal_patterns),
            "manipulation_patterns": len(self.manipulation_patterns),
            "bypass_patterns": len(self.bypass_patterns),
            "harmful_advice_patterns": len(self.harmful_advice_patterns),
            "personal_info_patterns": len(self.personal_info_patterns),
            "total_patterns": (
                len(self.violence_patterns)
                + len(self.sexual_patterns)
                + len(self.illegal_patterns)
                + len(self.manipulation_patterns)
                + len(self.bypass_patterns)
                + len(self.harmful_advice_patterns)
                + len(self.personal_info_patterns)
            ),
        }

    def should_notify_parent(self, severity: str, categories: List[str]) -> bool:
        """
        Determine if parent should be notified

        Args:
            severity: Severity level
            categories: Detected categories

        Returns:
            True if parent should be notified
        """
        # Notify parent for critical severity
        if severity == "critical":
            return True

        # Notify for high severity
        if severity == "high":
            return True

        # Notify for specific concerning categories even at medium severity
        concerning_categories = {"violence", "sexual", "harmful_advice"}
        if any(cat in concerning_categories for cat in categories):
            return True

        return False


# Global instance
inappropriate_request_detector = InappropriateRequestDetector()


# Convenience functions
def check_message(message: str) -> Dict:
    """
    Check a message for inappropriate requests

    Args:
        message: Message text

    Returns:
        Detection result dictionary
    """
    return inappropriate_request_detector.check_message(message)


def should_notify_parent(severity: str, categories: List[str]) -> bool:
    """Determine if parent should be notified"""
    return inappropriate_request_detector.should_notify_parent(severity, categories)


def get_stats() -> Dict:
    """Get detector statistics"""
    return inappropriate_request_detector.get_stats()
