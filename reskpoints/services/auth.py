"""Authentication and authorization services for ReskPoints."""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import uuid

import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from pydantic import BaseModel

from reskpoints.core.config import settings
from reskpoints.core.logging import get_logger

logger = get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = settings.JWT_ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_EXPIRE_MINUTES


class User(BaseModel):
    """User data model."""
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    roles: List[str] = []
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    """User creation model."""
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    roles: List[str] = []


class UserUpdate(BaseModel):
    """User update model."""
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    roles: Optional[List[str]] = None


class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    """Token data model."""
    username: Optional[str] = None
    user_id: Optional[str] = None
    roles: List[str] = []


class Role(BaseModel):
    """Role data model."""
    name: str
    description: str
    permissions: List[str] = []


class Permission(BaseModel):
    """Permission data model."""
    name: str
    description: str
    resource: str
    action: str


class PasswordManager:
    """Password management utilities."""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)


class JWTManager:
    """JWT token management."""
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> TokenData:
        """Verify and decode token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            user_id: str = payload.get("user_id")
            roles: List[str] = payload.get("roles", [])
            
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return TokenData(username=username, user_id=user_id, roles=roles)
        
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )


class RBACManager:
    """Role-Based Access Control manager."""
    
    def __init__(self):
        # Default roles and permissions
        self.default_permissions = {
            "metrics:read": Permission(
                name="metrics:read",
                description="Read metrics data",
                resource="metrics",
                action="read"
            ),
            "metrics:write": Permission(
                name="metrics:write",
                description="Submit metrics data",
                resource="metrics",
                action="write"
            ),
            "cost:read": Permission(
                name="cost:read",
                description="Read cost data",
                resource="cost",
                action="read"
            ),
            "cost:write": Permission(
                name="cost:write",
                description="Submit cost data",
                resource="cost",
                action="write"
            ),
            "incidents:read": Permission(
                name="incidents:read",
                description="Read incident data",
                resource="incidents",
                action="read"
            ),
            "incidents:write": Permission(
                name="incidents:write",
                description="Create and update incidents",
                resource="incidents",
                action="write"
            ),
            "admin:manage": Permission(
                name="admin:manage",
                description="Administrative access",
                resource="admin",
                action="manage"
            ),
        }
        
        self.default_roles = {
            "user": Role(
                name="user",
                description="Standard user with basic access",
                permissions=["metrics:read", "cost:read", "incidents:read"]
            ),
            "analyst": Role(
                name="analyst",
                description="Data analyst with read/write access",
                permissions=["metrics:read", "metrics:write", "cost:read", "cost:write", "incidents:read"]
            ),
            "admin": Role(
                name="admin",
                description="Administrator with full access",
                permissions=list(self.default_permissions.keys())
            ),
        }
    
    def has_permission(self, user_roles: List[str], required_permission: str) -> bool:
        """Check if user has required permission."""
        for role_name in user_roles:
            role = self.default_roles.get(role_name)
            if role and required_permission in role.permissions:
                return True
        return False
    
    def get_user_permissions(self, user_roles: List[str]) -> List[str]:
        """Get all permissions for user roles."""
        permissions = set()
        for role_name in user_roles:
            role = self.default_roles.get(role_name)
            if role:
                permissions.update(role.permissions)
        return list(permissions)


class UserManager:
    """User management service."""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.users_by_username: Dict[str, str] = {}
        self.rbac = RBACManager()
        
        # Create default admin user
        self._create_default_users()
    
    def _create_default_users(self):
        """Create default users for development."""
        admin_user = User(
            id=str(uuid.uuid4()),
            username="admin",
            email="admin@reskpoints.com",
            full_name="System Administrator",
            is_active=True,
            is_superuser=True,
            roles=["admin"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        test_user = User(
            id=str(uuid.uuid4()),
            username="testuser",
            email="test@reskpoints.com",
            full_name="Test User",
            is_active=True,
            is_superuser=False,
            roles=["user"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        self.users[admin_user.id] = admin_user
        self.users[test_user.id] = test_user
        self.users_by_username[admin_user.username] = admin_user.id
        self.users_by_username[test_user.username] = test_user.id
        
        logger.info("Created default users: admin, testuser")
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user by username and password."""
        user = self.get_user_by_username(username)
        if not user:
            return None
        
        # For demo purposes, accept "password" as password for all users
        # In production, this should verify against stored hash
        if password != "password":
            return None
        
        return user
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        user_id = self.users_by_username.get(username)
        if user_id:
            return self.users.get(user_id)
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.users.get(user_id)
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        if user_data.username in self.users_by_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            is_active=True,
            is_superuser=False,
            roles=user_data.roles or ["user"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        self.users[user_id] = user
        self.users_by_username[user.username] = user_id
        
        logger.info(f"Created user: {user.username}")
        return user
    
    async def update_user(self, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """Update an existing user."""
        user = self.users.get(user_id)
        if not user:
            return None
        
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.full_name is not None:
            user.full_name = user_data.full_name
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        if user_data.roles is not None:
            user.roles = user_data.roles
        
        user.updated_at = datetime.utcnow()
        
        logger.info(f"Updated user: {user.username}")
        return user


class AuthService:
    """Authentication service."""
    
    def __init__(self):
        self.user_manager = UserManager()
        self.jwt_manager = JWTManager()
        self.rbac = RBACManager()
    
    async def login(self, username: str, password: str) -> Token:
        """Authenticate user and return token."""
        user = await self.user_manager.authenticate_user(username, password)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.jwt_manager.create_access_token(
            data={
                "sub": user.username,
                "user_id": user.id,
                "roles": user.roles,
            },
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    async def get_current_user(self, token: str) -> User:
        """Get current user from token."""
        token_data = self.jwt_manager.verify_token(token)
        user = self.user_manager.get_user_by_username(token_data.username)
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    
    def check_permission(self, user: User, permission: str) -> bool:
        """Check if user has required permission."""
        return self.rbac.has_permission(user.roles, permission)
    
    def require_permission(self, user: User, permission: str):
        """Require user to have specific permission."""
        if not self.check_permission(user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}"
            )


# Global auth service instance
auth_service = AuthService()


def get_auth_service() -> AuthService:
    """Get the global auth service instance."""
    return auth_service