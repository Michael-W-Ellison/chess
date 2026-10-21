"""
Authentication Dependencies
FastAPI dependencies for protecting parent dashboard endpoints
"""

import logging
from fastapi import Depends, HTTPException, Request, status
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
        HTTPException: 503 if password protection is on but no password is set up
    """
    # If password protection is disabled, allow access
    if not settings.PARENT_DASHBOARD_REQUIRE_PASSWORD:
        logger.debug("Password protection disabled - allowing access")
        return {"sub": "parent", "access": "unrestricted"}

    # Password protection is on but no password is set up: no token can be valid until it is,
    # so the parent API is unavailable (503), not failing (500)
    if not auth_service.is_configured:
        logger.error("Authentication required but not properly configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Parent dashboard password is not set up. Set PARENT_DASHBOARD_PASSWORD and "
                "JWT_SECRET_KEY (POST /api/parent/auth/setup-password generates both), then "
                "restart the backend."
            ),
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


async def require_parent_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    Router-level guard for the parent API

    Requires authentication for every parent endpoint except the /auth/* endpoints,
    which must stay reachable so a parent can log in or set up a password.

    Args:
        request: Incoming request
        credentials: HTTP Authorization credentials from request

    Returns:
        User payload from token, or None for /auth/* endpoints

    Raises:
        HTTPException: 401 if authentication fails
    """
    route = request.scope.get("route")
    path = getattr(route, "path", request.url.path)
    if "/auth/" in path:
        return None

    return await get_current_user(credentials)


# Dependency that can be used in route parameters
RequireAuth = Depends(get_current_user)
