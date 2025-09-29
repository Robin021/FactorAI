"""
Security middleware and utilities
"""
from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models.user import User, UserInDB
from ..core.auth import verify_token, PermissionChecker, SessionManager
from ..core.database import get_database, get_redis
from ..core.exceptions import AuthenticationException, AuthorizationException


# Security scheme for JWT tokens
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> UserInDB:
    """
    Dependency to get current authenticated user
    """
    if not credentials:
        raise AuthenticationException("No authentication credentials provided")
    
    # Verify JWT token
    token_data = verify_token(credentials.credentials)
    
    # Get user from database
    user_doc = await db.users.find_one({"_id": token_data.user_id})
    if not user_doc:
        raise AuthenticationException("User not found")
    
    user = UserInDB(**user_doc)
    
    # Check if user is active
    if not user.is_active:
        raise AuthenticationException("User account is disabled")
    
    # Store user in request state for logging
    request.state.current_user = user
    
    return user


async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """
    Dependency to get current active user
    """
    if not current_user.is_active:
        raise AuthenticationException("User account is disabled")
    return current_user


def require_permissions(required_permissions: List[str]):
    """
    Dependency factory to require specific permissions
    """
    def permission_checker(
        current_user: UserInDB = Depends(get_current_active_user)
    ) -> UserInDB:
        for permission in required_permissions:
            PermissionChecker.require_permission(current_user.permissions, permission)
        return current_user
    
    return permission_checker


def require_roles(required_roles: List[str]):
    """
    Dependency factory to require specific roles
    """
    def role_checker(
        current_user: UserInDB = Depends(get_current_active_user)
    ) -> UserInDB:
        PermissionChecker.require_role(current_user.role.value, required_roles)
        return current_user
    
    return role_checker


async def get_current_admin_user(
    current_user: UserInDB = Depends(require_roles(["admin"]))
) -> UserInDB:
    """
    Dependency to ensure current user is an admin
    """
    return current_user


async def get_session_manager(
    redis_client = Depends(get_redis)
) -> SessionManager:
    """
    Dependency to get session manager
    """
    return SessionManager(redis_client)


class RateLimiter:
    """Rate limiting utility"""
    
    def __init__(self, redis_client, max_requests: int = 100, window_seconds: int = 3600):
        self.redis = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    async def is_allowed(self, key: str) -> bool:
        """Check if request is allowed under rate limit"""
        current_requests = await self.redis.get(f"rate_limit:{key}")
        
        if current_requests is None:
            # First request in window
            await self.redis.setex(f"rate_limit:{key}", self.window_seconds, 1)
            return True
        
        if int(current_requests) >= self.max_requests:
            return False
        
        # Increment counter
        await self.redis.incr(f"rate_limit:{key}")
        return True
    
    async def get_remaining_requests(self, key: str) -> int:
        """Get remaining requests in current window"""
        current_requests = await self.redis.get(f"rate_limit:{key}")
        if current_requests is None:
            return self.max_requests
        return max(0, self.max_requests - int(current_requests))


def create_rate_limiter(max_requests: int = 100, window_seconds: int = 3600):
    """
    Dependency factory to create rate limiter
    """
    async def rate_limit_checker(
        request: Request,
        redis_client = Depends(get_redis)
    ):
        limiter = RateLimiter(redis_client, max_requests, window_seconds)
        
        # Use IP address as rate limit key
        client_ip = request.client.host
        
        if not await limiter.is_allowed(client_ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
    
    return rate_limit_checker


# Common permission constants
class Permissions:
    """Permission constants"""
    
    # Analysis permissions
    ANALYSIS_CREATE = "analysis.create"
    ANALYSIS_READ = "analysis.read"
    ANALYSIS_UPDATE = "analysis.update"
    ANALYSIS_DELETE = "analysis.delete"
    
    # Configuration permissions
    CONFIG_READ = "config.read"
    CONFIG_UPDATE = "config.update"
    
    # User management permissions
    USER_CREATE = "user.create"
    USER_READ = "user.read"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    
    # System permissions
    SYSTEM_ADMIN = "system.admin"
    SYSTEM_MONITOR = "system.monitor"


# Default role permissions
DEFAULT_ROLE_PERMISSIONS = {
    "admin": ["*"],  # All permissions
    "user": [
        Permissions.ANALYSIS_CREATE,
        Permissions.ANALYSIS_READ,
        Permissions.ANALYSIS_UPDATE,
        Permissions.ANALYSIS_DELETE,
        Permissions.CONFIG_READ,
        Permissions.CONFIG_UPDATE,
    ],
    "viewer": [
        Permissions.ANALYSIS_READ,
        Permissions.CONFIG_READ,
    ]
}