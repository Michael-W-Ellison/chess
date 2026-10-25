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
        cleanup_interval: int = 100,
        throttle_seconds: Optional[int] = None,
    ):
        """
        Initialize RateLimiter

        Args:
            max_attempts: Maximum failed attempts before lockout
            lockout_minutes: Duration of lockout in minutes
            cleanup_interval: How often to cleanup old attempts (after N checks)
            throttle_seconds: If set, max_attempts failures in lockout_minutes do not lock
                out; they allow one attempt every throttle_seconds after the last one. Someone
                failing on purpose then delays the real user by seconds, not minutes.
        """
        self.max_attempts = max_attempts
        self.throttle = timedelta(seconds=throttle_seconds) if throttle_seconds else None
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

        # Check if under limit (or, when throttled, whether the wait since the last attempt is over)
        is_allowed = len(attempts) < self.max_attempts or (
            self.throttle is not None and datetime.now() - max(attempts) >= self.throttle)

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

    def wait_time(self, identifier: str) -> str:
        """How long until the next attempt is allowed, as text ("25 seconds"; "0 seconds" if now)"""
        if self.throttle is None:
            return self._get_remaining_lockout_time(identifier)
        attempts = self.attempts.get(identifier, [])
        if len(attempts) < self.max_attempts:
            return "0 seconds"
        remaining = max(0, int((max(attempts) + self.throttle - datetime.now()).total_seconds()) + 1)
        return f"{remaining} second{'s' if remaining != 1 else ''}"

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


# Global rate limiter instance for the parent password: after 5 failures within 15 minutes,
# one attempt every 30 seconds. There is one password and every request comes from this
# computer, so a lockout would let a child keep the parent out by typing wrong passwords; 30
# seconds is too slow to guess a password that meets the requirements.
auth_rate_limiter = RateLimiter(max_attempts=5, lockout_minutes=15, throttle_seconds=30)

