"""
Drift Rate Limiter Service
Enforces rate limits on personality trait drift to prevent rapid changes
"""

from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import func
from models.personality import BotPersonality
from models.personality_drift import PersonalityDrift

logger = logging.getLogger("chatbot.drift_rate_limiter")


class DriftRateLimiter:
    """
    Drift Rate Limiter - enforces rate limits on personality drift

    Prevents personality from changing too quickly by enforcing:
    - Maximum drift per conversation (per trait)
    - Maximum drift per time period (daily, weekly, monthly)
    - Cooldown periods between significant changes

    All limits are configurable and can be adjusted based on needs.
    """

    # Rate limit configuration
    MAX_DRIFT_PER_CONVERSATION = 0.02  # Maximum drift per conversation per trait
    MAX_DRIFT_PER_DAY = 0.05          # Maximum drift per day per trait
    MAX_DRIFT_PER_WEEK = 0.10         # Maximum drift per week per trait
    MAX_DRIFT_PER_MONTH = 0.15        # Maximum drift per month per trait

    # Cooldown configuration
    COOLDOWN_AFTER_LARGE_DRIFT = timedelta(hours=6)  # Wait 6 hours after large drift
    LARGE_DRIFT_THRESHOLD = 0.04  # Drifts >= this are considered "large"

    def __init__(self):
        """Initialize the rate limiter"""
        pass

    def check_conversation_limit(
        self,
        personality: BotPersonality,
        trait_name: str,
        requested_drift: float,
        db: Session,
        conversation_id: Optional[int] = None
    ) -> Tuple[bool, float, str]:
        """
        Check if requested drift exceeds per-conversation limit

        Args:
            personality: BotPersonality object
            trait_name: Name of trait
            requested_drift: Requested drift amount (can be positive or negative)
            db: Database session
            conversation_id: Optional conversation ID to check

        Returns:
            Tuple of (allowed, capped_drift, message)
        """
        abs_drift = abs(requested_drift)

        if abs_drift <= self.MAX_DRIFT_PER_CONVERSATION:
            return True, requested_drift, "Within per-conversation limit"

        # Drift exceeds limit, cap it
        capped_drift = (
            self.MAX_DRIFT_PER_CONVERSATION if requested_drift > 0
            else -self.MAX_DRIFT_PER_CONVERSATION
        )

        message = (
            f"Drift capped from {requested_drift:+.3f} to {capped_drift:+.3f} "
            f"(max per conversation: {self.MAX_DRIFT_PER_CONVERSATION})"
        )

        logger.warning(
            f"Conversation drift limit reached for {trait_name}: {message}"
        )

        return False, capped_drift, message

    def check_time_period_limit(
        self,
        personality: BotPersonality,
        trait_name: str,
        requested_drift: float,
        db: Session,
        period_days: int = 30
    ) -> Tuple[bool, float, str]:
        """
        Check if requested drift would exceed time period limit

        Args:
            personality: BotPersonality object
            trait_name: Name of trait
            requested_drift: Requested drift amount
            db: Database session
            period_days: Number of days to check (default 30 for monthly)

        Returns:
            Tuple of (allowed, capped_drift, message)
        """
        # Get drift limit for period
        if period_days == 1:
            max_drift = self.MAX_DRIFT_PER_DAY
        elif period_days == 7:
            max_drift = self.MAX_DRIFT_PER_WEEK
        elif period_days == 30:
            max_drift = self.MAX_DRIFT_PER_MONTH
        else:
            # Custom period - scale monthly limit
            max_drift = self.MAX_DRIFT_PER_MONTH * (period_days / 30.0)

        # Calculate total drift in period
        period_start = datetime.now() - timedelta(days=period_days)

        total_drift = self._calculate_total_drift(
            personality.user_id, trait_name, period_start, db
        )

        # Check if adding requested drift would exceed limit
        potential_total = total_drift + abs(requested_drift)

        if potential_total <= max_drift:
            return True, requested_drift, f"Within {period_days}-day limit"

        # Would exceed limit, calculate how much drift is still allowed
        remaining_drift = max_drift - total_drift

        if remaining_drift <= 0:
            # No drift allowed
            message = (
                f"Trait {trait_name} has already drifted {total_drift:.3f} in the last "
                f"{period_days} days (limit: {max_drift:.3f}). No further drift allowed."
            )
            logger.warning(message)
            return False, 0.0, message

        # Some drift is allowed, but less than requested
        capped_drift = (
            remaining_drift if requested_drift > 0
            else -remaining_drift
        )

        message = (
            f"Drift capped from {requested_drift:+.3f} to {capped_drift:+.3f} "
            f"(used {total_drift:.3f}/{max_drift:.3f} in {period_days} days)"
        )

        logger.warning(
            f"Time period drift limit approaching for {trait_name}: {message}"
        )

        return False, capped_drift, message

    def check_cooldown(
        self,
        personality: BotPersonality,
        trait_name: str,
        db: Session
    ) -> Tuple[bool, Optional[datetime], str]:
        """
        Check if trait is in cooldown period after large drift

        Args:
            personality: BotPersonality object
            trait_name: Name of trait
            db: Database session

        Returns:
            Tuple of (in_cooldown, cooldown_until, message)
        """
        # Get most recent large drift for this trait
        cutoff_time = datetime.now() - self.COOLDOWN_AFTER_LARGE_DRIFT

        recent_large_drift = (
            db.query(PersonalityDrift)
            .filter(
                PersonalityDrift.user_id == personality.user_id,
                PersonalityDrift.trait_name == trait_name,
                PersonalityDrift.timestamp >= cutoff_time,
                func.abs(PersonalityDrift.change_amount) >= self.LARGE_DRIFT_THRESHOLD
            )
            .order_by(PersonalityDrift.timestamp.desc())
            .first()
        )

        if not recent_large_drift:
            return False, None, "No cooldown active"

        # Calculate when cooldown ends
        cooldown_until = recent_large_drift.timestamp + self.COOLDOWN_AFTER_LARGE_DRIFT
        time_remaining = cooldown_until - datetime.now()

        if time_remaining.total_seconds() <= 0:
            return False, None, "Cooldown expired"

        message = (
            f"Trait {trait_name} in cooldown for {time_remaining.total_seconds() / 3600:.1f} more hours "
            f"after large drift of {recent_large_drift.change_amount:+.3f} at "
            f"{recent_large_drift.timestamp.strftime('%Y-%m-%d %H:%M')}"
        )

        logger.info(message)

        return True, cooldown_until, message

    def apply_rate_limits(
        self,
        personality: BotPersonality,
        trait_name: str,
        requested_drift: float,
        db: Session,
        conversation_id: Optional[int] = None,
        enforce_cooldown: bool = True
    ) -> Tuple[float, List[str]]:
        """
        Apply all rate limits to requested drift

        Args:
            personality: BotPersonality object
            trait_name: Name of trait
            requested_drift: Requested drift amount
            db: Database session
            conversation_id: Optional conversation ID
            enforce_cooldown: Whether to enforce cooldown (default True)

        Returns:
            Tuple of (final_drift, limit_messages)
        """
        messages = []
        final_drift = requested_drift

        # Check cooldown first (if enforcing)
        if enforce_cooldown:
            in_cooldown, cooldown_until, msg = self.check_cooldown(
                personality, trait_name, db
            )

            if in_cooldown:
                messages.append(msg)
                messages.append(f"Drift blocked due to cooldown")
                return 0.0, messages

        # Check per-conversation limit
        allowed, capped, msg = self.check_conversation_limit(
            personality, trait_name, final_drift, db, conversation_id
        )

        if not allowed:
            final_drift = capped
            messages.append(msg)

        # Check daily limit
        allowed, capped, msg = self.check_time_period_limit(
            personality, trait_name, final_drift, db, period_days=1
        )

        if not allowed:
            final_drift = capped
            messages.append(msg)

        # Check weekly limit
        allowed, capped, msg = self.check_time_period_limit(
            personality, trait_name, final_drift, db, period_days=7
        )

        if not allowed:
            final_drift = capped
            messages.append(msg)

        # Check monthly limit
        allowed, capped, msg = self.check_time_period_limit(
            personality, trait_name, final_drift, db, period_days=30
        )

        if not allowed:
            final_drift = capped
            messages.append(msg)

        # Log final result
        if abs(final_drift) < abs(requested_drift):
            logger.info(
                f"Rate limits reduced drift for {trait_name} from "
                f"{requested_drift:+.3f} to {final_drift:+.3f}"
            )

        return final_drift, messages

    def get_drift_allowance(
        self,
        personality: BotPersonality,
        trait_name: str,
        db: Session,
        period_days: int = 30
    ) -> Dict:
        """
        Get how much drift is still allowed for a trait

        Args:
            personality: BotPersonality object
            trait_name: Name of trait
            db: Database session
            period_days: Time period to check

        Returns:
            Dictionary with allowance information
        """
        # Get limit for period
        if period_days == 1:
            max_drift = self.MAX_DRIFT_PER_DAY
        elif period_days == 7:
            max_drift = self.MAX_DRIFT_PER_WEEK
        elif period_days == 30:
            max_drift = self.MAX_DRIFT_PER_MONTH
        else:
            max_drift = self.MAX_DRIFT_PER_MONTH * (period_days / 30.0)

        # Calculate used drift
        period_start = datetime.now() - timedelta(days=period_days)
        total_drift = self._calculate_total_drift(
            personality.user_id, trait_name, period_start, db
        )

        remaining = max_drift - total_drift

        return {
            "period_days": period_days,
            "max_drift": max_drift,
            "used_drift": total_drift,
            "remaining_drift": max(0, remaining),
            "usage_percentage": min(100, (total_drift / max_drift * 100)) if max_drift > 0 else 0,
            "can_drift": remaining > 0,
        }

    def get_all_allowances(
        self,
        personality: BotPersonality,
        trait_name: str,
        db: Session
    ) -> Dict:
        """
        Get drift allowances for all time periods

        Args:
            personality: BotPersonality object
            trait_name: Name of trait
            db: Database session

        Returns:
            Dictionary with all allowances
        """
        return {
            "trait_name": trait_name,
            "daily": self.get_drift_allowance(personality, trait_name, db, 1),
            "weekly": self.get_drift_allowance(personality, trait_name, db, 7),
            "monthly": self.get_drift_allowance(personality, trait_name, db, 30),
            "per_conversation_limit": self.MAX_DRIFT_PER_CONVERSATION,
        }

    def _calculate_total_drift(
        self,
        user_id: int,
        trait_name: str,
        since: datetime,
        db: Session
    ) -> float:
        """
        Calculate total absolute drift for a trait since a time

        Args:
            user_id: User ID
            trait_name: Trait name
            since: Start time
            db: Database session

        Returns:
            Total absolute drift
        """
        drifts = (
            db.query(PersonalityDrift)
            .filter(
                PersonalityDrift.user_id == user_id,
                PersonalityDrift.trait_name == trait_name,
                PersonalityDrift.timestamp >= since
            )
            .all()
        )

        # Sum absolute values of drift
        total = sum(abs(drift.change_amount) for drift in drifts)

        return total

    def get_drift_rate_stats(
        self,
        personality: BotPersonality,
        db: Session
    ) -> Dict:
        """
        Get comprehensive drift rate statistics for all traits

        Args:
            personality: BotPersonality object
            db: Database session

        Returns:
            Dictionary with drift rate stats
        """
        traits = ["humor", "energy", "curiosity", "formality"]

        stats = {
            "user_id": personality.user_id,
            "traits": {},
        }

        for trait in traits:
            # Get allowances for all periods
            allowances = self.get_all_allowances(personality, trait, db)

            # Check cooldown
            in_cooldown, cooldown_until, cooldown_msg = self.check_cooldown(
                personality, trait, db
            )

            stats["traits"][trait] = {
                "allowances": allowances,
                "in_cooldown": in_cooldown,
                "cooldown_until": cooldown_until.isoformat() if cooldown_until else None,
                "cooldown_message": cooldown_msg,
            }

        return stats


# Global instance
drift_rate_limiter = DriftRateLimiter()


# Convenience functions
def apply_rate_limits(
    personality: BotPersonality,
    trait_name: str,
    requested_drift: float,
    db: Session,
    conversation_id: Optional[int] = None,
    enforce_cooldown: bool = True
) -> Tuple[float, List[str]]:
    """Apply rate limits to requested drift"""
    return drift_rate_limiter.apply_rate_limits(
        personality, trait_name, requested_drift, db, conversation_id, enforce_cooldown
    )


def get_drift_allowance(
    personality: BotPersonality,
    trait_name: str,
    db: Session,
    period_days: int = 30
) -> Dict:
    """Get drift allowance for a trait"""
    return drift_rate_limiter.get_drift_allowance(
        personality, trait_name, db, period_days
    )


def get_drift_rate_stats(personality: BotPersonality, db: Session) -> Dict:
    """Get comprehensive drift rate statistics"""
    return drift_rate_limiter.get_drift_rate_stats(personality, db)
