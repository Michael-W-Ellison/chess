"""
Personality Manager Service
Manages bot personality evolution and trait adjustments
"""

from typing import Dict, Optional
import logging
import random

from sqlalchemy.orm import Session
from models.personality import BotPersonality
from models.user import User

logger = logging.getLogger("chatbot.personality_manager")


class PersonalityManager:
    """
    Personality Manager - handles personality evolution and updates

    Manages:
    - Personality trait drift based on conversation patterns
    - Friendship level progression
    - Mood updates
    - Quirk and interest development
    - Catchphrase generation
    """

    def __init__(self):
        # Trait boundaries (from design spec)
        self.trait_ranges = {
            "humor": (0.0, 1.0),
            "energy": (0.0, 1.0),
            "curiosity": (0.0, 1.0),
            "formality": (0.0, 1.0),
        }

        # Drift limits
        self.max_change_per_conversation = 0.02
        self.max_change_per_month = 0.15

        # Available quirks
        self.available_quirks = [
            "uses_emojis",
            "tells_puns",
            "shares_facts",
            "storyteller",
        ]

        # Available interests
        self.available_interests = [
            "sports",
            "music",
            "art",
            "science",
            "reading",
            "gaming",
            "nature",
            "cooking",
            "technology",
            "history",
            "animals",
        ]

        # Friendship level thresholds
        self.friendship_levels = [
            (0, 5, 1),      # 0-5 convos = level 1
            (6, 10, 2),     # 6-10 = level 2
            (11, 20, 3),    # 11-20 = level 3
            (21, 30, 4),
            (31, 45, 5),
            (46, 60, 6),
            (61, 80, 7),
            (81, 100, 8),
            (101, 150, 9),
            (151, 999999, 10),
        ]

    def initialize_personality(
        self, user_id: int, db: Session, bot_name: Optional[str] = None
    ) -> BotPersonality:
        """
        Create initial personality for a new user

        Args:
            user_id: User ID
            db: Database session
            bot_name: Optional custom bot name (defaults to "Buddy")

        Returns:
            Created BotPersonality object
        """
        # Check if personality already exists
        existing = (
            db.query(BotPersonality).filter(BotPersonality.user_id == user_id).first()
        )
        if existing:
            logger.warning(f"Personality already exists for user {user_id}")
            return existing

        # Generate random traits within initial ranges
        personality = BotPersonality(
            user_id=user_id,
            name=bot_name or "Buddy",
            humor=random.uniform(0.3, 0.8),
            energy=random.uniform(0.4, 0.9),
            curiosity=random.uniform(0.3, 0.8),
            formality=random.uniform(0.2, 0.6),
            friendship_level=1,
            total_conversations=0,
            mood="happy",
        )

        # Assign 1-2 random quirks
        num_quirks = random.randint(1, 2)
        quirks = random.sample(self.available_quirks, num_quirks)
        personality.set_quirks(quirks)

        # Assign 2-3 random interests
        num_interests = random.randint(2, 3)
        interests = random.sample(self.available_interests, num_interests)
        personality.set_interests(interests)

        db.add(personality)
        db.commit()
        db.refresh(personality)

        logger.info(f"Initialized personality for user {user_id}: {personality.name}")
        logger.info(f"  Traits: humor={personality.humor:.2f}, energy={personality.energy:.2f}")
        logger.info(f"  Quirks: {quirks}")
        logger.info(f"  Interests: {interests}")

        return personality

    def update_personality_traits(
        self, personality: BotPersonality, conversation_metrics: Dict, db: Session
    ) -> BotPersonality:
        """
        Update personality traits based on conversation patterns

        Args:
            personality: BotPersonality object
            conversation_metrics: Metrics from the conversation
            db: Database session

        Returns:
            Updated BotPersonality object
        """
        adjustments = {
            "humor": 0.0,
            "energy": 0.0,
            "curiosity": 0.0,
            "formality": 0.0,
        }

        # User responds positively to jokes (longer responses after jokes)
        if conversation_metrics.get("positive_joke_response", False):
            adjustments["humor"] += 0.01

        # User uses casual language
        if conversation_metrics.get("casual_language_detected", False):
            adjustments["formality"] -= 0.01

        # User asks many questions back
        user_question_ratio = conversation_metrics.get("user_question_ratio", 0)
        if user_question_ratio > 0.3:
            adjustments["curiosity"] += 0.01

        # Conversations are brief
        avg_message_length = conversation_metrics.get("avg_message_length", 50)
        if avg_message_length < 20:
            adjustments["energy"] -= 0.01
            adjustments["curiosity"] -= 0.01

        # Apply adjustments with bounds checking
        for trait, delta in adjustments.items():
            if delta != 0.0:
                # Apply max change limit
                delta = max(
                    -self.max_change_per_conversation,
                    min(self.max_change_per_conversation, delta),
                )

                current_value = getattr(personality, trait)
                new_value = current_value + delta

                # Enforce bounds (0.0 to 1.0)
                min_val, max_val = self.trait_ranges[trait]
                new_value = max(min_val, min(max_val, new_value))

                setattr(personality, trait, new_value)

                if delta != 0.0:
                    logger.debug(
                        f"Adjusted {trait}: {current_value:.3f} -> {new_value:.3f} (Δ{delta:+.3f})"
                    )

        db.commit()
        return personality

    def update_friendship_level(
        self, personality: BotPersonality, db: Session
    ) -> tuple[BotPersonality, bool]:
        """
        Update friendship level based on total conversations

        Args:
            personality: BotPersonality object
            db: Database session

        Returns:
            Tuple of (updated personality, level_increased flag)
        """
        old_level = personality.friendship_level
        new_level = self.calculate_friendship_level(personality.total_conversations)

        level_increased = new_level > old_level

        if level_increased:
            personality.friendship_level = new_level
            logger.info(
                f"Friendship level increased: {old_level} -> {new_level} "
                f"(after {personality.total_conversations} conversations)"
            )

            # Special events on level ups
            if new_level == 3 and not personality.catchphrase:
                # Generate catchphrase at level 3
                personality.catchphrase = self._generate_catchphrase(personality)
                logger.info(f"Generated catchphrase: {personality.catchphrase}")

            db.commit()

        return personality, level_increased

    def calculate_friendship_level(self, total_conversations: int) -> int:
        """
        Calculate friendship level from conversation count

        Args:
            total_conversations: Total number of conversations

        Returns:
            Friendship level (1-10)
        """
        for min_convos, max_convos, level in self.friendship_levels:
            if min_convos <= total_conversations <= max_convos:
                return level
        return 10  # Max level

    def update_mood(
        self, personality: BotPersonality, detected_user_mood: Optional[str], db: Session
    ) -> BotPersonality:
        """
        Update bot mood based on user's detected mood

        Args:
            personality: BotPersonality object
            detected_user_mood: Detected mood from user message
            db: Database session

        Returns:
            Updated BotPersonality object
        """
        mood_mapping = {
            "sad": "concerned",
            "anxious": "concerned",
            "angry": "calm",
            "happy": "happy",
            "excited": "excited",
            "neutral": "happy",
        }

        if detected_user_mood and detected_user_mood in mood_mapping:
            new_mood = mood_mapping[detected_user_mood]

            if personality.mood != new_mood:
                old_mood = personality.mood
                personality.mood = new_mood
                logger.debug(f"Mood changed: {old_mood} -> {new_mood}")
                db.commit()

        return personality

    def _generate_catchphrase(self, personality: BotPersonality) -> str:
        """
        Generate a catchphrase based on personality traits

        Args:
            personality: BotPersonality object

        Returns:
            Generated catchphrase
        """
        # Simple catchphrase generation based on traits
        catchphrases = {
            "high_humor": [
                "That's what I call fun!",
                "Let's keep it light!",
                "Laughter is the best!",
            ],
            "high_energy": [
                "Let's go!",
                "Awesome sauce!",
                "Super excited!",
            ],
            "high_curiosity": [
                "Tell me more!",
                "That's interesting!",
                "I wonder...",
            ],
            "casual": [
                "Cool beans!",
                "No worries!",
                "You got this!",
            ],
            "formal": [
                "Excellent!",
                "Very well!",
                "Indeed!",
            ],
        }

        # Select based on dominant trait
        if personality.humor > 0.7:
            options = catchphrases["high_humor"]
        elif personality.energy > 0.7:
            options = catchphrases["high_energy"]
        elif personality.curiosity > 0.7:
            options = catchphrases["high_curiosity"]
        elif personality.formality > 0.6:
            options = catchphrases["formal"]
        else:
            options = catchphrases["casual"]

        return random.choice(options)

    def get_personality_description(self, personality: BotPersonality) -> Dict[str, str]:
        """
        Get human-readable descriptions of personality traits

        Args:
            personality: BotPersonality object

        Returns:
            Dictionary with trait descriptions
        """
        def describe_humor(value):
            if value < 0.3:
                return "rarely jokes"
            elif value < 0.5:
                return "occasional humor"
            elif value < 0.7:
                return "frequently funny"
            else:
                return "very humorous"

        def describe_energy(value):
            if value < 0.4:
                return "calm and relaxed"
            elif value < 0.6:
                return "moderately energetic"
            elif value < 0.8:
                return "very energetic"
            else:
                return "extremely enthusiastic"

        def describe_curiosity(value):
            if value < 0.3:
                return "rarely asks questions"
            elif value < 0.5:
                return "somewhat curious"
            elif value < 0.7:
                return "very curious"
            else:
                return "extremely inquisitive"

        def describe_formality(value):
            if value < 0.3:
                return "very casual"
            elif value < 0.5:
                return "casual"
            elif value < 0.7:
                return "somewhat formal"
            else:
                return "very formal"

        return {
            "humor": describe_humor(personality.humor),
            "energy": describe_energy(personality.energy),
            "curiosity": describe_curiosity(personality.curiosity),
            "formality": describe_formality(personality.formality),
        }


# Global instance
personality_manager = PersonalityManager()


# Convenience functions
def initialize_personality(
    user_id: int, db: Session, bot_name: Optional[str] = None
) -> BotPersonality:
    """Initialize personality for new user"""
    return personality_manager.initialize_personality(user_id, db, bot_name)


def update_personality_traits(
    personality: BotPersonality, conversation_metrics: Dict, db: Session
) -> BotPersonality:
    """Update personality traits"""
    return personality_manager.update_personality_traits(
        personality, conversation_metrics, db
    )


def update_friendship_level(
    personality: BotPersonality, db: Session
) -> tuple[BotPersonality, bool]:
    """Update friendship level"""
    return personality_manager.update_friendship_level(personality, db)
