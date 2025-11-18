"""
Advice Category Detector Service
Detects when users are asking for advice and categorizes the type of advice needed

This service helps the chatbot identify advice requests from kids (ages 8-14)
and categorize them to provide more relevant, age-appropriate responses.
"""

from typing import Dict, List, Optional, Tuple
import re
import logging

logger = logging.getLogger("chatbot.advice_category_detector")


class AdviceCategoryDetector:
    """
    Advice Category Detector - identifies and categorizes advice requests

    Features:
    - Detects when user is asking for advice or help
    - Categorizes advice into relevant topics
    - Provides confidence scores for detection
    - Age-appropriate categories for kids 8-14

    Advice Categories:
    - friendship: Friend problems, making friends, peer relationships
    - school: Homework, teachers, grades, school activities
    - family: Parents, siblings, family relationships
    - emotional: Feelings, sadness, anxiety, worry, stress
    - hobby: Activities, interests, what to do for fun
    - bullying: Being bullied or witnessing bullying (redirects to safety)
    - social: Social situations, fitting in, social anxiety
    - decision: Making choices, deciding what to do
    - conflict: Arguments, disagreements, resolving conflicts
    - general: General life advice not fitting other categories
    """

    def __init__(self):
        """Initialize AdviceCategoryDetector with patterns and keywords"""

        # Advice-seeking patterns (indicates user is asking for advice)
        self.advice_patterns = [
            # Direct advice requests
            r"\b(?:what|how) (?:do|should|can|could) (?:i|we)\b",
            r"\bshould i\b",
            r"\bwhat (?:should|can|do) i do\b",
            r"\bany (?:advice|suggestions|ideas|tips)\b",
            r"\bcan you (?:help|advise)\b",
            r"\bneed (?:help|advice|guidance)\b",
            r"\bdon't know what to do\b",
            r"\bwhat would you do\b",
            r"\bhow (?:do|can) i\b",
            # Question patterns
            r"\?$",  # Ends with question mark
            # Seeking guidance
            r"\bhelp me\b",
            r"\btell me\b",
            r"\bgive me (?:advice|help|tips)\b",
        ]

        # Category-specific keywords (for categorization)
        self.category_keywords = {
            "friendship": {
                "primary": [
                    "friend", "friends", "best friend", "friendship",
                    "buddy", "buddies", "pal", "classmate", "peer"
                ],
                "secondary": [
                    "trust", "loyalty", "betrayed", "left out", "ignored",
                    "hang out", "play with", "talk to", "fight with",
                    "make friends", "new friend", "old friend"
                ],
                "context": [
                    "doesn't want to", "won't talk", "being mean",
                    "said something", "told", "shared", "secret"
                ]
            },
            "school": {
                "primary": [
                    "school", "homework", "teacher", "class", "grade",
                    "test", "quiz", "exam", "assignment", "project"
                ],
                "secondary": [
                    "study", "studying", "learning", "understand",
                    "math", "science", "english", "history", "reading",
                    "recess", "lunch", "classroom", "principal"
                ],
                "context": [
                    "hard", "difficult", "don't understand", "confused",
                    "too much", "stressed about", "worried about"
                ]
            },
            "family": {
                "primary": [
                    "mom", "dad", "mother", "father", "parent", "parents",
                    "sister", "brother", "sibling", "family"
                ],
                "secondary": [
                    "grandma", "grandpa", "aunt", "uncle", "cousin",
                    "stepmother", "stepfather", "step", "half-brother"
                ],
                "context": [
                    "won't let me", "said i can't", "grounded", "punished",
                    "annoying", "bothering", "fighting with", "arguing"
                ]
            },
            "emotional": {
                "primary": [
                    "feel", "feeling", "felt", "sad", "upset", "worried",
                    "anxious", "nervous", "scared", "angry", "mad"
                ],
                "secondary": [
                    "emotion", "emotions", "cry", "crying", "tears",
                    "lonely", "alone", "depressed", "stress", "stressed",
                    "overwhelmed", "frustrated", "embarrassed", "ashamed"
                ],
                "context": [
                    "can't stop", "all the time", "lately", "right now",
                    "don't know why", "making me", "feel like"
                ]
            },
            "hobby": {
                "primary": [
                    "hobby", "hobbies", "activity", "activities",
                    "fun", "play", "game", "games", "sport", "sports"
                ],
                "secondary": [
                    "bored", "boring", "nothing to do", "what to do",
                    "learn", "try", "start", "interest", "interested"
                ],
                "context": [
                    "do for fun", "keep busy", "after school",
                    "on weekends", "free time", "spare time"
                ]
            },
            "bullying": {
                "primary": [
                    "bully", "bullying", "bullied", "bully me",
                    "picking on", "mean to me", "teasing", "making fun"
                ],
                "secondary": [
                    "calling me names", "pushing", "hitting", "threatening",
                    "excluding", "leaving out", "spreading rumors",
                    "embarrassing", "hurting", "won't leave me alone"
                ],
                "context": [
                    "every day", "keeps", "won't stop", "always",
                    "at school", "in class", "on the bus", "online"
                ]
            },
            "social": {
                "primary": [
                    "fit in", "fitting in", "popular", "unpopular",
                    "cool", "awkward", "weird", "different"
                ],
                "secondary": [
                    "shy", "quiet", "talk to people", "make conversation",
                    "group", "clique", "party", "invited", "included"
                ],
                "context": [
                    "feel like", "everyone else", "nobody likes",
                    "everyone thinks", "what people think"
                ]
            },
            "decision": {
                "primary": [
                    "decide", "decision", "choice", "choose", "pick",
                    "should i", "which", "what to pick", "what to choose"
                ],
                "secondary": [
                    "option", "options", "either", "or", "between",
                    "can't decide", "don't know which", "both", "neither"
                ],
                "context": [
                    "what's better", "which is best", "pros and cons",
                    "thinking about", "considering"
                ]
            },
            "conflict": {
                "primary": [
                    "fight", "fighting", "argument", "arguing", "disagreement",
                    "conflict", "mad at", "angry at", "upset with"
                ],
                "secondary": [
                    "yelling", "shouting", "said something mean",
                    "hurt feelings", "apologize", "make up", "fix"
                ],
                "context": [
                    "we had a", "got into", "started", "ended up",
                    "now we're", "won't talk", "still mad"
                ]
            },
        }

        # Compiled regex patterns for efficiency
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.advice_patterns
        ]

        logger.info("AdviceCategoryDetector initialized")

    def detect_advice_request(self, message: str) -> Dict:
        """
        Detect if message is asking for advice and categorize it

        Args:
            message: User message to analyze

        Returns:
            Dictionary with detection results:
            {
                'is_advice_request': bool,
                'confidence': float (0.0-1.0),
                'category': str or None,
                'categories': List[str],  # All matching categories
                'category_scores': Dict[str, float],
                'keywords_found': List[str],
            }
        """
        message_lower = message.lower()

        # Step 1: Detect if this is an advice request
        is_advice_request, advice_confidence = self._is_asking_for_advice(message_lower)

        if not is_advice_request:
            return {
                "is_advice_request": False,
                "confidence": 0.0,
                "category": None,
                "categories": [],
                "category_scores": {},
                "keywords_found": [],
            }

        # Step 2: Categorize the advice request
        category_scores = self._score_categories(message_lower)

        # Step 3: Determine primary category and all matching categories
        primary_category, all_categories = self._determine_categories(category_scores)

        # Step 4: Extract keywords found
        keywords_found = self._extract_keywords(message_lower, primary_category)

        # Step 5: Calculate overall confidence
        overall_confidence = self._calculate_confidence(
            advice_confidence, category_scores, primary_category
        )

        return {
            "is_advice_request": True,
            "confidence": overall_confidence,
            "category": primary_category,
            "categories": all_categories,
            "category_scores": category_scores,
            "keywords_found": keywords_found,
        }

    def _is_asking_for_advice(self, message: str) -> Tuple[bool, float]:
        """
        Determine if message is asking for advice

        Args:
            message: Lowercase message text

        Returns:
            Tuple of (is_advice_request, confidence)
        """
        # Check if message matches advice-seeking patterns
        pattern_matches = 0
        for pattern in self.compiled_patterns:
            if pattern.search(message):
                pattern_matches += 1

        # High confidence if multiple patterns match
        if pattern_matches >= 2:
            return True, 0.9

        # Medium confidence if one pattern matches
        if pattern_matches == 1:
            return True, 0.7

        # Check for explicit advice keywords
        explicit_keywords = [
            "advice", "help me", "what should i", "how do i",
            "need help", "can you help", "tell me what"
        ]

        for keyword in explicit_keywords:
            if keyword in message:
                return True, 0.8

        return False, 0.0

    def _score_categories(self, message: str) -> Dict[str, float]:
        """
        Score all categories based on keyword matches

        Args:
            message: Lowercase message text

        Returns:
            Dictionary mapping category to score (0.0-1.0)
        """
        scores = {}

        for category, keywords in self.category_keywords.items():
            score = 0.0

            # Primary keywords (highest weight)
            for keyword in keywords.get("primary", []):
                if keyword in message:
                    score += 0.5

            # Secondary keywords (medium weight)
            for keyword in keywords.get("secondary", []):
                if keyword in message:
                    score += 0.3

            # Context keywords (lower weight)
            for keyword in keywords.get("context", []):
                if keyword in message:
                    score += 0.2

            # Normalize score to 0-1 range
            scores[category] = min(1.0, score)

        return scores

    def _determine_categories(
        self, category_scores: Dict[str, float]
    ) -> Tuple[Optional[str], List[str]]:
        """
        Determine primary category and all matching categories

        Args:
            category_scores: Dictionary of category scores

        Returns:
            Tuple of (primary_category, all_matching_categories)
        """
        # Filter categories with score > 0.3
        matching_categories = [
            cat for cat, score in category_scores.items() if score > 0.3
        ]

        # Sort by score
        sorted_categories = sorted(
            matching_categories, key=lambda c: category_scores[c], reverse=True
        )

        # Primary is highest scoring, or None if no matches
        primary = sorted_categories[0] if sorted_categories else "general"

        return primary, sorted_categories

    def _extract_keywords(self, message: str, category: Optional[str]) -> List[str]:
        """
        Extract keywords found in message for the given category

        Args:
            message: Lowercase message text
            category: Category to extract keywords for

        Returns:
            List of keywords found
        """
        if not category or category == "general":
            return []

        keywords = self.category_keywords.get(category, {})
        found = []

        for keyword_type in ["primary", "secondary", "context"]:
            for keyword in keywords.get(keyword_type, []):
                if keyword in message:
                    found.append(keyword)

        return found[:5]  # Limit to 5 keywords

    def _calculate_confidence(
        self, advice_confidence: float, category_scores: Dict[str, float], category: Optional[str]
    ) -> float:
        """
        Calculate overall confidence in advice detection and categorization

        Args:
            advice_confidence: Confidence that this is an advice request
            category_scores: Scores for all categories
            category: Primary category detected

        Returns:
            Overall confidence score (0.0-1.0)
        """
        if not category or category == "general":
            # Lower confidence for general/uncategorized advice
            return advice_confidence * 0.7

        category_score = category_scores.get(category, 0.0)

        # Combine advice confidence and category score
        overall = (advice_confidence * 0.6) + (category_score * 0.4)

        return round(overall, 2)

    def get_category_description(self, category: str) -> str:
        """
        Get human-readable description of advice category

        Args:
            category: Category name

        Returns:
            Description of the category
        """
        descriptions = {
            "friendship": "Advice about friends and peer relationships",
            "school": "Advice about school, homework, and learning",
            "family": "Advice about family relationships and home life",
            "emotional": "Emotional support and managing feelings",
            "hobby": "Advice about activities, hobbies, and fun",
            "bullying": "Support for bullying situations (safety-sensitive)",
            "social": "Advice about social situations and fitting in",
            "decision": "Help with making decisions and choices",
            "conflict": "Advice about resolving arguments and conflicts",
            "general": "General life advice and guidance",
        }

        return descriptions.get(category, "General advice and support")

    def get_stats(self) -> Dict:
        """
        Get statistics about the advice category detector

        Returns:
            Dictionary with detector statistics
        """
        return {
            "total_categories": len(self.category_keywords),
            "categories": list(self.category_keywords.keys()),
            "pattern_count": len(self.compiled_patterns),
        }


# Global instance
advice_category_detector = AdviceCategoryDetector()


# Convenience functions
def detect_advice_request(message: str) -> Dict:
    """Detect if message is asking for advice"""
    return advice_category_detector.detect_advice_request(message)


def get_category_description(category: str) -> str:
    """Get description of advice category"""
    return advice_category_detector.get_category_description(category)


def get_stats() -> Dict:
    """Get detector statistics"""
    return advice_category_detector.get_stats()
