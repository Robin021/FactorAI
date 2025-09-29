"""
Authentication API endpoints
"""
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from jose import jwt, JWTError

from ...models.user import User, UserInDB, UserLogin, Token, UserCreate, UserUpdate, PasswordResetRequest, PasswordReset
from ...core.auth import (
    verify_password,
    get_password_hash,
    create_token_for_user,
    create_access_token,
    SessionManager
)
from ...core.security import (
    get_current_user,
    get_current_active_user,
    get_current_admin_user,
    get_session_manager,
    security,
    create_rate_limiter
)
from ...core.database import get_database
from ...core.exceptions import AuthenticationException, AuthorizationException
from ...app.config import settings

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_database),
    session_manager: SessionManager = Depends(get_session_manager),
    _: None = Depends(create_rate_limiter(max_requests=10, window_seconds=300))  # 10 attempts per 5 minutes
):
    """
    User login endpoint
    """
    # Find user by username
    user_doc = await db.users.find_one({"username": user_credentials.username})
    if not user_doc:
        raise AuthenticationException("Invalid username or password")
    
    user = UserInDB(**user_doc)
    
    # Verify password
    if not verify_password(user_credentials.password, user.password_hash):
        raise AuthenticationException("Invalid username or password")
    
    # Check if user is active
    if not user.is_active:
        raise AuthenticationException("User account is disabled")
    
    # Create access token
    access_token = create_token_for_user(user)
    
    # Create session
    await session_manager.create_session(
        user_id=str(user.id),
        token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    # Update last login time
    await db.users.update_one(
        {"_id": user.id},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    User logout endpoint
    """
    if not credentials:
        raise AuthenticationException("No authentication credentials provided")
    
    # Delete session
    await session_manager.delete_session(credentials.credentials)
    
    return {"message": "Successfully logged out"}


@router.post("/logout-all")
async def logout_all(
    current_user: UserInDB = Depends(get_current_active_user),
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Logout from all devices
    """
    await session_manager.delete_all_user_sessions(str(current_user.id))
    return {"message": "Successfully logged out from all devices"}


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Get current user information
    """
    return User(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        permissions=current_user.permissions,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.put("/me", response_model=User)
async def update_current_user(
    user_update: UserUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Update current user information
    """
    update_data = {}
    
    # Only allow users to update their own basic info
    if user_update.username is not None:
        # Check if username is already taken
        existing_user = await db.users.find_one({
            "username": user_update.username,
            "_id": {"$ne": current_user.id}
        })
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        update_data["username"] = user_update.username
    
    if user_update.email is not None:
        # Check if email is already taken
        existing_user = await db.users.find_one({
            "email": user_update.email,
            "_id": {"$ne": current_user.id}
        })
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken"
            )
        update_data["email"] = user_update.email
    
    if update_data:
        await db.users.update_one(
            {"_id": current_user.id},
            {"$set": update_data}
        )
        
        # Get updated user
        updated_user_doc = await db.users.find_one({"_id": current_user.id})
        updated_user = UserInDB(**updated_user_doc)
        
        return User(
            id=str(updated_user.id),
            username=updated_user.username,
            email=updated_user.email,
            role=updated_user.role,
            permissions=updated_user.permissions,
            is_active=updated_user.is_active,
            created_at=updated_user.created_at,
            last_login=updated_user.last_login
        )
    
    # No changes made
    return User(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        permissions=current_user.permissions,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: UserInDB = Depends(get_current_active_user),
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Refresh access token
    """
    # Create new access token
    access_token = create_token_for_user(current_user)
    
    # Create new session
    await session_manager.create_session(
        user_id=str(current_user.id),
        token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: UserInDB = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Change user password
    """
    # Verify old password
    if not verify_password(old_password, current_user.password_hash):
        raise AuthenticationException("Invalid current password")
    
    # Validate new password
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    # Update password
    new_password_hash = get_password_hash(new_password)
    await db.users.update_one(
        {"_id": current_user.id},
        {"$set": {"password_hash": new_password_hash}}
    )
    
    # Logout from all other sessions for security
    await session_manager.delete_all_user_sessions(str(current_user.id))
    
    return {"message": "Password changed successfully. Please log in again."}


# Admin-only endpoints
@router.post("/users", response_model=User)
async def create_user(
    user_create: UserCreate,
    current_user: UserInDB = Depends(get_current_admin_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Create new user (admin only)
    """
    # Check if username already exists
    existing_user = await db.users.find_one({"username": user_create.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Check if email already exists
    if user_create.email:
        existing_email = await db.users.find_one({"email": user_create.email})
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    # Create user
    user_in_db = UserInDB(
        username=user_create.username,
        email=user_create.email,
        role=user_create.role,
        permissions=user_create.permissions,
        password_hash=get_password_hash(user_create.password),
        is_active=user_create.is_active,
        created_at=datetime.utcnow()
    )
    
    result = await db.users.insert_one(user_in_db.dict(by_alias=True))
    
    # Return created user
    created_user_doc = await db.users.find_one({"_id": result.inserted_id})
    created_user = UserInDB(**created_user_doc)
    
    return User(
        id=str(created_user.id),
        username=created_user.username,
        email=created_user.email,
        role=created_user.role,
        permissions=created_user.permissions,
        is_active=created_user.is_active,
        created_at=created_user.created_at,
        last_login=created_user.last_login
    )


@router.get("/users", response_model=List[User])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: UserInDB = Depends(get_current_admin_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    List all users (admin only)
    """
    cursor = db.users.find().skip(skip).limit(limit)
    users = []
    
    async for user_doc in cursor:
        user = UserInDB(**user_doc)
        users.append(User(
            id=str(user.id),
            username=user.username,
            email=user.email,
            role=user.role,
            permissions=user.permissions,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        ))
    
    return users


@router.get("/users/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    current_user: UserInDB = Depends(get_current_admin_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get user by ID (admin only)
    """
    try:
        user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = UserInDB(**user_doc)
    return User(
        id=str(user.id),
        username=user.username,
        email=user.email,
        role=user.role,
        permissions=user.permissions,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.put("/users/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: UserInDB = Depends(get_current_admin_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Update user (admin only)
    """
    try:
        user_object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    # Check if user exists
    existing_user = await db.users.find_one({"_id": user_object_id})
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    update_data = {}
    
    if user_update.username is not None:
        # Check if username is already taken
        existing_username = await db.users.find_one({
            "username": user_update.username,
            "_id": {"$ne": user_object_id}
        })
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        update_data["username"] = user_update.username
    
    if user_update.email is not None:
        # Check if email is already taken
        existing_email = await db.users.find_one({
            "email": user_update.email,
            "_id": {"$ne": user_object_id}
        })
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken"
            )
        update_data["email"] = user_update.email
    
    if user_update.role is not None:
        update_data["role"] = user_update.role
    
    if user_update.permissions is not None:
        update_data["permissions"] = user_update.permissions
    
    if user_update.is_active is not None:
        update_data["is_active"] = user_update.is_active
    
    if update_data:
        await db.users.update_one(
            {"_id": user_object_id},
            {"$set": update_data}
        )
    
    # Get updated user
    updated_user_doc = await db.users.find_one({"_id": user_object_id})
    updated_user = UserInDB(**updated_user_doc)
    
    return User(
        id=str(updated_user.id),
        username=updated_user.username,
        email=updated_user.email,
        role=updated_user.role,
        permissions=updated_user.permissions,
        is_active=updated_user.is_active,
        created_at=updated_user.created_at,
        last_login=updated_user.last_login
    )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: UserInDB = Depends(get_current_admin_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Delete user (admin only)
    """
    try:
        user_object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    # Prevent self-deletion
    if str(current_user.id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Check if user exists
    existing_user = await db.users.find_one({"_id": user_object_id})
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Delete all user sessions
    await session_manager.delete_all_user_sessions(user_id)
    
    # Delete user
    await db.users.delete_one({"_id": user_object_id})
    
    return {"message": "User deleted successfully"}


@router.post("/request-password-reset")
async def request_password_reset(
    reset_request: PasswordResetRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    session_manager: SessionManager = Depends(get_session_manager),
    _: None = Depends(create_rate_limiter(max_requests=5, window_seconds=3600))  # 5 attempts per hour
):
    """
    Request password reset
    """
    # Find user by email
    user_doc = await db.users.find_one({"email": reset_request.email})
    
    # Always return success to prevent email enumeration
    if not user_doc:
        return {"message": "If the email exists, a password reset link has been sent"}
    
    user = UserInDB(**user_doc)
    
    # Generate reset token (valid for 1 hour)
    reset_token_data = {
        "sub": str(user.id),
        "type": "password_reset",
        "email": user.email
    }
    reset_token = create_access_token(
        reset_token_data,
        expires_delta=timedelta(hours=1)
    )
    
    # Store reset token in Redis (for validation)
    await session_manager.redis.setex(
        f"password_reset:{reset_token}",
        3600,  # 1 hour
        str(user.id)
    )
    
    # TODO: Send email with reset link
    # In a real application, you would send an email here
    # For now, we'll just log the token (remove in production)
    print(f"Password reset token for {user.email}: {reset_token}")
    
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordReset,
    db: AsyncIOMotorDatabase = Depends(get_database),
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Reset password using reset token
    """
    try:
        # Verify reset token
        payload = jwt.decode(
            reset_data.token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        user_id = payload.get("sub")
        token_type = payload.get("type")
        
        if token_type != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )
        
        # Check if token exists in Redis
        stored_user_id = await session_manager.redis.get(f"password_reset:{reset_data.token}")
        if not stored_user_id or stored_user_id.decode() != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )
    
    # Update password
    new_password_hash = get_password_hash(reset_data.new_password)
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password_hash": new_password_hash}}
    )
    
    # Delete reset token
    await session_manager.redis.delete(f"password_reset:{reset_data.token}")
    
    # Delete all user sessions for security
    await session_manager.delete_all_user_sessions(user_id)
    
    return {"message": "Password reset successfully"}