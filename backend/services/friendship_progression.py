"""
Friendship Progression Service
Manages friendship level progression based on multiple factors
"""

from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from models.personality import BotPersonality

logger = logging.getLogger("chatbot.friendship_progression")

# Lazy import to avoid circular dependency
_level_up_handler_cache = None

def _get_level_up_handler():
    """Lazy import of level-up event handler"""
    global _level_up_handler_cache
    if _level_up_handler_cache is None:
        from services.level_up_event_handler import level_up_event_handler
        _level_up_handler_cache = level_up_event_handler
    return _level_up_handler_cache


class FriendshipProgressionManager:
    """
    Friendship Progression Manager - handles friendship level progression

    Manages:
    - Friendship points accumulation from various activities
    - Level progression based on points thresholds
    - Friendship level metadata (names, descriptions, perks)
    - Special events and rewards at level ups
    """

    def __init__(self):
        # Friendship level definitions
        # Each level has: name, min_points, description, perks
        self.friendship_levels = [
            {
                "level": 1,
                "name": "Stranger",
                "min_points": 0,
                "max_points": 99,
                "description": "Just met! Getting to know each other.",
                "perks": ["Basic conversations"],
                "icon": "👋"
            },
            {
                "level": 2,
                "name": "Acquaintance",
                "min_points": 100,
                "max_points": 299,
                "description": "Starting to get familiar with each other.",
                "perks": ["Basic conversations", "Remembers your name"],
                "icon": "🙂"
            },
            {
                "level": 3,
                "name": "Buddy",
                "min_points": 300,
                "max_points": 599,
                "description": "Becoming friends! More comfortable together.",
                "perks": ["Casual conversations", "Personal catchphrase", "Remembers favorites"],
                "icon": "😊"
            },
            {
                "level": 4,
                "name": "Friend",
                "min_points": 600,
                "max_points": 999,
                "description": "Good friends! Enjoy chatting together.",
                "perks": ["Deeper conversations", "Shares interests", "Remembers goals"],
                "icon": "🤗"
            },
            {
                "level": 5,
                "name": "Good Friend",
                "min_points": 1000,
                "max_points": 1599,
                "description": "Close friends! Trust is building.",
                "perks": ["Personal advice", "Emotional support", "Remembers achievements"],
                "icon": "😄"
            },
            {
                "level": 6,
                "name": "Close Friend",
                "min_points": 1600,
                "max_points": 2399,
                "description": "Very close! Strong bond forming.",
                "perks": ["Deep understanding", "Proactive help", "Celebrates milestones"],
                "icon": "🥰"
            },
            {
                "level": 7,
                "name": "Best Friend",
                "min_points": 2400,
                "max_points": 3499,
                "description": "Best friends! Always there for each other.",
                "perks": ["Complete trust", "Anticipates needs", "Custom activities"],
                "icon": "💙"
            },
            {
                "level": 8,
                "name": "Bestie",
                "min_points": 3500,
                "max_points": 4999,
                "description": "Inseparable besties! Deep connection.",
                "perks": ["Inside jokes", "Shared experiences", "Special surprises"],
                "icon": "💖"
            },
            {
                "level": 9,
                "name": "Soul Friend",
                "min_points": 5000,
                "max_points": 7499,
                "description": "Soul-level friendship! Incredibly close.",
                "perks": ["Deep understanding", "Life advice", "Celebration events"],
                "icon": "✨"
            },
            {
                "level": 10,
                "name": "Lifelong Companion",
                "min_points": 7500,
                "max_points": 999999,
                "description": "Lifelong companions! Unbreakable bond.",
                "perks": ["All features unlocked", "Maximum personalization", "Legacy memories"],
                "icon": "🌟"
            }
        ]

        # Point rewards for different activities
        self.point_rewards = {
            # Conversation-based rewards
            "message_sent": 5,                    # Each message in conversation
            "conversation_completed": 20,         # Completing a conversation
            "long_conversation": 30,              # 10+ messages in conversation
            "quality_conversation": 40,           # 20+ messages in conversation

            # Engagement rewards
            "daily_checkin": 15,                  # First conversation of the day
            "streak_3_days": 50,                  # 3 consecutive days
            "streak_7_days": 100,                 # 7 consecutive days
            "streak_30_days": 300,                # 30 consecutive days

            # Trust and sharing rewards
            "shares_personal_info": 25,           # Shares favorite, goal, etc.
            "shares_achievement": 35,             # Shares accomplishment
            "shares_feelings": 30,                # Expresses emotions
            "asks_for_advice": 20,                # Seeks bot's advice

            # Response quality rewards
            "positive_feedback": 40,              # User gives positive response
            "thanks_bot": 15,                     # User says thanks
            "laughs_at_joke": 10,                 # User responds to humor

            # Milestone rewards
            "completes_profile": 100,             # Fills out profile info
            "first_goal_set": 50,                 # Sets first goal
            "goal_achieved": 75,                  # Achieves a goal
            "week_active": 150,                   # Active for a week
            "month_active": 500,                  # Active for a month
        }

    def get_level_info(self, level: int) -> Dict:
        """
        Get information about a friendship level

        Args:
            level: Friendship level (1-10)

        Returns:
            Dictionary with level information
        """
        for level_info in self.friendship_levels:
            if level_info["level"] == level:
                return level_info

        # Default to max level if not found
        return self.friendship_levels[-1]

    def get_level_from_points(self, points: int) -> int:
        """
        Calculate friendship level from points

        Args:
            points: Total friendship points

        Returns:
            Friendship level (1-10)
        """
        for level_info in reversed(self.friendship_levels):
            if points >= level_info["min_points"]:
                return level_info["level"]

        return 1  # Minimum level

    def get_points_to_next_level(self, current_points: int) -> Tuple[int, int]:
        """
        Calculate points needed for next level

        Args:
            current_points: Current friendship points

        Returns:
            Tuple of (points_needed, next_level_threshold)
        """
        current_level = self.get_level_from_points(current_points)

        # If at max level, return 0
        if current_level >= 10:
            return 0, current_points

        # Get next level info
        next_level_info = self.get_level_info(current_level + 1)
        next_threshold = next_level_info["min_points"]
        points_needed = next_threshold - current_points

        return points_needed, next_threshold

    def add_friendship_points(
        self,
        personality: BotPersonality,
        activity: str,
        db: Session,
        custom_points: Optional[int] = None
    ) -> Tuple[BotPersonality, bool, Dict]:
        """
        Add friendship points for an activity

        Args:
            personality: BotPersonality object
            activity: Activity type (key from point_rewards)
            db: Database session
            custom_points: Optional custom points (overrides default)

        Returns:
            Tuple of (updated personality, level_increased flag, event_info dict)
        """
        # Get points for activity
        if custom_points is not None:
            points = custom_points
        elif activity in self.point_rewards:
            points = self.point_rewards[activity]
        else:
            logger.warning(f"Unknown activity: {activity}")
            points = 0

        if points == 0:
            return personality, False, {}

        # Store old values
        old_points = personality.friendship_points
        old_level = personality.friendship_level

        # Add points
        personality.friendship_points += points

        # Calculate new level
        new_level = self.get_level_from_points(personality.friendship_points)
        level_increased = new_level > old_level

        # Update level if increased
        if level_increased:
            personality.friendship_level = new_level

            logger.info(
                f"Friendship level increased: {old_level} -> {new_level} "
                f"(points: {old_points} -> {personality.friendship_points})"
            )

        # Commit changes
        db.commit()
        db.refresh(personality)

        # Build event info
        event_info = {
            "activity": activity,
            "points_earned": points,
            "old_points": old_points,
            "new_points": personality.friendship_points,
            "old_level": old_level,
            "new_level": new_level,
            "level_increased": level_increased,
        }

        # Add level-up specific info
        if level_increased:
            level_info = self.get_level_info(new_level)
            event_info["level_info"] = level_info
            event_info["message"] = f"Congratulations! You reached {level_info['name']}!"

            # Create level-up event in database
            try:
                handler = _get_level_up_handler()
                level_up_event = handler.create_level_up_event(
                    user_id=personality.user_id,
                    old_level=old_level,
                    new_level=new_level,
                    friendship_points=personality.friendship_points,
                    points_earned=points,
                    db=db
                )
                event_info["level_up_event_id"] = level_up_event.id
            except Exception as e:
                logger.error(f"Failed to create level-up event: {e}", exc_info=True)
                # Don't fail the whole operation if event creation fails

        return personality, level_increased, event_info

    def get_friendship_progress(
        self,
        personality: BotPersonality
    ) -> Dict:
        """
        Get detailed friendship progression information

        Args:
            personality: BotPersonality object

        Returns:
            Dictionary with progression details
        """
        current_level = personality.friendship_level
        current_points = personality.friendship_points

        current_level_info = self.get_level_info(current_level)
        points_needed, next_threshold = self.get_points_to_next_level(current_points)

        # Calculate progress percentage to next level
        if current_level < 10:
            level_min = current_level_info["min_points"]
            level_max = current_level_info["max_points"]
            level_range = level_max - level_min + 1
            progress_in_level = current_points - level_min
            progress_percentage = (progress_in_level / level_range) * 100
        else:
            progress_percentage = 100.0

        return {
            "current_level": current_level,
            "current_level_info": current_level_info,
            "current_points": current_points,
            "points_to_next_level": points_needed,
            "next_level_threshold": next_threshold,
            "progress_percentage": round(progress_percentage, 1),
            "is_max_level": current_level >= 10,
        }

    def get_available_activities(self) -> Dict[str, int]:
        """
        Get all available activities and their point values

        Returns:
            Dictionary of activity -> points
        """
        return self.point_rewards.copy()

    def get_friendship_history_summary(
        self,
        personality: BotPersonality,
        db: Session
    ) -> Dict:
        """
        Get summary of friendship progression history

        Args:
            personality: BotPersonality object
            db: Database session

        Returns:
            Dictionary with history summary
        """
        # Calculate time-based stats
        account_age = datetime.now() - personality.created_at
        days_active = account_age.days

        # Calculate average points per day
        avg_points_per_day = (
            personality.friendship_points / days_active if days_active > 0 else 0
        )

        # Calculate average points per conversation
        avg_points_per_conversation = (
            personality.friendship_points / personality.total_conversations
            if personality.total_conversations > 0
            else 0
        )

        return {
            "total_points_earned": personality.friendship_points,
            "current_level": personality.friendship_level,
            "total_conversations": personality.total_conversations,
            "days_active": days_active,
            "avg_points_per_day": round(avg_points_per_day, 1),
            "avg_points_per_conversation": round(avg_points_per_conversation, 1),
            "account_created": personality.created_at.isoformat(),
            "last_updated": personality.updated_at.isoformat(),
        }

    def simulate_points_needed_for_level(self, target_level: int) -> Dict:
        """
        Simulate how many points are needed to reach a target level

        Args:
            target_level: Target friendship level (1-10)

        Returns:
            Dictionary with simulation results
        """
        if target_level < 1 or target_level > 10:
            raise ValueError("Target level must be between 1 and 10")

        level_info = self.get_level_info(target_level)
        points_needed = level_info["min_points"]

        # Estimate activities needed
        estimates = {}
        for activity, points_per_activity in self.point_rewards.items():
            if points_per_activity > 0:
                activities_needed = points_needed / points_per_activity
                estimates[activity] = round(activities_needed, 1)

        return {
            "target_level": target_level,
            "level_name": level_info["name"],
            "points_required": points_needed,
            "estimated_activities": estimates,
            "level_info": level_info,
        }


# Global instance
friendship_manager = FriendshipProgressionManager()


# Convenience functions
def add_friendship_points(
    personality: BotPersonality,
    activity: str,
    db: Session,
    custom_points: Optional[int] = None
) -> Tuple[BotPersonality, bool, Dict]:
    """Add friendship points for an activity"""
    return friendship_manager.add_friendship_points(
        personality, activity, db, custom_points
    )


def get_friendship_progress(personality: BotPersonality) -> Dict:
    """Get friendship progression information"""
    return friendship_manager.get_friendship_progress(personality)


def get_level_info(level: int) -> Dict:
    """Get information about a friendship level"""
    return friendship_manager.get_level_info(level)
