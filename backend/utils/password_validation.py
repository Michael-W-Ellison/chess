"""
Password Validation Utilities
Validates password strength and requirements
"""

import re
from typing import List, Dict
import logging

logger = logging.getLogger("chatbot.password_validation")


class PasswordValidator:
    """
    Password Validator

    Validates password strength against configurable requirements.

    Default requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """

    def __init__(
        self,
        min_length: int = 8,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digit: bool = True,
        require_special: bool = True,
        special_chars: str = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    ):
        """
        Initialize PasswordValidator

        Args:
            min_length: Minimum password length
            require_uppercase: Require at least one uppercase letter
            require_lowercase: Require at least one lowercase letter
            require_digit: Require at least one digit
            require_special: Require at least one special character
            special_chars: Allowed special characters
        """
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digit = require_digit
        self.require_special = require_special
        self.special_chars = special_chars

    def validate(self, password: str) -> Dict[str, any]:
        """
        Validate a password against requirements

        Args:
            password: Password to validate

        Returns:
            Dictionary with validation results:
            {
                "valid": bool,
                "errors": List[str],
                "strength": str ("weak", "medium", "strong")
            }
        """
        errors = []

        # Check minimum length
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters long")

        # Check uppercase
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")

        # Check lowercase
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")

        # Check digit
        if self.require_digit and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")

        # Check special character
        if self.require_special:
            has_special = any(char in self.special_chars for char in password)
            if not has_special:
                errors.append(f"Password must contain at least one special character ({self.special_chars[:10]}...)")

        # Calculate strength
        strength = self._calculate_strength(password)

        is_valid = len(errors) == 0

        if is_valid:
            logger.debug(f"Password validation successful (strength: {strength})")
        else:
            logger.debug(f"Password validation failed: {', '.join(errors)}")

        return {
            "valid": is_valid,
            "errors": errors,
            "strength": strength
        }

    def _calculate_strength(self, password: str) -> str:
        """
        Calculate password strength

        Args:
            password: Password to evaluate

        Returns:
            Strength level: "weak", "medium", or "strong"
        """
        score = 0

        # Length bonus
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if len(password) >= 16:
            score += 1

        # Character variety
        if re.search(r'[a-z]', password):
            score += 1
        if re.search(r'[A-Z]', password):
            score += 1
        if re.search(r'\d', password):
            score += 1
        if any(char in self.special_chars for char in password):
            score += 1

        # Determine strength
        if score <= 3:
            return "weak"
        elif score <= 5:
            return "medium"
        else:
            return "strong"

    def get_requirements_text(self) -> str:
        """
        Get human-readable requirements text

        Returns:
            Description of password requirements
        """
        requirements = []

        requirements.append(f"At least {self.min_length} characters long")

        if self.require_uppercase:
            requirements.append("At least one uppercase letter (A-Z)")

        if self.require_lowercase:
            requirements.append("At least one lowercase letter (a-z)")

        if self.require_digit:
            requirements.append("At least one digit (0-9)")

        if self.require_special:
            requirements.append(f"At least one special character ({self.special_chars[:10]}...)")

        return "Password must contain:\n- " + "\n- ".join(requirements)


# Global validator instance with default settings
password_validator = PasswordValidator()


def validate_password(password: str) -> Dict[str, any]:
    """
    Validate a password using default validator

    Args:
        password: Password to validate

    Returns:
        Validation result dictionary
    """
    return password_validator.validate(password)


def is_password_strong_enough(password: str) -> bool:
    """
    Check if a password meets minimum requirements

    Args:
        password: Password to check

    Returns:
        True if password is valid
    """
    result = password_validator.validate(password)
    return result["valid"]


def get_password_requirements() -> str:
    """
    Get password requirements as text

    Returns:
        Human-readable requirements
    """
    return password_validator.get_requirements_text()


# Common weak passwords to reject
COMMON_PASSWORDS = {
    "password", "password123", "12345678", "qwerty", "abc123",
    "password1", "admin", "letmein", "welcome", "monkey",
    "1234567890", "password!", "Password1", "admin123",
    "chess", "chesstutorr", "parent", "parent123"
}


def is_common_password(password: str) -> bool:
    """
    Check if password is in common passwords list

    Args:
        password: Password to check

    Returns:
        True if password is too common
    """
    return password.lower() in COMMON_PASSWORDS
