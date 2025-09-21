"""Authentication middleware for FastAPI."""

from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from reskpoints.services.auth import get_auth_service, User, AuthService

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Get current authenticated user."""
    token = credentials.credentials
    user = await auth_service.get_current_user(token)
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_permission(permission: str):
    """Create dependency that requires specific permission."""
    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
        auth_service: AuthService = Depends(get_auth_service)
    ) -> User:
        auth_service.require_permission(current_user, permission)
        return current_user
    
    return permission_checker


# Convenience dependencies for common permissions
require_metrics_read = require_permission("metrics:read")
require_metrics_write = require_permission("metrics:write")
require_cost_read = require_permission("cost:read")
require_cost_write = require_permission("cost:write")
require_incidents_read = require_permission("incidents:read")
require_incidents_write = require_permission("incidents:write")
require_admin = require_permission("admin:manage")