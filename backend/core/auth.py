"""
Authentication and authorization logic
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from ..app.config import settings
from ..models.user import User, UserInDB, TokenData
from ..core.exceptions import AuthenticationException, AuthorizationException


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        username: str = payload.get("username")
        role: str = payload.get("role")
        
        if user_id is None:
            raise AuthenticationException("Invalid token: missing user ID")
        
        token_data = TokenData(user_id=user_id, username=username, role=role)
        return token_data
        
    except JWTError as e:
        raise AuthenticationException(f"Invalid token: {str(e)}")


def create_token_for_user(user: UserInDB) -> str:
    """Create access token for a user"""
    token_data = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role.value,
        "permissions": user.permissions
    }
    return create_access_token(token_data)


class PermissionChecker:
    """Permission checking utility"""
    
    @staticmethod
    def has_permission(user_permissions: list, required_permission: str) -> bool:
        """Check if user has required permission"""
        # Admin users have all permissions
        if "*" in user_permissions:
            return True
        
        # Check exact permission match
        if required_permission in user_permissions:
            return True
        
        # Check wildcard permissions (e.g., "analysis.*" matches "analysis.create")
        for permission in user_permissions:
            if permission.endswith("*"):
                prefix = permission[:-1]
                if required_permission.startswith(prefix):
                    return True
        
        return False
    
    @staticmethod
    def require_permission(user_permissions: list, required_permission: str):
        """Raise exception if user doesn't have required permission"""
        if not PermissionChecker.has_permission(user_permissions, required_permission):
            raise AuthorizationException(
                f"Permission denied: requires '{required_permission}'"
            )
    
    @staticmethod
    def require_role(user_role: str, required_roles: list):
        """Raise exception if user doesn't have required role"""
        if user_role not in required_roles:
            raise AuthorizationException(
                f"Role access denied: requires one of {required_roles}"
            )


class SessionManager:
    """Session management for user authentication"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.session_prefix = "session:"
        self.user_sessions_prefix = "user_sessions:"
    
    async def create_session(self, user_id: str, token: str, expires_in: int = None) -> str:
        """Create a new user session"""
        if expires_in is None:
            expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        
        session_data = {
            "user_id": user_id,
            "token": token,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }
        
        # Store session data
        session_key = f"{self.session_prefix}{token}"
        await self.redis.setex(session_key, expires_in, str(session_data))
        
        # Track user sessions
        user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
        await self.redis.sadd(user_sessions_key, token)
        await self.redis.expire(user_sessions_key, expires_in)
        
        return token
    
    async def get_session(self, token: str) -> Optional[Dict[str, Any]]:
        """Get session data by token"""
        session_key = f"{self.session_prefix}{token}"
        session_data = await self.redis.get(session_key)
        
        if session_data:
            # Update last activity
            await self.update_session_activity(token)
            return eval(session_data)  # Note: In production, use json.loads
        
        return None
    
    async def update_session_activity(self, token: str):
        """Update session last activity timestamp"""
        session_key = f"{self.session_prefix}{token}"
        session_data = await self.redis.get(session_key)
        
        if session_data:
            data = eval(session_data)  # Note: In production, use json.loads
            data["last_activity"] = datetime.utcnow().isoformat()
            
            # Get remaining TTL and update with new data
            ttl = await self.redis.ttl(session_key)
            if ttl > 0:
                await self.redis.setex(session_key, ttl, str(data))
    
    async def delete_session(self, token: str):
        """Delete a user session"""
        session_key = f"{self.session_prefix}{token}"
        session_data = await self.redis.get(session_key)
        
        if session_data:
            data = eval(session_data)  # Note: In production, use json.loads
            user_id = data.get("user_id")
            
            # Remove from user sessions
            if user_id:
                user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
                await self.redis.srem(user_sessions_key, token)
            
            # Delete session
            await self.redis.delete(session_key)
    
    async def delete_all_user_sessions(self, user_id: str):
        """Delete all sessions for a user"""
        user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
        tokens = await self.redis.smembers(user_sessions_key)
        
        # Delete all session tokens
        for token in tokens:
            session_key = f"{self.session_prefix}{token}"
            await self.redis.delete(session_key)
        
        # Delete user sessions set
        await self.redis.delete(user_sessions_key)
    
    async def is_session_valid(self, token: str) -> bool:
        """Check if session is valid"""
        session_key = f"{self.session_prefix}{token}"
        return await self.redis.exists(session_key)