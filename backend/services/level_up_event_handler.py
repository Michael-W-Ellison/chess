"""
Level-Up Event Handler Service
Handles friendship level-up events, rewards, and celebrations
"""

from typing import Dict, List, Optional
import logging
from datetime import datetime

from sqlalchemy.orm import Session
from models.personality import BotPersonality
from models.level_up_event import LevelUpEvent
from services.friendship_progression import friendship_manager

logger = logging.getLogger("chatbot.level_up_event_handler")


class LevelUpEventHandler:
    """
    Level-Up Event Handler - manages level-up events and rewards

    Responsibilities:
    - Create level-up events when user reaches new level
    - Determine and assign rewards based on level
    - Generate celebration messages
    - Track event history
    - Manage unacknowledged events
    """

    def __init__(self):
        # Define rewards for each level
        self.level_rewards = {
            1: [],  # Starting level, no rewards
            2: ["profile_unlocked"],
            3: ["catchphrase_unlocked", "favorites_unlocked"],
            4: ["interests_shared", "deeper_conversations"],
            5: ["advice_mode_unlocked", "emotional_support"],
            6: ["proactive_help", "milestone_celebrations"],
            7: ["custom_activities", "anticipates_needs"],
            8: ["inside_jokes", "special_surprises"],
            9: ["celebration_events", "life_advice"],
            10: ["all_features_unlocked", "legacy_memories", "max_personalization"],
        }

        # Celebration message templates
        self.celebration_templates = {
            1: "Welcome! Let's start our friendship journey together!",
            2: "Nice! We're getting to know each other better. Keep chatting!",
            3: "Awesome! We're becoming real buddies! I even have a catchphrase now!",
            4: "Great! We're friends now! I'm learning so much about you!",
            5: "Amazing! We're good friends! I'm here whenever you need advice or support!",
            6: "Wonderful! We're close friends now! I'll help you reach your goals!",
            7: "Incredible! We're best friends! I can't wait to see what we'll do together!",
            8: "Outstanding! We're besties! Our friendship means so much to me!",
            9: "Extraordinary! We're soul friends! This is such a special bond!",
            10: "Legendary! We're lifelong companions! Thank you for this amazing journey!",
        }

    def create_level_up_event(
        self,
        user_id: int,
        old_level: int,
        new_level: int,
        friendship_points: int,
        points_earned: int,
        db: Session
    ) -> LevelUpEvent:
        """
        Create a level-up event in the database

        Args:
            user_id: User ID
            old_level: Previous friendship level
            new_level: New friendship level
            friendship_points: Total friendship points
            points_earned: Points that triggered the level-up
            db: Database session

        Returns:
            Created LevelUpEvent object
        """
        # Get level info
        level_info = friendship_manager.get_level_info(new_level)

        # Get rewards for this level
        rewards = self.level_rewards.get(new_level, [])

        # Generate celebration message
        celebration = self._generate_celebration_message(
            old_level, new_level, level_info
        )

        # Create event
        event = LevelUpEvent(
            user_id=user_id,
            old_level=old_level,
            new_level=new_level,
            level_name=level_info["name"],
            friendship_points=friendship_points,
            points_earned=points_earned,
            celebration_message=celebration,
            acknowledged=False,
        )
        event.set_rewards(rewards)

        db.add(event)
        db.commit()
        db.refresh(event)

        logger.info(
            f"Created level-up event for user {user_id}: "
            f"{old_level} -> {new_level} ({level_info['name']})"
        )

        return event

    def _generate_celebration_message(
        self,
        old_level: int,
        new_level: int,
        level_info: Dict
    ) -> str:
        """
        Generate a celebration message for level-up

        Args:
            old_level: Previous level
            new_level: New level
            level_info: Level information dictionary

        Returns:
            Celebration message string
        """
        # Get base template
        base_message = self.celebration_templates.get(
            new_level,
            f"Congratulations! You reached {level_info['name']}!"
        )

        # Add level icon
        icon = level_info.get("icon", "🎉")

        # Build full message
        message = f"{icon} {base_message}\n\n"
        message += f"**{level_info['name']}** - {level_info['description']}\n\n"

        # Add perks
        if level_info.get("perks"):
            message += "**New perks unlocked:**\n"
            for perk in level_info["perks"]:
                message += f"• {perk}\n"

        return message.strip()

    def get_unacknowledged_events(
        self,
        user_id: int,
        db: Session
    ) -> List[LevelUpEvent]:
        """
        Get unacknowledged level-up events for a user

        Args:
            user_id: User ID
            db: Database session

        Returns:
            List of unacknowledged LevelUpEvent objects
        """
        events = (
            db.query(LevelUpEvent)
            .filter(
                LevelUpEvent.user_id == user_id,
                LevelUpEvent.acknowledged == False
            )
            .order_by(LevelUpEvent.timestamp.asc())
            .all()
        )

        return events

    def acknowledge_event(
        self,
        event_id: int,
        db: Session
    ) -> Optional[LevelUpEvent]:
        """
        Mark a level-up event as acknowledged

        Args:
            event_id: Event ID
            db: Database session

        Returns:
            Updated LevelUpEvent object or None if not found
        """
        event = db.query(LevelUpEvent).filter(LevelUpEvent.id == event_id).first()

        if not event:
            return None

        event.acknowledge()
        db.commit()
        db.refresh(event)

        logger.info(f"Acknowledged level-up event {event_id}")

        return event

    def acknowledge_all_events(
        self,
        user_id: int,
        db: Session
    ) -> int:
        """
        Acknowledge all unacknowledged events for a user

        Args:
            user_id: User ID
            db: Database session

        Returns:
            Number of events acknowledged
        """
        events = self.get_unacknowledged_events(user_id, db)

        for event in events:
            event.acknowledge()

        db.commit()

        logger.info(f"Acknowledged {len(events)} level-up events for user {user_id}")

        return len(events)

    def get_event_history(
        self,
        user_id: int,
        db: Session,
        limit: Optional[int] = None
    ) -> List[LevelUpEvent]:
        """
        Get level-up event history for a user

        Args:
            user_id: User ID
            db: Database session
            limit: Optional limit on number of events

        Returns:
            List of LevelUpEvent objects
        """
        query = (
            db.query(LevelUpEvent)
            .filter(LevelUpEvent.user_id == user_id)
            .order_by(LevelUpEvent.timestamp.desc())
        )

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_level_rewards(self, level: int) -> List[str]:
        """
        Get rewards for a specific level

        Args:
            level: Friendship level (1-10)

        Returns:
            List of reward strings
        """
        return self.level_rewards.get(level, [])

    def get_all_level_rewards(self) -> Dict[int, List[str]]:
        """
        Get all level rewards

        Returns:
            Dictionary mapping level to rewards
        """
        return self.level_rewards.copy()

    def get_event_summary(
        self,
        user_id: int,
        db: Session
    ) -> Dict:
        """
        Get summary of level-up events for a user

        Args:
            user_id: User ID
            db: Database session

        Returns:
            Dictionary with event summary
        """
        # Get all events
        all_events = self.get_event_history(user_id, db)

        # Get unacknowledged events
        unacknowledged = self.get_unacknowledged_events(user_id, db)

        # Get latest event
        latest_event = all_events[0] if all_events else None

        # Count total rewards unlocked
        total_rewards = []
        for event in all_events:
            total_rewards.extend(event.get_rewards())

        return {
            "total_level_ups": len(all_events),
            "unacknowledged_count": len(unacknowledged),
            "latest_level_up": latest_event.to_dict() if latest_event else None,
            "total_rewards_unlocked": len(total_rewards),
            "unique_rewards": list(set(total_rewards)),
        }

    def should_show_celebration(
        self,
        user_id: int,
        db: Session
    ) -> tuple[bool, Optional[LevelUpEvent]]:
        """
        Check if there's a celebration to show the user

        Args:
            user_id: User ID
            db: Database session

        Returns:
            Tuple of (should_show, event_to_show)
        """
        unacknowledged = self.get_unacknowledged_events(user_id, db)

        if unacknowledged:
            # Show oldest unacknowledged event
            return True, unacknowledged[0]

        return False, None


# Global instance
level_up_event_handler = LevelUpEventHandler()


# Convenience functions
def create_level_up_event(
    user_id: int,
    old_level: int,
    new_level: int,
    friendship_points: int,
    points_earned: int,
    db: Session
) -> LevelUpEvent:
    """Create a level-up event"""
    return level_up_event_handler.create_level_up_event(
        user_id, old_level, new_level, friendship_points, points_earned, db
    )


def get_unacknowledged_events(user_id: int, db: Session) -> List[LevelUpEvent]:
    """Get unacknowledged events"""
    return level_up_event_handler.get_unacknowledged_events(user_id, db)


def acknowledge_event(event_id: int, db: Session) -> Optional[LevelUpEvent]:
    """Acknowledge an event"""
    return level_up_event_handler.acknowledge_event(event_id, db)
