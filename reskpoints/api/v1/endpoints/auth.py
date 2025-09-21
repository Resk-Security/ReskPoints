"""Authentication API endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from reskpoints.services.auth import (
    get_auth_service,
    AuthService,
    User,
    UserCreate,
    UserUpdate,
    Token,
)
from reskpoints.api.middleware.auth import (
    get_current_active_user,
    require_admin,
)

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str


class UserResponse(BaseModel):
    """User response model (without sensitive data)."""
    id: str
    username: str
    email: str
    full_name: str = None
    is_active: bool
    roles: List[str]


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Authenticate user and return access token."""
    token = await auth_service.login(login_data.username, login_data.password)
    return token


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """OAuth2 compatible token endpoint."""
    token = await auth_service.login(form_data.username, form_data.password)
    return token


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        roles=current_user.roles,
    )


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    admin_user: User = Depends(require_admin),
    auth_service: AuthService = Depends(get_auth_service)
):
    """List all users (admin only)."""
    users = []
    for user in auth_service.user_manager.users.values():
        users.append(UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            roles=user.roles,
        ))
    return users


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    admin_user: User = Depends(require_admin),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Create a new user (admin only)."""
    user = await auth_service.user_manager.create_user(user_data)
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        roles=user.roles,
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    admin_user: User = Depends(require_admin),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get user by ID (admin only)."""
    user = auth_service.user_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        roles=user.roles,
    )


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    admin_user: User = Depends(require_admin),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Update user (admin only)."""
    user = await auth_service.user_manager.update_user(user_id, user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        roles=user.roles,
    )


@router.get("/permissions")
async def get_my_permissions(
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get current user's permissions."""
    permissions = auth_service.rbac.get_user_permissions(current_user.roles)
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "roles": current_user.roles,
        "permissions": permissions,
    }