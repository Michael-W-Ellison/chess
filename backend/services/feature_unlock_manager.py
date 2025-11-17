"""
Feature Unlock Manager Service
Manages feature availability based on friendship level
"""

from typing import Dict, List, Set, Optional
import logging

from sqlalchemy.orm import Session
from models.personality import BotPersonality

logger = logging.getLogger("chatbot.feature_unlock_manager")


class FeatureUnlockManager:
    """
    Feature Unlock Manager - controls feature availability by friendship level

    Manages:
    - Feature definitions and requirements
    - Feature availability checks
    - Feature metadata and descriptions
    - Progressive feature unlocking
    """

    def __init__(self):
        # Define all features and their unlock levels
        self.feature_definitions = {
            # Level 1 - Starting features (always available)
            "basic_chat": {
                "level": 1,
                "name": "Basic Chat",
                "description": "Send and receive messages",
                "category": "conversation",
            },
            "view_personality": {
                "level": 1,
                "name": "View Personality",
                "description": "See bot's personality traits",
                "category": "profile",
            },

            # Level 2 - Acquaintance
            "profile_unlocked": {
                "level": 2,
                "name": "Profile Access",
                "description": "View and edit your user profile",
                "category": "profile",
            },
            "save_memories": {
                "level": 2,
                "name": "Memory System",
                "description": "Bot remembers your preferences",
                "category": "memory",
            },

            # Level 3 - Buddy
            "catchphrase_unlocked": {
                "level": 3,
                "name": "Personal Catchphrase",
                "description": "Bot develops a unique catchphrase",
                "category": "personality",
            },
            "favorites_unlocked": {
                "level": 3,
                "name": "Favorites Tracking",
                "description": "Save and remember your favorite things",
                "category": "memory",
            },
            "casual_mode": {
                "level": 3,
                "name": "Casual Conversation Mode",
                "description": "More relaxed, friendly conversation style",
                "category": "conversation",
            },

            # Level 4 - Friend
            "interests_shared": {
                "level": 4,
                "name": "Shared Interests",
                "description": "Bot talks about shared interests",
                "category": "personality",
            },
            "deeper_conversations": {
                "level": 4,
                "name": "Deeper Conversations",
                "description": "More meaningful, context-aware chats",
                "category": "conversation",
            },
            "remember_goals": {
                "level": 4,
                "name": "Goal Tracking",
                "description": "Set and track personal goals",
                "category": "memory",
            },

            # Level 5 - Good Friend
            "advice_mode_unlocked": {
                "level": 5,
                "name": "Advice Mode",
                "description": "Ask for guidance and recommendations",
                "category": "conversation",
            },
            "emotional_support": {
                "level": 5,
                "name": "Emotional Support",
                "description": "Empathetic responses to feelings",
                "category": "conversation",
            },
            "achievement_tracking": {
                "level": 5,
                "name": "Achievement System",
                "description": "Track and celebrate accomplishments",
                "category": "memory",
            },

            # Level 6 - Close Friend
            "proactive_help": {
                "level": 6,
                "name": "Proactive Suggestions",
                "description": "Bot suggests helpful things unprompted",
                "category": "conversation",
            },
            "milestone_celebrations": {
                "level": 6,
                "name": "Milestone Celebrations",
                "description": "Special celebrations for achievements",
                "category": "events",
            },
            "custom_reminders": {
                "level": 6,
                "name": "Custom Reminders",
                "description": "Set personalized reminders",
                "category": "utility",
            },

            # Level 7 - Best Friend
            "custom_activities": {
                "level": 7,
                "name": "Custom Activities",
                "description": "Special activities and games",
                "category": "activities",
            },
            "anticipates_needs": {
                "level": 7,
                "name": "Predictive Assistance",
                "description": "Bot anticipates what you might need",
                "category": "conversation",
            },
            "mood_detection_advanced": {
                "level": 7,
                "name": "Advanced Mood Detection",
                "description": "Better understanding of your emotions",
                "category": "conversation",
            },

            # Level 8 - Bestie
            "inside_jokes": {
                "level": 8,
                "name": "Inside Jokes",
                "description": "References to shared experiences",
                "category": "personality",
            },
            "special_surprises": {
                "level": 8,
                "name": "Surprise Rewards",
                "description": "Random special treats and rewards",
                "category": "events",
            },
            "personalized_stories": {
                "level": 8,
                "name": "Personalized Stories",
                "description": "Custom stories based on your interests",
                "category": "activities",
            },

            # Level 9 - Soul Friend
            "celebration_events": {
                "level": 9,
                "name": "Special Events",
                "description": "Unique celebration experiences",
                "category": "events",
            },
            "life_advice": {
                "level": 9,
                "name": "Life Advice",
                "description": "Deeper guidance on important matters",
                "category": "conversation",
            },
            "memory_timeline": {
                "level": 9,
                "name": "Memory Timeline",
                "description": "View timeline of shared experiences",
                "category": "memory",
            },

            # Level 10 - Lifelong Companion
            "all_features_unlocked": {
                "level": 10,
                "name": "All Features Unlocked",
                "description": "Access to every feature",
                "category": "meta",
            },
            "legacy_memories": {
                "level": 10,
                "name": "Legacy Memory Archive",
                "description": "Permanent archive of all memories",
                "category": "memory",
            },
            "max_personalization": {
                "level": 10,
                "name": "Maximum Personalization",
                "description": "Full customization of bot behavior",
                "category": "personality",
            },
            "friendship_badge": {
                "level": 10,
                "name": "Lifelong Companion Badge",
                "description": "Special achievement badge",
                "category": "achievement",
            },
        }

        # Feature categories
        self.categories = {
            "conversation": "Conversation Features",
            "personality": "Personality Features",
            "memory": "Memory & Tracking",
            "activities": "Activities & Games",
            "events": "Special Events",
            "utility": "Utility Features",
            "profile": "Profile Features",
            "achievement": "Achievements",
            "meta": "Meta Features",
        }

    def is_feature_unlocked(
        self,
        feature_id: str,
        friendship_level: int
    ) -> bool:
        """
        Check if a feature is unlocked at current friendship level

        Args:
            feature_id: Feature identifier
            friendship_level: Current friendship level

        Returns:
            True if feature is unlocked
        """
        if feature_id not in self.feature_definitions:
            logger.warning(f"Unknown feature: {feature_id}")
            return False

        required_level = self.feature_definitions[feature_id]["level"]
        return friendship_level >= required_level

    def get_unlocked_features(
        self,
        friendship_level: int
    ) -> List[Dict]:
        """
        Get all features unlocked at current level

        Args:
            friendship_level: Current friendship level

        Returns:
            List of unlocked feature dictionaries
        """
        unlocked = []

        for feature_id, feature_data in self.feature_definitions.items():
            if feature_data["level"] <= friendship_level:
                feature_info = feature_data.copy()
                feature_info["id"] = feature_id
                unlocked.append(feature_info)

        # Sort by level, then by name
        unlocked.sort(key=lambda x: (x["level"], x["name"]))

        return unlocked

    def get_locked_features(
        self,
        friendship_level: int
    ) -> List[Dict]:
        """
        Get all features still locked at current level

        Args:
            friendship_level: Current friendship level

        Returns:
            List of locked feature dictionaries
        """
        locked = []

        for feature_id, feature_data in self.feature_definitions.items():
            if feature_data["level"] > friendship_level:
                feature_info = feature_data.copy()
                feature_info["id"] = feature_id
                feature_info["unlock_at_level"] = feature_data["level"]
                locked.append(feature_info)

        # Sort by unlock level, then by name
        locked.sort(key=lambda x: (x["level"], x["name"]))

        return locked

    def get_features_by_level(
        self,
        level: int
    ) -> List[Dict]:
        """
        Get all features that unlock at a specific level

        Args:
            level: Friendship level

        Returns:
            List of features unlocking at that level
        """
        features = []

        for feature_id, feature_data in self.feature_definitions.items():
            if feature_data["level"] == level:
                feature_info = feature_data.copy()
                feature_info["id"] = feature_id
                features.append(feature_info)

        features.sort(key=lambda x: x["name"])

        return features

    def get_features_by_category(
        self,
        category: str,
        friendship_level: Optional[int] = None
    ) -> List[Dict]:
        """
        Get features in a specific category

        Args:
            category: Feature category
            friendship_level: Optional filter by unlocked status

        Returns:
            List of features in category
        """
        features = []

        for feature_id, feature_data in self.feature_definitions.items():
            if feature_data["category"] == category:
                # Apply level filter if provided
                if friendship_level is not None:
                    if feature_data["level"] > friendship_level:
                        continue

                feature_info = feature_data.copy()
                feature_info["id"] = feature_id
                features.append(feature_info)

        features.sort(key=lambda x: (x["level"], x["name"]))

        return features

    def get_feature_info(
        self,
        feature_id: str
    ) -> Optional[Dict]:
        """
        Get detailed information about a feature

        Args:
            feature_id: Feature identifier

        Returns:
            Feature information dictionary or None
        """
        if feature_id not in self.feature_definitions:
            return None

        feature_info = self.feature_definitions[feature_id].copy()
        feature_info["id"] = feature_id
        feature_info["category_name"] = self.categories.get(
            feature_info["category"],
            "Other"
        )

        return feature_info

    def get_feature_summary(
        self,
        personality: BotPersonality
    ) -> Dict:
        """
        Get comprehensive feature summary for a user

        Args:
            personality: BotPersonality object

        Returns:
            Dictionary with feature summary
        """
        unlocked = self.get_unlocked_features(personality.friendship_level)
        locked = self.get_locked_features(personality.friendship_level)

        # Get features by category (unlocked only)
        by_category = {}
        for category_id in self.categories:
            features = self.get_features_by_category(
                category_id,
                personality.friendship_level
            )
            if features:
                by_category[category_id] = {
                    "name": self.categories[category_id],
                    "features": features,
                    "count": len(features),
                }

        # Get next unlockable features
        next_level = personality.friendship_level + 1
        next_features = []
        if next_level <= 10:
            next_features = self.get_features_by_level(next_level)

        return {
            "current_level": personality.friendship_level,
            "total_features": len(self.feature_definitions),
            "unlocked_count": len(unlocked),
            "locked_count": len(locked),
            "unlocked_features": unlocked,
            "locked_features": locked,
            "by_category": by_category,
            "next_level_features": next_features,
            "unlock_percentage": round(
                (len(unlocked) / len(self.feature_definitions)) * 100,
                1
            ),
        }

    def get_all_categories(self) -> Dict[str, str]:
        """
        Get all feature categories

        Returns:
            Dictionary of category_id -> category_name
        """
        return self.categories.copy()

    def check_multiple_features(
        self,
        feature_ids: List[str],
        friendship_level: int
    ) -> Dict[str, bool]:
        """
        Check multiple features at once

        Args:
            feature_ids: List of feature identifiers
            friendship_level: Current friendship level

        Returns:
            Dictionary mapping feature_id -> is_unlocked
        """
        results = {}

        for feature_id in feature_ids:
            results[feature_id] = self.is_feature_unlocked(
                feature_id,
                friendship_level
            )

        return results


# Global instance
feature_unlock_manager = FeatureUnlockManager()


# Convenience functions
def is_feature_unlocked(feature_id: str, friendship_level: int) -> bool:
    """Check if feature is unlocked"""
    return feature_unlock_manager.is_feature_unlocked(feature_id, friendship_level)


def get_unlocked_features(friendship_level: int) -> List[Dict]:
    """Get all unlocked features"""
    return feature_unlock_manager.get_unlocked_features(friendship_level)


def get_feature_summary(personality: BotPersonality) -> Dict:
    """Get feature summary for user"""
    return feature_unlock_manager.get_feature_summary(personality)
