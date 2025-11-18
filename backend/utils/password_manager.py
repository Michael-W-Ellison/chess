#!/usr/bin/env python3
"""
Password Manager Utility
Helper script to generate and manage parent dashboard passwords
"""

import secrets
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from passlib.context import CryptContext


class PasswordManager:
    """
    Password Manager Utility

    Provides helper functions for:
    - Generating secure random passwords
    - Hashing passwords for storage
    - Generating JWT secret keys
    """

    def __init__(self):
        """Initialize PasswordManager"""
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def generate_password(self, length: int = 16) -> str:
        """
        Generate a secure random password

        Args:
            length: Length of password (default 16)

        Returns:
            Random password string
        """
        # Use a mix of uppercase, lowercase, digits, and special chars
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password

    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt

        Args:
            password: Plaintext password

        Returns:
            Hashed password string
        """
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against a hash

        Args:
            plain_password: Plaintext password
            hashed_password: Hashed password

        Returns:
            True if password matches
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def generate_jwt_secret(self, length: int = 32) -> str:
        """
        Generate a secure JWT secret key

        Args:
            length: Length of secret (default 32)

        Returns:
            Secure random secret string
        """
        return secrets.token_urlsafe(length)


def main():
    """Main CLI interface"""
    manager = PasswordManager()

    print("=" * 60)
    print("Chess Tutor - Parent Dashboard Password Manager")
    print("=" * 60)
    print()

    # Get action from user
    print("Select an action:")
    print("1. Generate new password and hash")
    print("2. Hash an existing password")
    print("3. Generate JWT secret key")
    print("4. Verify password against hash")
    print()

    try:
        choice = input("Enter choice (1-4): ").strip()

        if choice == "1":
            # Generate new password
            length = input("Password length (default 16): ").strip()
            length = int(length) if length else 16

            password = manager.generate_password(length)
            hashed = manager.hash_password(password)

            print("\n" + "=" * 60)
            print("Generated Password:")
            print(f"  {password}")
            print()
            print("Hashed Password (store in .env):")
            print(f"  {hashed}")
            print()
            print("Add to your .env file:")
            print(f"  PARENT_DASHBOARD_PASSWORD={hashed}")
            print("=" * 60)

        elif choice == "2":
            # Hash existing password
            password = input("Enter password to hash: ").strip()
            if not password:
                print("Error: Password cannot be empty")
                return

            hashed = manager.hash_password(password)

            print("\n" + "=" * 60)
            print("Hashed Password (store in .env):")
            print(f"  {hashed}")
            print()
            print("Add to your .env file:")
            print(f"  PARENT_DASHBOARD_PASSWORD={hashed}")
            print("=" * 60)

        elif choice == "3":
            # Generate JWT secret
            secret = manager.generate_jwt_secret()

            print("\n" + "=" * 60)
            print("JWT Secret Key (store in .env):")
            print(f"  {secret}")
            print()
            print("Add to your .env file:")
            print(f"  JWT_SECRET_KEY={secret}")
            print("=" * 60)

        elif choice == "4":
            # Verify password
            password = input("Enter password: ").strip()
            hashed = input("Enter hash: ").strip()

            if not password or not hashed:
                print("Error: Both password and hash required")
                return

            is_valid = manager.verify_password(password, hashed)

            print("\n" + "=" * 60)
            if is_valid:
                print("✓ Password matches hash!")
            else:
                print("✗ Password does NOT match hash")
            print("=" * 60)

        else:
            print("Invalid choice")

    except KeyboardInterrupt:
        print("\n\nAborted")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
