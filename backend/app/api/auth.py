"""
临时认证API - 让前端能正常工作
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

class User(BaseModel):
    id: str
    username: str
    email: str
    role: str

class AuthResponse(BaseModel):
    user: User
    token: str

@router.post("/v1/auth/login")
def login(request: LoginRequest):
    """临时登录API"""
    # 简单的演示登录，任何用户名密码都能登录
    if len(request.username) >= 3 and len(request.password) >= 6:
        return AuthResponse(
            user=User(
                id="demo_user_123",
                username=request.username,
                email=f"{request.username}@demo.com",
                role="user"
            ),
            token="demo_token_123456"
        )
    else:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

@router.get("/v1/auth/me")
def get_current_user():
    """获取当前用户信息"""
    # 返回演示用户
    return User(
        id="demo_user_123",
        username="demo_user",
        email="demo@demo.com",
        role="user"
    )

@router.post("/v1/auth/logout")
def logout():
    """登出"""
    return {"message": "登出成功"}

@router.post("/v1/auth/refresh")
def refresh_token():
    """刷新token"""
    return AuthResponse(
        user=User(
            id="demo_user_123",
            username="demo_user",
            email="demo@demo.com",
            role="user"
        ),
        token="new_demo_token_123456"
    )