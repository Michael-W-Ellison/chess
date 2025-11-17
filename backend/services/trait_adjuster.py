"""
Trait Adjustment Service
Provides bounded, validated personality trait adjustments
"""

from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

from sqlalchemy.orm import Session
from models.personality import BotPersonality

logger = logging.getLogger("chatbot.trait_adjuster")


class TraitAdjuster:
    """
    Trait Adjuster - centralized service for bounded personality trait adjustments

    Ensures all trait changes:
    - Stay within valid bounds [0.0, 1.0]
    - Use validated trait names
    - Are properly logged
    - Can be tracked and audited

    All personality trait modifications should go through this service.
    """

    # Trait configuration
    VALID_TRAITS = ["humor", "energy", "curiosity", "formality"]
    TRAIT_MIN = 0.0
    TRAIT_MAX = 1.0

    # Default trait values
    DEFAULT_TRAIT_VALUES = {
        "humor": 0.5,
        "energy": 0.6,
        "curiosity": 0.5,
        "formality": 0.3,
    }

    def __init__(self):
        """Initialize the trait adjuster"""
        pass

    def validate_trait_name(self, trait_name: str) -> bool:
        """
        Validate that a trait name is valid

        Args:
            trait_name: Trait name to validate

        Returns:
            True if valid, False otherwise
        """
        return trait_name in self.VALID_TRAITS

    def validate_trait_value(self, value: float) -> bool:
        """
        Validate that a trait value is within bounds

        Args:
            value: Trait value to validate

        Returns:
            True if valid, False otherwise
        """
        return self.TRAIT_MIN <= value <= self.TRAIT_MAX

    def clamp_value(self, value: float) -> float:
        """
        Clamp a value to valid trait bounds

        Args:
            value: Value to clamp

        Returns:
            Clamped value between TRAIT_MIN and TRAIT_MAX
        """
        return max(self.TRAIT_MIN, min(self.TRAIT_MAX, value))

    def adjust_trait(
        self,
        personality: BotPersonality,
        trait_name: str,
        new_value: float,
        db: Session,
        commit: bool = True
    ) -> Tuple[float, float, float]:
        """
        Adjust a personality trait to a specific value with bounds checking

        Args:
            personality: BotPersonality object
            trait_name: Name of trait to adjust
            new_value: New value to set
            db: Database session
            commit: Whether to commit the change (default True)

        Returns:
            Tuple of (old_value, new_value_clamped, actual_change)

        Raises:
            ValueError: If trait_name is invalid
        """
        # Validate trait name
        if not self.validate_trait_name(trait_name):
            raise ValueError(
                f"Invalid trait name '{trait_name}'. "
                f"Must be one of: {', '.join(self.VALID_TRAITS)}"
            )

        # Get current value
        old_value = getattr(personality, trait_name)

        # Clamp new value to bounds
        new_value_clamped = self.clamp_value(new_value)

        # Calculate actual change
        actual_change = new_value_clamped - old_value

        # Apply change
        setattr(personality, trait_name, new_value_clamped)

        # Commit if requested
        if commit:
            db.commit()

        # Log the change
        logger.info(
            f"Adjusted {trait_name} for user {personality.user_id}: "
            f"{old_value:.3f} -> {new_value_clamped:.3f} "
            f"(change: {actual_change:+.3f})"
        )

        # Warn if value was clamped
        if new_value != new_value_clamped:
            logger.warning(
                f"Trait value {new_value:.3f} was clamped to {new_value_clamped:.3f} "
                f"(bounds: [{self.TRAIT_MIN}, {self.TRAIT_MAX}])"
            )

        return old_value, new_value_clamped, actual_change

    def adjust_trait_by_delta(
        self,
        personality: BotPersonality,
        trait_name: str,
        delta: float,
        db: Session,
        commit: bool = True
    ) -> Tuple[float, float, float]:
        """
        Adjust a personality trait by a delta amount with bounds checking

        Args:
            personality: BotPersonality object
            trait_name: Name of trait to adjust
            delta: Amount to change (can be positive or negative)
            db: Database session
            commit: Whether to commit the change (default True)

        Returns:
            Tuple of (old_value, new_value, actual_change)

        Raises:
            ValueError: If trait_name is invalid
        """
        # Validate trait name
        if not self.validate_trait_name(trait_name):
            raise ValueError(
                f"Invalid trait name '{trait_name}'. "
                f"Must be one of: {', '.join(self.VALID_TRAITS)}"
            )

        # Get current value
        old_value = getattr(personality, trait_name)

        # Calculate new value
        new_value = old_value + delta

        # Use adjust_trait to apply with bounds checking
        return self.adjust_trait(personality, trait_name, new_value, db, commit)

    def adjust_multiple_traits(
        self,
        personality: BotPersonality,
        adjustments: Dict[str, float],
        db: Session,
        is_delta: bool = False,
        commit: bool = True
    ) -> Dict[str, Tuple[float, float, float]]:
        """
        Adjust multiple personality traits at once

        Args:
            personality: BotPersonality object
            adjustments: Dictionary of {trait_name: value}
            db: Database session
            is_delta: If True, values are deltas; if False, absolute values
            commit: Whether to commit changes (default True)

        Returns:
            Dictionary of {trait_name: (old_value, new_value, change)}

        Raises:
            ValueError: If any trait_name is invalid
        """
        results = {}

        for trait_name, value in adjustments.items():
            if is_delta:
                old_val, new_val, change = self.adjust_trait_by_delta(
                    personality, trait_name, value, db, commit=False
                )
            else:
                old_val, new_val, change = self.adjust_trait(
                    personality, trait_name, value, db, commit=False
                )

            results[trait_name] = (old_val, new_val, change)

        # Commit once for all changes
        if commit:
            db.commit()

        logger.info(
            f"Adjusted {len(adjustments)} traits for user {personality.user_id}"
        )

        return results

    def reset_trait(
        self,
        personality: BotPersonality,
        trait_name: str,
        db: Session,
        commit: bool = True
    ) -> Tuple[float, float, float]:
        """
        Reset a trait to its default value

        Args:
            personality: BotPersonality object
            trait_name: Name of trait to reset
            db: Database session
            commit: Whether to commit the change (default True)

        Returns:
            Tuple of (old_value, default_value, change)

        Raises:
            ValueError: If trait_name is invalid
        """
        # Validate trait name
        if not self.validate_trait_name(trait_name):
            raise ValueError(f"Invalid trait name '{trait_name}'")

        # Get default value
        default_value = self.DEFAULT_TRAIT_VALUES[trait_name]

        # Adjust to default
        return self.adjust_trait(personality, trait_name, default_value, db, commit)

    def reset_all_traits(
        self,
        personality: BotPersonality,
        db: Session,
        commit: bool = True
    ) -> Dict[str, Tuple[float, float, float]]:
        """
        Reset all traits to their default values

        Args:
            personality: BotPersonality object
            db: Database session
            commit: Whether to commit changes (default True)

        Returns:
            Dictionary of {trait_name: (old_value, new_value, change)}
        """
        results = {}

        for trait_name in self.VALID_TRAITS:
            old_val, new_val, change = self.reset_trait(
                personality, trait_name, db, commit=False
            )
            results[trait_name] = (old_val, new_val, change)

        # Commit once for all changes
        if commit:
            db.commit()

        logger.info(f"Reset all traits for user {personality.user_id}")

        return results

    def get_trait_value(
        self,
        personality: BotPersonality,
        trait_name: str
    ) -> float:
        """
        Get the current value of a trait

        Args:
            personality: BotPersonality object
            trait_name: Name of trait to get

        Returns:
            Current trait value

        Raises:
            ValueError: If trait_name is invalid
        """
        if not self.validate_trait_name(trait_name):
            raise ValueError(f"Invalid trait name '{trait_name}'")

        return getattr(personality, trait_name)

    def get_all_trait_values(
        self,
        personality: BotPersonality
    ) -> Dict[str, float]:
        """
        Get all trait values as a dictionary

        Args:
            personality: BotPersonality object

        Returns:
            Dictionary of {trait_name: value}
        """
        return {
            trait: getattr(personality, trait)
            for trait in self.VALID_TRAITS
        }

    def validate_all_traits(
        self,
        personality: BotPersonality
    ) -> Dict[str, bool]:
        """
        Check if all traits are within valid bounds

        Args:
            personality: BotPersonality object

        Returns:
            Dictionary of {trait_name: is_valid}
        """
        return {
            trait: self.validate_trait_value(getattr(personality, trait))
            for trait in self.VALID_TRAITS
        }

    def get_trait_info(self, trait_name: str) -> Dict:
        """
        Get information about a trait

        Args:
            trait_name: Trait name

        Returns:
            Dictionary with trait information

        Raises:
            ValueError: If trait_name is invalid
        """
        if not self.validate_trait_name(trait_name):
            raise ValueError(f"Invalid trait name '{trait_name}'")

        trait_descriptions = {
            "humor": {
                "name": "Humor",
                "description": "Frequency and intensity of jokes",
                "high": "Very playful, lots of jokes",
                "low": "Serious, minimal humor",
            },
            "energy": {
                "name": "Energy",
                "description": "Enthusiasm and liveliness",
                "high": "Highly enthusiastic, energetic",
                "low": "Calm, subdued, relaxed",
            },
            "curiosity": {
                "name": "Curiosity",
                "description": "How often bot asks questions",
                "high": "Very inquisitive, engaged",
                "low": "More passive, less questioning",
            },
            "formality": {
                "name": "Formality",
                "description": "Casual vs formal language",
                "high": "Very formal, proper language",
                "low": "Very casual, informal",
            },
        }

        info = trait_descriptions[trait_name].copy()
        info["min_value"] = self.TRAIT_MIN
        info["max_value"] = self.TRAIT_MAX
        info["default_value"] = self.DEFAULT_TRAIT_VALUES[trait_name]

        return info

    def get_all_trait_info(self) -> Dict[str, Dict]:
        """
        Get information about all traits

        Returns:
            Dictionary of {trait_name: trait_info}
        """
        return {
            trait: self.get_trait_info(trait)
            for trait in self.VALID_TRAITS
        }


# Global instance
trait_adjuster = TraitAdjuster()


# Convenience functions
def adjust_trait(
    personality: BotPersonality,
    trait_name: str,
    new_value: float,
    db: Session,
    commit: bool = True
) -> Tuple[float, float, float]:
    """Adjust a personality trait to a specific value"""
    return trait_adjuster.adjust_trait(
        personality, trait_name, new_value, db, commit
    )


def adjust_trait_by_delta(
    personality: BotPersonality,
    trait_name: str,
    delta: float,
    db: Session,
    commit: bool = True
) -> Tuple[float, float, float]:
    """Adjust a personality trait by a delta amount"""
    return trait_adjuster.adjust_trait_by_delta(
        personality, trait_name, delta, db, commit
    )


def reset_all_traits(
    personality: BotPersonality,
    db: Session,
    commit: bool = True
) -> Dict[str, Tuple[float, float, float]]:
    """Reset all traits to default values"""
    return trait_adjuster.reset_all_traits(personality, db, commit)


def get_all_trait_values(personality: BotPersonality) -> Dict[str, float]:
    """Get all trait values"""
    return trait_adjuster.get_all_trait_values(personality)
