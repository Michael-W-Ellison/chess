"""
Authentication Dependencies
FastAPI dependencies for protecting parent dashboard endpoints
"""

import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from utils.config import settings
from services.auth_service import auth_service

logger = logging.getLogger("chatbot.auth_dependencies")

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """
    Verify JWT token and get current user

    This dependency can be used to protect any FastAPI endpoint.
    It checks for a valid JWT token in the Authorization header.

    Args:
        credentials: HTTP Authorization credentials from request

    Returns:
        User payload from token

    Raises:
        HTTPException: 401 if authentication fails
    """
    # If password protection is disabled, allow access
    if not settings.PARENT_DASHBOARD_REQUIRE_PASSWORD:
        logger.debug("Password protection disabled - allowing access")
        return {"sub": "parent", "access": "unrestricted"}

    # Check if authentication is configured
    if not auth_service.is_configured:
        logger.error("Authentication required but not properly configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication not properly configured"
        )

    # Check if credentials are provided
    if not credentials:
        logger.warning("No authentication credentials provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token
    token = credentials.credentials
    payload = auth_service.verify_token(token)

    if not payload:
        logger.warning("Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.debug(f"Authentication successful for: {payload.get('sub')}")
    return payload


async def verify_parent_access(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> bool:
    """
    Verify parent dashboard access

    This is a simpler dependency that just returns True/False.
    Use get_current_user if you need the full payload.

    Args:
        credentials: HTTP Authorization credentials from request

    Returns:
        True if access is granted

    Raises:
        HTTPException: 401 if authentication fails
    """
    await get_current_user(credentials)
    return True


# Dependency that can be used in route parameters
RequireAuth = Depends(get_current_user)
RequireParentAccess = Depends(verify_parent_access)
