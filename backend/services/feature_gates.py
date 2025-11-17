"""
Feature Gates
Decorators and utilities for feature gating based on friendship level
"""

from typing import Callable, Optional
from functools import wraps
import logging

from sqlalchemy.orm import Session
from models.personality import BotPersonality
from services.feature_unlock_manager import feature_unlock_manager

logger = logging.getLogger("chatbot.feature_gates")


class FeatureNotUnlockedException(Exception):
    """Exception raised when attempting to use locked feature"""

    def __init__(self, feature_id: str, required_level: int, current_level: int):
        self.feature_id = feature_id
        self.required_level = required_level
        self.current_level = current_level
        super().__init__(
            f"Feature '{feature_id}' requires level {required_level} "
            f"(current level: {current_level})"
        )


def require_feature(feature_id: str):
    """
    Decorator to require a feature to be unlocked

    Usage:
        @require_feature("advice_mode_unlocked")
        def give_advice(personality, ...):
            ...

    Raises:
        FeatureNotUnlockedException if feature is locked
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to find personality in args/kwargs
            personality = None

            # Check args for BotPersonality
            for arg in args:
                if isinstance(arg, BotPersonality):
                    personality = arg
                    break

            # Check kwargs
            if personality is None and "personality" in kwargs:
                personality = kwargs["personality"]

            if personality is None:
                logger.warning(
                    f"Could not find personality object for feature gate: {feature_id}"
                )
                # Allow if we can't check
                return func(*args, **kwargs)

            # Check if feature is unlocked
            if not feature_unlock_manager.is_feature_unlocked(
                feature_id, personality.friendship_level
            ):
                feature_info = feature_unlock_manager.get_feature_info(feature_id)
                required_level = feature_info["level"] if feature_info else 1

                raise FeatureNotUnlockedException(
                    feature_id, required_level, personality.friendship_level
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def check_feature_access(
    personality: BotPersonality, feature_id: str, raise_exception: bool = False
) -> bool:
    """
    Check if user has access to a feature

    Args:
        personality: BotPersonality object
        feature_id: Feature to check
        raise_exception: If True, raise exception if locked

    Returns:
        True if unlocked

    Raises:
        FeatureNotUnlockedException if raise_exception=True and feature is locked
    """
    unlocked = feature_unlock_manager.is_feature_unlocked(
        feature_id, personality.friendship_level
    )

    if not unlocked and raise_exception:
        feature_info = feature_unlock_manager.get_feature_info(feature_id)
        required_level = feature_info["level"] if feature_info else 1

        raise FeatureNotUnlockedException(
            feature_id, required_level, personality.friendship_level
        )

    return unlocked


def get_feature_gate_message(feature_id: str, personality: BotPersonality) -> str:
    """
    Get user-friendly message when feature is locked

    Args:
        feature_id: Feature identifier
        personality: BotPersonality object

    Returns:
        Friendly message explaining how to unlock
    """
    feature_info = feature_unlock_manager.get_feature_info(feature_id)

    if not feature_info:
        return "This feature is not available yet."

    required_level = feature_info["level"]
    current_level = personality.friendship_level
    levels_needed = required_level - current_level

    # Get level name
    from services.friendship_progression import friendship_manager

    level_info = friendship_manager.get_level_info(required_level)

    message = f"**{feature_info['name']}** is locked! 🔒\n\n"
    message += f"{feature_info['description']}\n\n"

    if levels_needed == 1:
        message += f"Reach **{level_info['name']}** (Level {required_level}) to unlock this feature!\n"
    else:
        message += (
            f"You need to reach Level {required_level} ({level_info['name']}) "
            f"to unlock this feature. That's {levels_needed} more levels!\n"
        )

    message += "\nKeep chatting and earning friendship points to level up!"

    return message


def apply_feature_modifiers(
    personality: BotPersonality, base_config: dict
) -> dict:
    """
    Apply feature-based modifications to configuration

    Args:
        personality: BotPersonality object
        base_config: Base configuration dictionary

    Returns:
        Modified configuration with feature unlocks applied
    """
    config = base_config.copy()

    # Deeper conversations - increase context length
    if check_feature_access(personality, "deeper_conversations"):
        config["max_context_messages"] = config.get("max_context_messages", 5) + 5
        config["max_memory_items"] = config.get("max_memory_items", 5) + 5

    # Emotional support - enable empathy mode
    if check_feature_access(personality, "emotional_support"):
        config["empathy_mode"] = True
        config["mood_detection_enabled"] = True

    # Advanced mood detection
    if check_feature_access(personality, "mood_detection_advanced"):
        config["advanced_mood_detection"] = True
        config["emotion_granularity"] = "high"

    # Proactive help - enable suggestions
    if check_feature_access(personality, "proactive_help"):
        config["proactive_suggestions"] = True
        config["suggestion_frequency"] = "medium"

    # Anticipates needs - enable prediction
    if check_feature_access(personality, "anticipates_needs"):
        config["predictive_mode"] = True
        config["anticipation_enabled"] = True

    # Maximum personalization
    if check_feature_access(personality, "max_personalization"):
        config["personalization_level"] = "maximum"
        config["all_customization_enabled"] = True

    return config


def get_conversation_features(personality: BotPersonality) -> dict:
    """
    Get conversation-related features that are unlocked

    Args:
        personality: BotPersonality object

    Returns:
        Dictionary of conversation feature flags
    """
    return {
        "basic_chat": check_feature_access(personality, "basic_chat"),
        "casual_mode": check_feature_access(personality, "casual_mode"),
        "deeper_conversations": check_feature_access(personality, "deeper_conversations"),
        "advice_mode": check_feature_access(personality, "advice_mode_unlocked"),
        "emotional_support": check_feature_access(personality, "emotional_support"),
        "proactive_help": check_feature_access(personality, "proactive_help"),
        "anticipates_needs": check_feature_access(personality, "anticipates_needs"),
        "life_advice": check_feature_access(personality, "life_advice"),
    }


def get_memory_features(personality: BotPersonality) -> dict:
    """
    Get memory-related features that are unlocked

    Args:
        personality: BotPersonality object

    Returns:
        Dictionary of memory feature flags
    """
    return {
        "save_memories": check_feature_access(personality, "save_memories"),
        "favorites": check_feature_access(personality, "favorites_unlocked"),
        "goals": check_feature_access(personality, "remember_goals"),
        "achievements": check_feature_access(personality, "achievement_tracking"),
        "timeline": check_feature_access(personality, "memory_timeline"),
        "legacy_archive": check_feature_access(personality, "legacy_memories"),
    }


def get_personality_features(personality: BotPersonality) -> dict:
    """
    Get personality-related features that are unlocked

    Args:
        personality: BotPersonality object

    Returns:
        Dictionary of personality feature flags
    """
    return {
        "catchphrase": check_feature_access(personality, "catchphrase_unlocked"),
        "shared_interests": check_feature_access(personality, "interests_shared"),
        "inside_jokes": check_feature_access(personality, "inside_jokes"),
        "max_personalization": check_feature_access(
            personality, "max_personalization"
        ),
    }


# Feature-specific helper functions
def can_use_catchphrase(personality: BotPersonality) -> bool:
    """Check if bot can use catchphrase"""
    return check_feature_access(personality, "catchphrase_unlocked")


def can_give_advice(personality: BotPersonality) -> bool:
    """Check if advice mode is unlocked"""
    return check_feature_access(personality, "advice_mode_unlocked")


def can_share_interests(personality: BotPersonality) -> bool:
    """Check if bot can share interests"""
    return check_feature_access(personality, "interests_shared")


def can_celebrate_milestones(personality: BotPersonality) -> bool:
    """Check if milestone celebrations are unlocked"""
    return check_feature_access(personality, "milestone_celebrations")


def can_create_inside_jokes(personality: BotPersonality) -> bool:
    """Check if inside jokes are unlocked"""
    return check_feature_access(personality, "inside_jokes")


def has_max_personalization(personality: BotPersonality) -> bool:
    """Check if maximum personalization is unlocked"""
    return check_feature_access(personality, "max_personalization")
