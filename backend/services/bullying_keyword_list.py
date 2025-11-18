"""
Bullying Keyword List Service
Comprehensive bullying detection for kid-friendly chatbot

This list is designed for children ages 8-14 and focuses on:
- Detecting when children are being bullied
- Identifying different types of bullying (physical, verbal, social, cyber)
- Providing supportive responses and resources
- Age-appropriate detection and support

All keywords have MEDIUM severity and trigger supportive responses.
"""

from typing import Dict, List, Set
import logging

logger = logging.getLogger("chatbot.bullying_keyword_list")


class BullyingKeywordList:
    """
    Bullying Keyword List - Comprehensive bullying detection

    Categories:
    - PHYSICAL_BULLYING: Physical bullying indicators
    - VERBAL_BULLYING: Name-calling, insults, verbal harassment
    - SOCIAL_EXCLUSION: Social isolation, exclusion, rejection
    - CYBERBULLYING: Online harassment indicators
    - THREATS: Threats and intimidation
    - EMOTIONAL_IMPACT: How bullying makes the child feel

    All categories have MEDIUM severity and trigger supportive responses.
    """

    def __init__(self):
        # PHYSICAL_BULLYING - Physical bullying indicators
        self.physical_bullying_keywords = {
            # General physical bullying
            "bully me",
            "bullies me",
            "bullying me",
            "getting bullied",
            "being bullied",
            "got bullied",

            # Pushing/shoving
            "pushes me around",
            "pushing me around",
            "shoves me",
            "shoving me",

            # Taking belongings
            "steals my stuff",
            "takes my stuff",
            "took my lunch",
            "takes my lunch money",
            "steals my lunch",

            # Tripping/physical harassment
            "trips me",
            "tripping me",
            "knocks my books",
        }

        # VERBAL_BULLYING - Name-calling, insults, verbal harassment
        self.verbal_bullying_keywords = {
            # Name-calling
            "calls me names",
            "calling me names",
            "makes fun of me",
            "making fun of me",
            "laughs at me",
            "laughing at me",
            "teases me",
            "teasing me",
            "picks on me",
            "picking on me",

            # Insults
            "says mean things",
            "saying mean things",
            "talks about me",
            "talking behind my back",

            # Mocking
            "mocks me",
            "mocking me",
            "imitates me",
            "imitating me",
        }

        # SOCIAL_EXCLUSION - Social isolation, exclusion, rejection
        self.social_exclusion_keywords = {
            # Direct exclusion
            "left me out",
            "leaves me out",
            "leaving me out",
            "won't let me play",
            "wont let me play",
            "excludes me",
            "excluding me",
            "excluded me",

            # Social isolation
            "no one talks to me",
            "nobody talks to me",
            "sits alone at lunch",
            "sit alone at lunch",
            "eat lunch alone",
            "play alone at recess",

            # Friendship issues
            "no friends",
            "don't have any friends",
            "dont have any friends",
            "no one likes me",
            "nobody likes me",
            "everyone hates me",
            "all my friends left me",

            # Group exclusion
            "won't sit with me",
            "wont sit with me",
            "won't include me",
            "wont include me",
            "keeps me out",
            "shut me out",
        }

        # CYBERBULLYING - Online harassment indicators
        self.cyberbullying_keywords = {
            # Social media bullying
            "mean messages",
            "mean texts",
            "mean comments",
            "posting about me",
            "posts about me",

            # Group chats
            "group chat without me",
            "left out of group chat",
            "kicked from group chat",

            # Online exclusion
            "unfriended me",
            "blocked me",
            "won't add me",
            "wont add me",

            # Spreading rumors online
            "posted lies about me",
            "posting lies about me",
            "sharing embarrassing",
        }

        # THREATS - Threats and intimidation
        self.threat_keywords = {
            # Direct threats (non-violent - violent threats in crisis detector)
            "threatens to tell",
            "says they'll tell",
            "says theyll tell",

            # Intimidation
            "intimidates me",
            "intimidating me",
            "scares me at school",
        }

        # EMOTIONAL_IMPACT - How bullying makes the child feel
        self.emotional_impact_keywords = {
            # Fear
            "scared to go to school",
            "afraid to go to school",
            "don't want to go to school",
            "dont want to go to school",
            "scared of school",

            # Loneliness
            "feel so alone",
            "feeling so alone",
            "alone at school",
            "lonely at school",

            # Social anxiety
            "everyone's against me",
            "everyones against me",
            "whole class hates me",
            "whole grade hates me",

            # Rumor spreading
            "spreading rumors",
            "spreading lies",
            "told everyone",
            "telling everyone",
            "rumors about me",
            "lies about me",
        }

        # Severity - all bullying keywords are MEDIUM
        self.severity = "medium"

        logger.info("Bullying keyword list initialized with comprehensive categories")

    def contains_bullying_keywords(self, text: str) -> bool:
        """
        Check if text contains any bullying keywords

        Args:
            text: Text to check

        Returns:
            True if any bullying keyword is found
        """
        text_lower = text.lower()

        # Check all categories
        return (
            self._contains_any(text_lower, self.physical_bullying_keywords)
            or self._contains_any(text_lower, self.verbal_bullying_keywords)
            or self._contains_any(text_lower, self.social_exclusion_keywords)
            or self._contains_any(text_lower, self.cyberbullying_keywords)
            or self._contains_any(text_lower, self.threat_keywords)
            or self._contains_any(text_lower, self.emotional_impact_keywords)
        )

    def find_bullying_keywords(self, text: str) -> List[Dict[str, str]]:
        """
        Find all bullying keywords in text with categories

        Args:
            text: Text to search

        Returns:
            List of dictionaries with keyword info:
            [
                {
                    'keyword': str,
                    'category': str,  # 'physical', 'verbal', 'social', 'cyber', 'threats', 'emotional'
                    'severity': str,  # Always 'medium'
                }
            ]
        """
        text_lower = text.lower()
        found_keywords = []

        # Check physical bullying keywords
        for keyword in self.physical_bullying_keywords:
            if keyword in text_lower:
                found_keywords.append({
                    "keyword": keyword,
                    "category": "physical_bullying",
                    "severity": "medium",
                })

        # Check verbal bullying keywords
        for keyword in self.verbal_bullying_keywords:
            if keyword in text_lower:
                found_keywords.append({
                    "keyword": keyword,
                    "category": "verbal_bullying",
                    "severity": "medium",
                })

        # Check social exclusion keywords
        for keyword in self.social_exclusion_keywords:
            if keyword in text_lower:
                found_keywords.append({
                    "keyword": keyword,
                    "category": "social_exclusion",
                    "severity": "medium",
                })

        # Check cyberbullying keywords
        for keyword in self.cyberbullying_keywords:
            if keyword in text_lower:
                found_keywords.append({
                    "keyword": keyword,
                    "category": "cyberbullying",
                    "severity": "medium",
                })

        # Check threat keywords
        for keyword in self.threat_keywords:
            if keyword in text_lower:
                found_keywords.append({
                    "keyword": keyword,
                    "category": "threats",
                    "severity": "medium",
                })

        # Check emotional impact keywords
        for keyword in self.emotional_impact_keywords:
            if keyword in text_lower:
                found_keywords.append({
                    "keyword": keyword,
                    "category": "emotional_impact",
                    "severity": "medium",
                })

        return found_keywords

    def get_category(self, text: str) -> str:
        """
        Get the primary bullying category detected

        Args:
            text: Text to analyze

        Returns:
            Category name: 'physical_bullying', 'verbal_bullying',
            'social_exclusion', 'cyberbullying', 'threats',
            'emotional_impact', or 'none'
        """
        text_lower = text.lower()

        # Priority order (most severe/actionable first)
        if self._contains_any(text_lower, self.threat_keywords):
            return "threats"
        elif self._contains_any(text_lower, self.physical_bullying_keywords):
            return "physical_bullying"
        elif self._contains_any(text_lower, self.cyberbullying_keywords):
            return "cyberbullying"
        elif self._contains_any(text_lower, self.verbal_bullying_keywords):
            return "verbal_bullying"
        elif self._contains_any(text_lower, self.social_exclusion_keywords):
            return "social_exclusion"
        elif self._contains_any(text_lower, self.emotional_impact_keywords):
            return "emotional_impact"
        else:
            return "none"

    def get_all_categories(self, text: str) -> List[str]:
        """
        Get all bullying categories detected in text

        Args:
            text: Text to analyze

        Returns:
            List of category names found
        """
        text_lower = text.lower()
        categories = []

        if self._contains_any(text_lower, self.physical_bullying_keywords):
            categories.append("physical_bullying")
        if self._contains_any(text_lower, self.verbal_bullying_keywords):
            categories.append("verbal_bullying")
        if self._contains_any(text_lower, self.social_exclusion_keywords):
            categories.append("social_exclusion")
        if self._contains_any(text_lower, self.cyberbullying_keywords):
            categories.append("cyberbullying")
        if self._contains_any(text_lower, self.threat_keywords):
            categories.append("threats")
        if self._contains_any(text_lower, self.emotional_impact_keywords):
            categories.append("emotional_impact")

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
            "physical_bullying_keywords": len(self.physical_bullying_keywords),
            "verbal_bullying_keywords": len(self.verbal_bullying_keywords),
            "social_exclusion_keywords": len(self.social_exclusion_keywords),
            "cyberbullying_keywords": len(self.cyberbullying_keywords),
            "threat_keywords": len(self.threat_keywords),
            "emotional_impact_keywords": len(self.emotional_impact_keywords),
            "total_keywords": (
                len(self.physical_bullying_keywords)
                + len(self.verbal_bullying_keywords)
                + len(self.social_exclusion_keywords)
                + len(self.cyberbullying_keywords)
                + len(self.threat_keywords)
                + len(self.emotional_impact_keywords)
            ),
        }


# Global instance
bullying_keyword_list = BullyingKeywordList()


# Convenience functions
def contains_bullying_keywords(text: str) -> bool:
    """Check if text contains any bullying keywords"""
    return bullying_keyword_list.contains_bullying_keywords(text)


def find_bullying_keywords(text: str) -> List[Dict[str, str]]:
    """Find all bullying keywords in text"""
    return bullying_keyword_list.find_bullying_keywords(text)


def get_category(text: str) -> str:
    """Get primary bullying category"""
    return bullying_keyword_list.get_category(text)


def get_all_categories(text: str) -> List[str]:
    """Get all bullying categories detected"""
    return bullying_keyword_list.get_all_categories(text)


def get_stats() -> Dict[str, int]:
    """Get keyword list statistics"""
    return bullying_keyword_list.get_stats()
