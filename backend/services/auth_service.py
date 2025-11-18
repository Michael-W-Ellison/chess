"""
Authentication Service
Handles password verification and JWT token generation for parent dashboard
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext

from utils.config import settings

logger = logging.getLogger("chatbot.auth_service")


class AuthService:
    """
    Authentication Service for Parent Dashboard

    Features:
    - Password hashing and verification using bcrypt
    - JWT token generation and validation
    - Configurable token expiration
    - Secure password management

    Usage:
        auth_service.verify_password("user_password", "hashed_password")
        token = auth_service.create_access_token({"sub": "parent"})
        payload = auth_service.verify_token(token)
    """

    def __init__(self):
        """Initialize AuthService"""
        # Password hashing context using bcrypt
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        # JWT configuration
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

        # Check if authentication is properly configured
        self.is_configured = self._check_configuration()

        if self.is_configured:
            logger.info("AuthService initialized and configured")
        else:
            logger.warning("AuthService initialized but not properly configured")

    def _check_configuration(self) -> bool:
        """
        Check if authentication is properly configured

        Returns:
            True if all required settings are present
        """
        if not settings.PARENT_DASHBOARD_REQUIRE_PASSWORD:
            return True  # Password protection disabled

        if not settings.PARENT_DASHBOARD_PASSWORD:
            logger.warning("PARENT_DASHBOARD_PASSWORD not set in configuration")
            return False

        if not settings.JWT_SECRET_KEY:
            logger.warning("JWT_SECRET_KEY not set in configuration")
            return False

        return True

    def hash_password(self, password: str) -> str:
        """
        Hash a plaintext password

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
            plain_password: Plaintext password to verify
            hashed_password: Hashed password to compare against

        Returns:
            True if password matches
        """
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Error verifying password: {e}", exc_info=True)
            return False

    def authenticate(self, password: str) -> bool:
        """
        Authenticate a parent dashboard login attempt

        Args:
            password: Password provided by user

        Returns:
            True if authentication successful
        """
        if not settings.PARENT_DASHBOARD_REQUIRE_PASSWORD:
            logger.info("Password protection disabled - allowing access")
            return True

        if not self.is_configured:
            logger.error("Authentication not properly configured")
            return False

        # Verify against stored hashed password
        stored_password = settings.PARENT_DASHBOARD_PASSWORD
        result = self.verify_password(password, stored_password)

        if result:
            logger.info("Parent dashboard authentication successful")
        else:
            logger.warning("Parent dashboard authentication failed")

        return result

    def create_access_token(
        self,
        data: Dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token

        Args:
            data: Data to encode in token (typically {"sub": "parent"})
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT token string
        """
        if not self.secret_key:
            raise ValueError("JWT_SECRET_KEY not configured")

        to_encode = data.copy()

        # Set expiration time
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.access_token_expire_minutes
            )

        to_encode.update({"exp": expire})

        # Encode JWT
        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm
        )

        logger.debug(f"Created access token, expires at {expire}")
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify and decode a JWT token

        Args:
            token: JWT token string

        Returns:
            Decoded token payload if valid, None otherwise
        """
        if not self.secret_key:
            logger.error("JWT_SECRET_KEY not configured")
            return None

        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload

        except JWTError as e:
            logger.debug(f"Token verification failed: {e}")
            return None

        except Exception as e:
            logger.error(f"Unexpected error verifying token: {e}", exc_info=True)
            return None

    def is_token_valid(self, token: str) -> bool:
        """
        Check if a token is valid

        Args:
            token: JWT token string

        Returns:
            True if token is valid and not expired
        """
        payload = self.verify_token(token)
        return payload is not None

    def get_token_expiry(self, token: str) -> Optional[datetime]:
        """
        Get the expiration time of a token

        Args:
            token: JWT token string

        Returns:
            Expiration datetime if token is valid, None otherwise
        """
        payload = self.verify_token(token)
        if payload and "exp" in payload:
            return datetime.fromtimestamp(payload["exp"])
        return None


# Global service instance
auth_service = AuthService()


# Convenience functions
def hash_password(password: str) -> str:
    """Hash a plaintext password"""
    return auth_service.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return auth_service.verify_password(plain_password, hashed_password)


def authenticate(password: str) -> bool:
    """Authenticate a parent dashboard login"""
    return auth_service.authenticate(password)


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    return auth_service.create_access_token(data, expires_delta)


def verify_token(token: str) -> Optional[Dict]:
    """Verify and decode a JWT token"""
    return auth_service.verify_token(token)


def is_token_valid(token: str) -> bool:
    """Check if a token is valid"""
    return auth_service.is_token_valid(token)
