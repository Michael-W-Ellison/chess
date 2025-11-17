"""
Crisis Keyword List Service
Comprehensive crisis keyword detection for kid-friendly chatbot

This list is designed for children ages 8-14 and focuses on:
- Suicide ideation detection
- Self-harm indicators
- Physical abuse indicators
- Emotional abuse indicators
- Sexual abuse indicators
- Immediate crisis response triggering

All keywords trigger CRITICAL severity responses with crisis resources.
"""

from typing import Dict, List, Set, Tuple
import logging

logger = logging.getLogger("chatbot.crisis_keyword_list")


class CrisisKeywordList:
    """
    Crisis Keyword List - Comprehensive crisis keyword detection

    Categories:
    - SUICIDE: Suicide ideation keywords
    - SELF_HARM: Self-harm indicators
    - ABUSE_PHYSICAL: Physical abuse indicators
    - ABUSE_EMOTIONAL: Emotional abuse indicators
    - ABUSE_SEXUAL: Sexual abuse indicators

    All categories have CRITICAL severity and trigger immediate parent notification.
    """

    def __init__(self):
        # SUICIDE keywords - Suicide ideation and related thoughts
        self.suicide_keywords = {
            # Direct suicide mentions
            "suicide",
            "commit suicide",
            "kill myself",
            "killing myself",

            # Death wishes
            "want to die",
            "wanna die",
            "wish i was dead",
            "wish i were dead",
            "better off dead",
            "everyone would be better off",
            "world would be better without me",

            # Life negation
            "no reason to live",
            "nothing to live for",
            "don't want to be alive",
            "dont want to be alive",
            "don't want to live",
            "dont want to live",
            "tired of living",
            "can't go on",
            "cant go on",

            # Ending thoughts
            "end it all",
            "end my life",
            "ending my life",
            "take my life",
            "taking my life",

            # Hopelessness expressions
            "no point in living",
            "life isn't worth living",
            "life is not worth living",
            "give up on life",
            "ready to die",
        }

        # SELF_HARM keywords - Self-harm indicators
        self.self_harm_keywords = {
            # Cutting
            "cut myself",
            "cutting myself",
            "want to cut myself",
            "wanna cut myself",
            "cut my wrists",
            "cutting my wrists",
            "slice myself",
            "slicing myself",

            # General self-harm
            "hurt myself",
            "hurting myself",
            "harm myself",
            "harming myself",
            "injure myself",
            "injuring myself",

            # Burning
            "burn myself",
            "burning myself",

            # Hitting
            "hit myself",
            "hitting myself",
            "punch myself",
            "punching myself",

            # Specific self-harm methods
            "self harm",
            "self-harm",
            "self injury",
            "self-injury",
            "self mutilation",

            # Pain seeking
            "need to hurt myself",
            "have to hurt myself",
            "want to feel pain",
            "deserve pain",
            "punish myself",
        }

        # ABUSE_PHYSICAL keywords - Physical abuse indicators
        self.abuse_physical_keywords = {
            # Hitting/striking
            "hit me",
            "hits me",
            "hitting me",
            "beat me",
            "beats me",
            "beating me",
            "punch me",
            "punches me",
            "punching me",
            "slap me",
            "slaps me",
            "slapping me",
            "smack me",
            "smacks me",
            "smacking me",

            # Kicking
            "kick me",
            "kicks me",
            "kicking me",

            # Throwing
            "throw me",
            "throws me",
            "threw me",
            "push me",
            "pushes me",
            "shove me",
            "shoves me",

            # Choking/strangling
            "choke me",
            "chokes me",
            "choking me",
            "strangle me",
            "strangles me",

            # General violence
            "hurt me",
            "hurts me",
            "hurting me",
            "harm me",
            "harms me",
            "harming me",

            # Physical restraint
            "locked me in",
            "locks me in",
            "tied me up",
            "ties me up",
            "won't let me leave",
            "wont let me leave",
            "keeps me locked",

            # Results of abuse
            "gave me bruises",
            "gives me bruises",
            "left marks on me",
            "leaves marks on me",
            "made me bleed",
            "makes me bleed",
        }

        # ABUSE_EMOTIONAL keywords - Emotional/psychological abuse indicators
        self.abuse_emotional_keywords = {
            # Threats and fear
            "threatens me",
            "threatening me",
            "makes me scared",
            "makes me afraid",
            "afraid of him",
            "afraid of her",
            "afraid of them",
            "scared of him",
            "scared of her",
            "scared of them",
            "terrified of",

            # Screaming/yelling
            "screams at me",
            "screaming at me",
            "yells at me",
            "yelling at me",
            "shouts at me",
            "shouting at me",

            # Control and isolation
            "won't let me",
            "wont let me",
            "doesn't let me",
            "doesnt let me",
            "won't allow me",
            "wont allow me",
            "controls everything",
            "won't let me see",
            "isolates me",

            # Deprivation
            "won't let me eat",
            "wont let me eat",
            "won't feed me",
            "wont feed me",
            "starves me",
            "starving me",
            "locks me in my room",

            # Verbal abuse
            "calls me names",
            "tells me i'm worthless",
            "tells me im worthless",
            "says i'm stupid",
            "says im stupid",
            "says i'm useless",
            "says im useless",

            # Watching/stalking
            "watches me all the time",
            "follows me everywhere",
            "won't leave me alone",
            "wont leave me alone",
        }

        # ABUSE_SEXUAL keywords - Sexual abuse indicators (age-appropriate detection)
        self.abuse_sexual_keywords = {
            # Inappropriate touching
            "touched me inappropriately",
            "touches me inappropriately",
            "touching me inappropriately",
            "touched my private parts",
            "touches my private parts",
            "touching my private parts",
            "touched me where",
            "touches me where",

            # Unwanted contact
            "made me touch",
            "makes me touch",
            "forced me to touch",
            "forces me to touch",

            # Exposure
            "showed me his",
            "showed me her",
            "shows me his",
            "shows me her",
            "made me look at",
            "makes me look at",

            # General inappropriate behavior
            "does things to me",
            "did things to me",
            "inappropriate things",
            "something bad happened",
            "bad touch",
            "uncomfortable touching",

            # Secret keeping (grooming indicator)
            "said to keep it secret",
            "says to keep it secret",
            "told me not to tell",
            "tells me not to tell",
            "said don't tell anyone",
            "says dont tell anyone",
        }

        # Severity mapping - all crisis keywords are CRITICAL
        self.severity = "critical"

        # Exception words/phrases that might contain keywords but aren't actually crisis situations
        # (e.g., "I don't want to hurt myself" could be someone asking for help preventing it)
        # These are handled by context analysis, not simple exceptions

        logger.info("Crisis keyword list initialized with comprehensive categories")

    def contains_crisis_keywords(self, text: str) -> bool:
        """
        Check if text contains any crisis keywords

        Args:
            text: Text to check

        Returns:
            True if any crisis keyword is found
        """
        text_lower = text.lower()

        # Check all categories
        return (
            self._contains_any(text_lower, self.suicide_keywords)
            or self._contains_any(text_lower, self.self_harm_keywords)
            or self._contains_any(text_lower, self.abuse_physical_keywords)
            or self._contains_any(text_lower, self.abuse_emotional_keywords)
            or self._contains_any(text_lower, self.abuse_sexual_keywords)
        )

    def find_crisis_keywords(self, text: str) -> List[Dict[str, str]]:
        """
        Find all crisis keywords in text with categories

        Args:
            text: Text to search

        Returns:
            List of dictionaries with keyword info:
            [
                {
                    'keyword': str,
                    'category': str,  # 'suicide', 'self_harm', 'abuse_physical', etc.
                    'severity': str,  # Always 'critical'
                }
            ]
        """
        text_lower = text.lower()
        found_keywords = []

        # Check suicide keywords
        for keyword in self.suicide_keywords:
            if keyword in text_lower:
                found_keywords.append({
                    "keyword": keyword,
                    "category": "suicide",
                    "severity": "critical",
                })

        # Check self-harm keywords
        for keyword in self.self_harm_keywords:
            if keyword in text_lower:
                found_keywords.append({
                    "keyword": keyword,
                    "category": "self_harm",
                    "severity": "critical",
                })

        # Check physical abuse keywords
        for keyword in self.abuse_physical_keywords:
            if keyword in text_lower:
                found_keywords.append({
                    "keyword": keyword,
                    "category": "abuse_physical",
                    "severity": "critical",
                })

        # Check emotional abuse keywords
        for keyword in self.abuse_emotional_keywords:
            if keyword in text_lower:
                found_keywords.append({
                    "keyword": keyword,
                    "category": "abuse_emotional",
                    "severity": "critical",
                })

        # Check sexual abuse keywords
        for keyword in self.abuse_sexual_keywords:
            if keyword in text_lower:
                found_keywords.append({
                    "keyword": keyword,
                    "category": "abuse_sexual",
                    "severity": "critical",
                })

        return found_keywords

    def get_category(self, text: str) -> str:
        """
        Get the primary crisis category detected

        Args:
            text: Text to analyze

        Returns:
            Category name: 'suicide', 'self_harm', 'abuse_physical',
            'abuse_emotional', 'abuse_sexual', or 'none'
        """
        text_lower = text.lower()

        # Priority order: suicide > self_harm > abuse (all are critical)
        # This determines which response to show if multiple categories present
        if self._contains_any(text_lower, self.suicide_keywords):
            return "suicide"
        elif self._contains_any(text_lower, self.self_harm_keywords):
            return "self_harm"
        elif self._contains_any(text_lower, self.abuse_sexual_keywords):
            return "abuse_sexual"
        elif self._contains_any(text_lower, self.abuse_physical_keywords):
            return "abuse_physical"
        elif self._contains_any(text_lower, self.abuse_emotional_keywords):
            return "abuse_emotional"
        else:
            return "none"

    def get_all_categories(self, text: str) -> List[str]:
        """
        Get all crisis categories detected in text

        Args:
            text: Text to analyze

        Returns:
            List of category names found
        """
        text_lower = text.lower()
        categories = []

        if self._contains_any(text_lower, self.suicide_keywords):
            categories.append("suicide")
        if self._contains_any(text_lower, self.self_harm_keywords):
            categories.append("self_harm")
        if self._contains_any(text_lower, self.abuse_physical_keywords):
            categories.append("abuse_physical")
        if self._contains_any(text_lower, self.abuse_emotional_keywords):
            categories.append("abuse_emotional")
        if self._contains_any(text_lower, self.abuse_sexual_keywords):
            categories.append("abuse_sexual")

        return categories

    def _contains_any(self, text: str, keywords: Set[str]) -> bool:
        """
        Check if text contains any of the keywords

        Args:
            text: Text to check (should be lowercased)
            keywords: Set of keywords to search for

        Returns:
            True if any keyword is found
        """
        return any(keyword in text for keyword in keywords)

    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about the keyword lists

        Returns:
            Dictionary with counts for each category
        """
        return {
            "suicide_keywords": len(self.suicide_keywords),
            "self_harm_keywords": len(self.self_harm_keywords),
            "abuse_physical_keywords": len(self.abuse_physical_keywords),
            "abuse_emotional_keywords": len(self.abuse_emotional_keywords),
            "abuse_sexual_keywords": len(self.abuse_sexual_keywords),
            "total_keywords": (
                len(self.suicide_keywords)
                + len(self.self_harm_keywords)
                + len(self.abuse_physical_keywords)
                + len(self.abuse_emotional_keywords)
                + len(self.abuse_sexual_keywords)
            ),
        }


# Global instance
crisis_keyword_list = CrisisKeywordList()


# Convenience functions
def contains_crisis_keywords(text: str) -> bool:
    """Check if text contains any crisis keywords"""
    return crisis_keyword_list.contains_crisis_keywords(text)


def find_crisis_keywords(text: str) -> List[Dict[str, str]]:
    """Find all crisis keywords in text"""
    return crisis_keyword_list.find_crisis_keywords(text)


def get_category(text: str) -> str:
    """Get primary crisis category"""
    return crisis_keyword_list.get_category(text)


def get_all_categories(text: str) -> List[str]:
    """Get all crisis categories detected"""
    return crisis_keyword_list.get_all_categories(text)


def get_stats() -> Dict[str, int]:
    """Get keyword list statistics"""
    return crisis_keyword_list.get_stats()
