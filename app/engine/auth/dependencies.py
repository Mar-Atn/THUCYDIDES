"""FastAPI dependency injection for auth."""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from engine.auth.models import AuthUser
from engine.config.settings import settings

logger = logging.getLogger(__name__)

# Bearer token extractor — returns None if no token (allows optional auth)
_bearer = HTTPBearer(auto_error=False)


async def _get_user_from_token(token: str) -> Optional[AuthUser]:
    """Verify JWT with Supabase and fetch user profile."""
    from supabase import create_client

    try:
        # Create a client with the user's JWT to verify it
        client = create_client(settings.supabase_url, settings.supabase_anon_key)
        # Verify the token by getting the user
        user_response = client.auth.get_user(token)

        if not user_response or not user_response.user:
            return None

        uid = user_response.user.id

        # Fetch user profile from our users table using service role
        admin_client = create_client(
            settings.supabase_url, settings.supabase_service_role_key
        )
        result = (
            admin_client.table("users")
            .select("id, email, display_name, system_role, status, data_consent")
            .eq("id", uid)
            .single()
            .execute()
        )

        if not result.data:
            return None

        return AuthUser(**result.data)

    except Exception as e:
        logger.warning("JWT verification failed: %s", e)
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> AuthUser:
    """Dependency: require authenticated user.

    Usage:
        @app.get("/api/protected")
        async def endpoint(user: AuthUser = Depends(get_current_user)):
            ...
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")

    user = await _get_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account suspended")

    return user


async def require_moderator(
    user: AuthUser = Depends(get_current_user),
) -> AuthUser:
    """Dependency: require active moderator.

    Usage:
        @app.get("/api/admin/users")
        async def endpoint(user: AuthUser = Depends(require_moderator)):
            ...
    """
    if not user.is_moderator:
        raise HTTPException(status_code=403, detail="Moderator access required")
    return user
