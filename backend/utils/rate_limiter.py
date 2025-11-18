"""
Rate Limiter
Simple in-memory rate limiter for authentication attempts
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from collections import defaultdict

logger = logging.getLogger("chatbot.rate_limiter")


class RateLimiter:
    """
    Rate Limiter for Authentication

    Prevents brute force attacks by limiting failed login attempts.

    Features:
    - Configurable attempt limits
    - Configurable lockout duration
    - Automatic cleanup of old attempts
    - In-memory storage (simple, no database needed)

    Usage:
        rate_limiter = RateLimiter(max_attempts=5, lockout_minutes=15)
        if rate_limiter.is_allowed("user_ip"):
            # Allow login attempt
            if login_success:
                rate_limiter.clear_attempts("user_ip")
            else:
                rate_limiter.record_attempt("user_ip")
        else:
            # Too many attempts - deny
    """

    def __init__(
        self,
        max_attempts: int = 5,
        lockout_minutes: int = 15,
        cleanup_interval: int = 100
    ):
        """
        Initialize RateLimiter

        Args:
            max_attempts: Maximum failed attempts before lockout
            lockout_minutes: Duration of lockout in minutes
            cleanup_interval: How often to cleanup old attempts (after N checks)
        """
        self.max_attempts = max_attempts
        self.lockout_duration = timedelta(minutes=lockout_minutes)
        self.cleanup_interval = cleanup_interval

        # Store attempts: {identifier: [timestamp1, timestamp2, ...]}
        self.attempts: Dict[str, list] = defaultdict(list)

        # Counter for cleanup
        self.check_counter = 0

        logger.info(
            f"RateLimiter initialized: max_attempts={max_attempts}, "
            f"lockout_minutes={lockout_minutes}"
        )

    def is_allowed(self, identifier: str) -> bool:
        """
        Check if an identifier is allowed to attempt login

        Args:
            identifier: Unique identifier (e.g., IP address, username)

        Returns:
            True if attempt is allowed, False if rate limited
        """
        self._maybe_cleanup()

        # Get attempts for this identifier
        attempts = self.attempts.get(identifier, [])

        # Remove expired attempts
        cutoff_time = datetime.now() - self.lockout_duration
        attempts = [attempt for attempt in attempts if attempt > cutoff_time]
        self.attempts[identifier] = attempts

        # Check if under limit
        is_allowed = len(attempts) < self.max_attempts

        if not is_allowed:
            remaining_time = self._get_remaining_lockout_time(identifier)
            logger.warning(
                f"Rate limit exceeded for {identifier}: "
                f"{len(attempts)}/{self.max_attempts} attempts, "
                f"{remaining_time} remaining lockout"
            )
        else:
            logger.debug(
                f"Login attempt allowed for {identifier}: "
                f"{len(attempts)}/{self.max_attempts} attempts"
            )

        return is_allowed

    def record_attempt(self, identifier: str) -> None:
        """
        Record a failed login attempt

        Args:
            identifier: Unique identifier
        """
        self.attempts[identifier].append(datetime.now())
        attempts_count = len(self.attempts[identifier])

        logger.info(
            f"Recorded failed attempt for {identifier}: "
            f"{attempts_count}/{self.max_attempts}"
        )

        if attempts_count >= self.max_attempts:
            logger.warning(
                f"Rate limit reached for {identifier}: "
                f"Locked out for {self.lockout_duration.total_seconds() / 60} minutes"
            )

    def clear_attempts(self, identifier: str) -> None:
        """
        Clear all attempts for an identifier (on successful login)

        Args:
            identifier: Unique identifier
        """
        if identifier in self.attempts:
            del self.attempts[identifier]
            logger.debug(f"Cleared attempts for {identifier}")

    def get_remaining_attempts(self, identifier: str) -> int:
        """
        Get remaining attempts before lockout

        Args:
            identifier: Unique identifier

        Returns:
            Number of remaining attempts
        """
        attempts = self.attempts.get(identifier, [])
        cutoff_time = datetime.now() - self.lockout_duration
        valid_attempts = [a for a in attempts if a > cutoff_time]

        return max(0, self.max_attempts - len(valid_attempts))

    def _get_remaining_lockout_time(self, identifier: str) -> str:
        """
        Get remaining lockout time as human-readable string

        Args:
            identifier: Unique identifier

        Returns:
            Formatted time string (e.g., "14 minutes")
        """
        attempts = self.attempts.get(identifier, [])
        if not attempts:
            return "0 minutes"

        # Find oldest attempt in window
        cutoff_time = datetime.now() - self.lockout_duration
        valid_attempts = [a for a in attempts if a > cutoff_time]

        if not valid_attempts:
            return "0 minutes"

        oldest = min(valid_attempts)
        unlock_time = oldest + self.lockout_duration
        remaining = unlock_time - datetime.now()

        minutes = int(remaining.total_seconds() / 60)
        seconds = int(remaining.total_seconds() % 60)

        if minutes > 0:
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        else:
            return f"{seconds} second{'s' if seconds != 1 else ''}"

    def get_lockout_info(self, identifier: str) -> Optional[Dict]:
        """
        Get lockout information for an identifier

        Args:
            identifier: Unique identifier

        Returns:
            Dictionary with lockout info or None if not locked out
        """
        if not self.is_allowed(identifier):
            attempts = self.attempts.get(identifier, [])
            cutoff_time = datetime.now() - self.lockout_duration
            valid_attempts = [a for a in attempts if a > cutoff_time]

            oldest = min(valid_attempts) if valid_attempts else datetime.now()
            unlock_time = oldest + self.lockout_duration

            return {
                "locked_out": True,
                "attempts": len(valid_attempts),
                "max_attempts": self.max_attempts,
                "unlock_time": unlock_time.isoformat(),
                "remaining_time": self._get_remaining_lockout_time(identifier)
            }

        return None

    def _maybe_cleanup(self) -> None:
        """
        Periodically cleanup old attempts to prevent memory growth
        """
        self.check_counter += 1

        if self.check_counter >= self.cleanup_interval:
            self._cleanup()
            self.check_counter = 0

    def _cleanup(self) -> None:
        """
        Remove all expired attempts
        """
        cutoff_time = datetime.now() - self.lockout_duration
        original_count = len(self.attempts)

        # Remove identifiers with no valid attempts
        identifiers_to_remove = []
        for identifier, attempts in self.attempts.items():
            valid_attempts = [a for a in attempts if a > cutoff_time]
            if not valid_attempts:
                identifiers_to_remove.append(identifier)
            else:
                self.attempts[identifier] = valid_attempts

        for identifier in identifiers_to_remove:
            del self.attempts[identifier]

        cleaned = original_count - len(self.attempts)
        if cleaned > 0:
            logger.debug(f"Cleaned up {cleaned} expired rate limit entries")


# Global rate limiter instance
# 5 attempts, 15 minute lockout
auth_rate_limiter = RateLimiter(max_attempts=5, lockout_minutes=15)


def is_login_allowed(identifier: str) -> bool:
    """
    Check if a login attempt is allowed

    Args:
        identifier: Unique identifier (IP, username, etc.)

    Returns:
        True if attempt is allowed
    """
    return auth_rate_limiter.is_allowed(identifier)


def record_failed_login(identifier: str) -> None:
    """
    Record a failed login attempt

    Args:
        identifier: Unique identifier
    """
    auth_rate_limiter.record_attempt(identifier)


def clear_login_attempts(identifier: str) -> None:
    """
    Clear login attempts on successful login

    Args:
        identifier: Unique identifier
    """
    auth_rate_limiter.clear_attempts(identifier)


def get_login_lockout_info(identifier: str) -> Optional[Dict]:
    """
    Get lockout information

    Args:
        identifier: Unique identifier

    Returns:
        Lockout info or None
    """
    return auth_rate_limiter.get_lockout_info(identifier)
