#!/usr/bin/env python3
"""
TradingAgents-CN 服务器
智能股票分析平台 - FastAPI 后端服务
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
import jwt
from datetime import datetime, timedelta
import hashlib
import time
import uuid

# 设置日志（需要在import MongoDB之前，因为异常处理需要用到logger）
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB支持
try:
    from motor.motor_asyncio import AsyncIOMotorClient
    from bson import ObjectId
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    logger.warning("⚠️ MongoDB driver not available, analysis history will not be saved")

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv(project_root / ".env", override=True)

app = FastAPI(
    title="TradingAgents-CN API",
    description="基于多智能体的智能股票分析平台 - 企业级 REST API 服务",
    version="1.0.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 安全
security = HTTPBearer()

# 进度存储 - 使用内存存储（生产环境建议使用Redis）
analysis_progress_store = {}

# Redis客户端（用于与前端API共享进度数据）
redis_client = None
try:
    import redis
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)  # 支持密码认证
    
    # 构建Redis连接参数
    redis_config = {
        "host": REDIS_HOST,
        "port": REDIS_PORT,
        "db": REDIS_DB,
        "decode_responses": True
    }
    
    # 如果有密码，添加密码参数
    if REDIS_PASSWORD:
        redis_config["password"] = REDIS_PASSWORD
    
    redis_client = redis.Redis(**redis_config)
    
    # 测试连接
    redis_client.ping()
    password_info = "with password" if REDIS_PASSWORD else "without password"
    logger.info(f"✅ Redis连接成功: {REDIS_HOST}:{REDIS_PORT} ({password_info})")
except Exception as e:
    logger.warning(f"⚠️ Redis连接失败，进度仅保存在内存中: {e}")
    redis_client = None

# MongoDB客户端（用于持久化分析记录）
mongodb_client = None
mongodb_db = None
if MONGODB_AVAILABLE:
    try:
        MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        DATABASE_NAME = os.getenv("DATABASE_NAME", "tradingagents")
        
        mongodb_client = AsyncIOMotorClient(MONGODB_URL)
        mongodb_db = mongodb_client[DATABASE_NAME]
        
        logger.info(f"✅ MongoDB连接成功: {DATABASE_NAME}")
    except Exception as e:
        logger.warning(f"⚠️ MongoDB连接失败，分析历史将不会保存: {e}")
        mongodb_client = None
        mongodb_db = None

# 模拟用户数据库
fake_users_db = {
    "admin": {
        "username": "admin",
        "email": "admin@tradingagents.cn",
        "password_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",  # "admin123"
        "role": "admin",
        "permissions": ["read", "write", "admin"],
        "is_active": True
    },
    "demo": {
        "username": "demo",
        "email": "demo@tradingagents.cn", 
        "password_hash": "ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f",  # "demo123"
        "role": "user",
        "permissions": ["read"],
        "is_active": True
    }
}

# 数据模型
class HealthResponse(BaseModel):
    status: str
    message: str
    version: str
    environment: str

class AnalysisRequest(BaseModel):
    symbol: str
    market_type: str = "US"
    analysis_type: str = "comprehensive"

class AnalysisResponse(BaseModel):
    status: str
    analysis_id: str
    symbol: str
    message: str

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: Dict[str, Any]

class User(BaseModel):
    username: str
    email: str
    role: str
    permissions: list
    is_active: bool

# 工具函数
def hash_password(password: str) -> str:
    """简单的密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return hash_password(plain_password) == hashed_password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = fake_users_db.get(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# 根路径
@app.get("/")
async def root():
    return {
        "name": "TradingAgents-CN API Server",
        "description": "智能股票分析平台 - 企业级 REST API 服务",
        "version": "1.0.0",
        "architecture": "FastAPI + React",
        "features": ["多智能体分析", "实时数据", "企业SSO", "多市场支持"],
        "docs": "/api/v1/docs",
        "status": "running",
        "auth": "enabled"
    }

# 认证接口
@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """用户登录"""
    user = fake_users_db.get(login_data.username)
    if not user or not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户账户已被禁用"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "permissions": user["permissions"]
        }
    )

@app.post("/api/v1/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """用户登出"""
    return {"message": "成功登出"}

@app.get("/api/v1/auth/me", response_model=User)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    # 优先使用邮箱，如果没有邮箱就使用手机号，都没有就生成默认邮箱
    email = current_user.get("email")
    if not email:
        phone = current_user.get("phone")
        if phone:
            email = f"{phone}@phone.user"
        else:
            email = f"{current_user['username']}@example.com"
    
    return User(
        username=current_user["username"],
        email=email,
        role=current_user["role"],
        permissions=current_user["permissions"],
        is_active=current_user["is_active"]
    )

# 调试用户信息API
@app.get("/api/v1/auth/debug")
async def debug_user_info(current_user: dict = Depends(get_current_user)):
    """调试用户信息 - 查看完整的用户数据"""
    return {
        "current_user": current_user,
        "user_analyses_count": len([
            aid for aid, data in analysis_progress_store.items() 
            if data.get("user") == current_user["username"] or 
               data.get("user_sub") == current_user.get("sub", "")
        ]),
        "total_analyses": len(analysis_progress_store)
    }

# 健康检查
@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        message="TradingAgents-CN API Server is running",
        version="1.0.0",
        environment="development"
    )

# 配置检查
@app.get("/api/v1/config/check")
async def check_config():
    """检查环境变量配置"""
    config_status = {}
    
    # 检查必要的环境变量
    required_vars = [
        "DASHSCOPE_API_KEY",
        "DEEPSEEK_API_KEY", 
        "FINNHUB_API_KEY",
        "TUSHARE_TOKEN"
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value and value != "your_api_key_here":
            config_status[var] = "✅ 已配置"
        else:
            config_status[var] = "❌ 未配置"
    
    # 检查可选环境变量
    optional_vars = [
        "OPENAI_API_KEY",
        "GOOGLE_API_KEY",
        "SILICONFLOW_API_KEY"
    ]
    
    for var in optional_vars:
        value = os.getenv(var)
        if value and value != "your_api_key_here":
            config_status[var] = "✅ 已配置 (可选)"
        else:
            config_status[var] = "⚪ 未配置 (可选)"
    
    return {
        "status": "success",
        "config": config_status,
        "message": "配置检查完成"
    }

# 股票分析接口 (需要认证)
@app.post("/api/v1/analysis/start", response_model=AnalysisResponse)
async def start_analysis(request: AnalysisRequest, current_user: dict = Depends(get_current_user)):
    """启动股票分析 (需要登录)"""
    
    # 检查权限
    if "read" not in current_user["permissions"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有分析权限"
        )
    
    # 基础验证
    if not request.symbol:
        raise HTTPException(status_code=400, detail="股票代码不能为空")
    
    # 生成分析ID
    analysis_id = str(uuid.uuid4())
    
    # 保存到MongoDB数据库（如果可用）
    db_object_id = None
    if mongodb_db is not None:
        try:
            # 创建分析记录
            analysis_doc = {
                "user_id": current_user.get("sub", current_user["username"]),  # 用户唯一标识
                "stock_code": request.symbol.upper(),
                "market_type": request.market_type,
                "status": "pending",  # 初始状态
                "progress": 0.0,
                "config": {
                    "analysis_type": request.analysis_type,
                    "username": current_user["username"]
                },
                "created_at": datetime.utcnow(),
                "result_data": None,
                "error_message": None
            }
            
            result = await mongodb_db.analyses.insert_one(analysis_doc)
            db_object_id = str(result.inserted_id)
            
            # 使用数据库ID作为分析ID，保持一致性
            analysis_id = db_object_id
            
            logger.info(f"✅ 分析记录已保存到数据库: {analysis_id}")
        except Exception as e:
            logger.warning(f"⚠️ 保存分析到数据库失败: {e}，将继续使用内存存储")
    
    # 初始化进度数据（内存和Redis）
    analysis_progress_store[analysis_id] = {
        "analysis_id": analysis_id,
        "symbol": request.symbol.upper(),
        "status": "starting",
        "current_step": 0,
        "total_steps": 7,
        "progress_percentage": 0,
        "current_step_name": "准备中",
        "current_step_description": "正在初始化分析...",
        "elapsed_time": 0,
        "estimated_total_time": 35.0,
        "remaining_time": 35.0,
        "last_message": "分析即将开始...",
        "last_update": time.time(),
        "start_time": time.time(),  # 记录开始时间
        "timestamp": datetime.now().isoformat(),
        "user": current_user["username"],
        "user_sub": current_user.get("sub", ""),
        "market_type": request.market_type,
        "analysis_type": request.analysis_type
    }
    
    # 启动真实分析
    start_real_analysis(analysis_id, request.symbol.upper(), request.market_type, request.analysis_type, current_user["username"])
    
    return AnalysisResponse(
        status="started",
        analysis_id=analysis_id,
        symbol=request.symbol.upper(),
        message=f"用户 {current_user['username']} 已启动 {request.symbol} 的{request.analysis_type}分析"
    )

# 分析状态查询 (需要认证)
@app.get("/api/v1/analysis/{analysis_id}/status")
async def get_analysis_status(analysis_id: str, current_user: dict = Depends(get_current_user)):
    """查询分析状态 (需要登录)"""
    
    # 模拟状态返回
    return {
        "analysis_id": analysis_id,
        "status": "completed",
        "progress": 100,
        "message": "分析已完成",
        "user": current_user["username"],
        "created_at": "2024-01-01T00:00:00Z",
        "completed_at": "2024-01-01T00:05:00Z"
    }

# 分析结果获取 (需要认证)
@app.get("/api/v1/analysis/{analysis_id}/results")
async def get_analysis_results(analysis_id: str, current_user: dict = Depends(get_current_user)):
    """获取分析结果 (需要登录)"""
    
    progress_data = analysis_progress_store.get(analysis_id)
    if not progress_data:
        raise HTTPException(status_code=404, detail="分析未找到")
    
    if progress_data.get("status") != "completed":
        raise HTTPException(status_code=400, detail="分析尚未完成")
    
    # 返回真实的分析结果
    results = progress_data.get("results", {})
    if not results:
        raise HTTPException(status_code=404, detail="分析结果未找到")
    
    return {
        "analysis_id": analysis_id,
        "symbol": progress_data.get("symbol"),
        "status": progress_data.get("status"),
        "user": current_user["username"],
        "results": results,
        "created_at": progress_data.get("timestamp"),
        "completed_at": progress_data.get("timestamp")
    }

# 获取用户的分析历史 (需要认证)
@app.get("/api/v1/analysis/history")
async def get_analysis_history(current_user: dict = Depends(get_current_user)):
    """获取用户的分析历史 (需要登录)"""
    
    user_analyses = []
    current_username = current_user["username"]
    current_user_sub = current_user.get("sub", "")
    
    for analysis_id, data in analysis_progress_store.items():
        # 只返回当前用户的分析记录
        analysis_user = data.get("user", "")
        analysis_user_sub = data.get("user_sub", "")
        
        # 通过用户名或sub匹配（sub更可靠）
        if (analysis_user == current_username or 
            (current_user_sub and analysis_user_sub == current_user_sub)):
            
            analysis_info = {
                "analysis_id": analysis_id,
                "symbol": data.get("symbol", ""),
                "status": data.get("status", "unknown"),
                "progress_percentage": data.get("progress_percentage", 0),
                "created_at": data.get("timestamp", ""),
                "last_update": data.get("last_update", 0),
                "current_step_name": data.get("current_step_name", ""),
                "elapsed_time": data.get("elapsed_time", 0),
                "market_type": data.get("market_type", ""),
                "analysis_type": data.get("analysis_type", "")
            }
            user_analyses.append(analysis_info)
    
    # 按最后更新时间排序，最新的在前面
    user_analyses.sort(key=lambda x: x.get("last_update", 0), reverse=True)
    
    return {
        "analyses": user_analyses,
        "total": len(user_analyses)
    }

# Authing SSO 回调处理
@app.get("/api/v1/auth/authing/callback")
async def authing_callback(code: str, state: str = None):
    """处理 Authing SSO 回调"""
    try:
        # 从环境变量读取 Authing 配置
        authing_app_id = os.getenv("AUTHING_APP_ID")
        authing_app_secret = os.getenv("AUTHING_APP_SECRET")
        authing_app_host = os.getenv("AUTHING_APP_HOST")
        authing_redirect_uri = os.getenv("AUTHING_REDIRECT_URI")
        
        if not all([authing_app_id, authing_app_host]):
            # 返回错误页面
            error_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>SSO 登录失败</title>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                    .error {{ color: #d32f2f; }}
                </style>
            </head>
            <body>
                <h2 class="error">SSO 登录失败</h2>
                <p>Authing 配置不完整，请联系管理员</p>
                <button onclick="window.location.href='http://localhost:3000/login'">返回登录</button>
            </body>
            </html>
            """
            return HTMLResponse(content=error_html)
        
        # 调用 Authing API 来交换 code 获取用户信息
        try:
            import requests
            
            # 第一步：用 code 换取 access_token
            token_url = f"{authing_app_host}/oidc/token"
            token_data = {
                "client_id": authing_app_id,
                "client_secret": authing_app_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": authing_redirect_uri
            }
            
            logger.info(f"正在调用 Authing Token API: {token_url}")
            logger.info(f"Token 请求数据: {token_data}")
            
            token_response = requests.post(token_url, data=token_data)
            logger.info(f"Token API 响应状态: {token_response.status_code}")
            logger.info(f"Token API 响应内容: {token_response.text}")
            
            if not token_response.ok:
                raise Exception(f"获取token失败: {token_response.text}")
            
            token_info = token_response.json()
            access_token = token_info.get("access_token")
            
            if not access_token:
                raise Exception("未获取到access_token")
            
            # 第二步：用 access_token 获取用户信息
            userinfo_url = f"{authing_app_host}/oidc/me"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            logger.info(f"正在调用 Authing UserInfo API: {userinfo_url}")
            logger.info(f"UserInfo 请求头: {headers}")
            
            userinfo_response = requests.get(userinfo_url, headers=headers)
            logger.info(f"UserInfo API 响应状态: {userinfo_response.status_code}")
            logger.info(f"UserInfo API 响应内容: {userinfo_response.text}")
            
            if not userinfo_response.ok:
                raise Exception(f"获取用户信息失败: {userinfo_response.text}")
            
            user_info = userinfo_response.json()
            logger.info(f"解析后的用户信息: {user_info}")
            
            # 提取用户信息 - 使用标准化的逻辑确保一致性
            sub = user_info.get("sub")
            if not sub:
                raise Exception("用户信息中缺少 sub 字段")
            
            # 用户名优先级：preferred_username > username > 手机号 > sub
            # 改进：如果用户名相关字段都为空，使用手机号作为用户名
            username = (
                user_info.get("preferred_username") or 
                user_info.get("username") or 
                user_info.get("phone_number") or 
                sub
            )
            
            # 显示名称优先级：name > nickname > 手机号 > username
            display_name = (
                user_info.get("name") or 
                user_info.get("nickname") or 
                user_info.get("phone_number") or 
                username
            )
            
            # 邮箱处理 - 改进：如果邮箱为空，使用手机号生成邮箱
            email = user_info.get("email")
            if not email:
                phone = user_info.get("phone_number")
                if phone:
                    # 使用手机号生成邮箱
                    email = f"{phone}@authing.demo"
                else:
                    # 最后回退到用户名生成邮箱
                    email = f"{username}@authing.demo"
            
            authing_user_info = {
                "sub": sub,  # 唯一标识符
                "username": username,  # 用户名
                "display_name": display_name,  # 显示名称
                "email": email,  # 邮箱
                "name": display_name,  # 兼容性字段
                "phone": user_info.get("phone_number"),  # 手机号
                "avatar": user_info.get("picture"),  # 头像
                "roles": user_info.get("roles", []),  # 角色列表
                "extended_fields": user_info.get("extended_fields", {})  # 扩展字段
            }
            
        except Exception as e:
            logger.error(f"Authing API调用失败: {e}")
            # 返回错误页面而不是使用模拟数据
            error_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>SSO 登录失败</title>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                    .error {{ color: #d32f2f; }}
                    .details {{ background: #f5f5f5; padding: 20px; margin: 20px; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <h2 class="error">SSO 登录失败</h2>
                <p>Authing API 调用失败</p>
                <div class="details">
                    <strong>错误详情:</strong><br>
                    {str(e)}
                </div>
                <p>请检查:</p>
                <ul style="text-align: left; display: inline-block;">
                    <li>Authing 应用配置是否正确</li>
                    <li>用户是否存在并已激活</li>
                    <li>网络连接是否正常</li>
                </ul>
                <button onclick="window.location.href='http://localhost:3000/login'">返回登录</button>
            </body>
            </html>
            """
            return HTMLResponse(content=error_html)
        
        # 创建或更新本地用户 - 使用标准化的用户信息
        user_data = {
            "username": authing_user_info["username"],
            "email": authing_user_info["email"],
            "name": authing_user_info["display_name"],
            "phone": authing_user_info.get("phone", ""),
            "sub": authing_user_info["sub"],  # 唯一标识符
            "avatar": authing_user_info.get("avatar", ""),
            "roles": authing_user_info.get("roles", []),
            "extended_fields": authing_user_info.get("extended_fields", {}),
            "role": "user",  # 默认角色
            "permissions": ["read"],
            "is_active": True,
            "auth_type": "sso",
            "auth_provider": "authing"
        }
        
        # 将用户添加到模拟数据库（实际使用时应该存储到真实数据库）
        fake_users_db[user_data["username"]] = {
            **user_data,
            "password_hash": "sso_user",  # SSO 用户不需要密码
        }
        
        # 生成访问令牌
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_data["username"]}, expires_delta=access_token_expires
        )
        
        # 返回成功页面，自动跳转到前端并传递 token
        success_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>SSO 登录成功</title>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    background: white;
                    border-radius: 20px;
                    padding: 40px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.15);
                    text-align: center;
                    max-width: 500px;
                    width: 100%;
                }}
                .spinner {{
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #667eea;
                    border-radius: 50%;
                    width: 50px;
                    height: 50px;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 20px;
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
                .success {{
                    color: #2e7d32;
                    margin: 20px 0;
                }}
                .user-info {{
                    background: #f5f5f5;
                    padding: 15px;
                    border-radius: 10px;
                    margin: 20px 0;
                    text-align: left;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="spinner" id="spinner"></div>
                <h2 class="success">🎉 SSO 登录成功！</h2>
                <div class="user-info">
                    <strong>用户信息：</strong><br>
                    用户名: {user_data['username']}<br>
                    邮箱: {user_data['email']}<br>
                    角色: {user_data['role']}<br>
                    权限: {', '.join(user_data['permissions'])}
                </div>
                <p id="status">正在跳转到系统首页...</p>
            </div>

            <script>
                // 保存 token 到 localStorage
                try {{
                    localStorage.setItem('auth_token', '{access_token}');
                    localStorage.setItem('user_info', JSON.stringify({user_data}));
                    console.log('Token 已保存到 localStorage');
                }} catch (e) {{
                    console.warn('无法保存到 localStorage:', e);
                }}

                // 3秒后跳转到前端应用
                let countdown = 3;
                const statusElement = document.getElementById('status');
                
                const timer = setInterval(() => {{
                    countdown--;
                    statusElement.textContent = `正在跳转到系统首页... (${{countdown}}秒)`;
                    
                    if (countdown <= 0) {{
                        clearInterval(timer);
                        window.location.href = 'http://localhost:3000/dashboard';
                    }}
                }}, 1000);

                // 也可以点击立即跳转
                document.addEventListener('click', () => {{
                    clearInterval(timer);
                    window.location.href = 'http://localhost:3000/dashboard';
                }});
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=success_html)
        
    except Exception as e:
        # 返回错误页面
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>SSO 登录失败</title>
            <meta charset="UTF-8">
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    text-align: center; 
                    padding: 50px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    margin: 0;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .container {{
                    background: white;
                    padding: 40px;
                    border-radius: 20px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.15);
                }}
                .error {{ color: #d32f2f; }}
                .btn {{
                    background: #667eea;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 16px;
                    margin: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2 class="error">❌ SSO 登录失败</h2>
                <p>错误信息: {str(e)}</p>
                <button class="btn" onclick="window.location.href='http://localhost:3000/login'">返回登录</button>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html)

# 分析进度轮询接口
@app.get("/api/v1/analysis/{analysis_id}/progress")
async def get_analysis_progress(analysis_id: str, current_user: dict = Depends(get_current_user)):
    """获取分析进度 (轮询接口)"""
    
    progress_data = analysis_progress_store.get(analysis_id)
    if not progress_data:
        raise HTTPException(status_code=404, detail="分析进度未找到")
    
    # 完全不记录进度轮询日志，避免刷屏
    
    return progress_data

# 取消分析接口
@app.post("/api/v1/analysis/{analysis_id}/cancel")
async def cancel_analysis(analysis_id: str, current_user: dict = Depends(get_current_user)):
    """取消分析任务"""
    
    progress_data = analysis_progress_store.get(analysis_id)
    if not progress_data:
        raise HTTPException(status_code=404, detail="分析任务未找到")
    
    # 检查分析是否已经完成
    if progress_data.get("status") in ["completed", "failed", "cancelled"]:
        return {"message": f"分析已经{progress_data.get('status')}，无法取消"}
    
    # 更新状态为已取消
    progress_data["status"] = "cancelled"
    progress_data["message"] = "分析已被用户取消"
    progress_data["end_time"] = time.time()
    
    # 更新存储
    analysis_progress_store[analysis_id] = progress_data
    
    return {"message": "分析已成功取消"}

# PDF报告下载接口
@app.get("/api/v1/analysis/{analysis_id}/download/pdf")
async def download_analysis_pdf(analysis_id: str, current_user: dict = Depends(get_current_user)):
    """下载分析报告PDF"""
    from fastapi.responses import FileResponse
    import os
    from pathlib import Path
    
    progress_data = analysis_progress_store.get(analysis_id)
    if not progress_data:
        raise HTTPException(status_code=404, detail="分析未找到")
    
    if progress_data.get("status") != "completed":
        raise HTTPException(status_code=400, detail="分析尚未完成")
    
    # 查找PDF文件
    symbol = progress_data.get("symbol", "UNKNOWN")
    results_dir = Path("results") / symbol / "2025-09-29" / "reports"
    
    # 查找PDF文件
    pdf_files = list(results_dir.glob("*.pdf"))
    if not pdf_files:
        # 如果没有PDF，尝试查找markdown文件并提示
        md_files = list(results_dir.glob("*.md"))
        if md_files:
            raise HTTPException(status_code=404, detail="PDF文件未生成，但有Markdown报告可用")
        else:
            raise HTTPException(status_code=404, detail="报告文件未找到")
    
    # 返回第一个找到的PDF文件
    pdf_file = pdf_files[0]
    if not pdf_file.exists():
        raise HTTPException(status_code=404, detail="PDF文件不存在")
    
    return FileResponse(
        path=str(pdf_file),
        filename=f"{symbol}_analysis_report.pdf",
        media_type="application/pdf"
    )

# 获取报告文件列表
@app.get("/api/v1/analysis/{analysis_id}/files")
async def get_analysis_files(analysis_id: str, current_user: dict = Depends(get_current_user)):
    """获取分析报告文件列表"""
    
    progress_data = analysis_progress_store.get(analysis_id)
    if not progress_data:
        raise HTTPException(status_code=404, detail="分析未找到")
    
    if progress_data.get("status") != "completed":
        raise HTTPException(status_code=400, detail="分析尚未完成")
    
    # 查找报告文件
    symbol = progress_data.get("symbol", "UNKNOWN")
    results_dir = Path("results") / symbol / "2025-09-29" / "reports"
    
    files = []
    if results_dir.exists():
        for file_path in results_dir.iterdir():
            if file_path.is_file():
                files.append({
                    "name": file_path.name,
                    "type": file_path.suffix.lower(),
                    "size": file_path.stat().st_size,
                    "url": f"/api/v1/analysis/{analysis_id}/download/{file_path.name}"
                })
    
    return {"files": files}

# 下载任意报告文件
@app.get("/api/v1/analysis/{analysis_id}/download/{filename}")
async def download_analysis_file(analysis_id: str, filename: str, current_user: dict = Depends(get_current_user)):
    """下载指定的分析报告文件"""
    from fastapi.responses import FileResponse
    import os
    from pathlib import Path
    
    progress_data = analysis_progress_store.get(analysis_id)
    if not progress_data:
        raise HTTPException(status_code=404, detail="分析未找到")
    
    # 安全检查：防止路径遍历攻击
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="无效的文件名")
    
    # 查找文件
    symbol = progress_data.get("symbol", "UNKNOWN")
    results_dir = Path("results") / symbol / "2025-09-29" / "reports"
    file_path = results_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 确定媒体类型
    media_type = "application/octet-stream"
    if filename.endswith(".pdf"):
        media_type = "application/pdf"
    elif filename.endswith(".md"):
        media_type = "text/markdown"
    elif filename.endswith(".txt"):
        media_type = "text/plain"
    elif filename.endswith(".json"):
        media_type = "application/json"
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type
    )

# 启动真实分析
def start_real_analysis(analysis_id: str, symbol: str, market_type: str, analysis_type: str, username: str):
    """启动真实的股票分析"""
    import threading
    import time
    from datetime import datetime
    
    def analysis_worker():
        try:
            # 导入真实的分析函数
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            from web.utils.analysis_runner import run_stock_analysis
            
            # 进度回调函数
            def progress_callback(message, step=None, total_steps=None):
                # 检查是否已被取消
                if analysis_progress_store[analysis_id].get("status") == "cancelled":
                    logger.info(f"Analysis {analysis_id} was cancelled, stopping execution")
                    raise Exception("Analysis was cancelled by user")
                    
                current_time = time.time()
                start_time = analysis_progress_store[analysis_id].get("start_time", current_time)
                elapsed_time = current_time - start_time
                
                # 计算进度百分比
                if step is not None and total_steps is not None and total_steps > 0:
                    # 使用传入的步骤信息计算精确进度
                    progress_percentage = min((step / total_steps), 1.0)  # 返回0-1之间的小数
                    current_step_num = step
                    total_step_num = total_steps
                else:
                    # 根据消息内容估算进度（返回0-1之间的小数）
                    current_progress = analysis_progress_store[analysis_id].get("progress_percentage", 0)
                    
                    # 更全面的消息匹配逻辑 - 详细进度步骤
                    if "验证" in message or "预获取" in message or "股票代码" in message:
                        progress_percentage = 0.05
                        current_step_num = 1
                    elif "数据准备完成" in message or "✅ 数据准备完成" in message:
                        progress_percentage = 0.08
                        current_step_num = 1
                    elif "开始股票分析" in message:
                        progress_percentage = 0.1
                        current_step_num = 2
                    elif "预估分析成本" in message or "成本" in message:
                        progress_percentage = 0.12
                        current_step_num = 2
                    elif "环境变量" in message or "检查环境变量" in message:
                        progress_percentage = 0.15
                        current_step_num = 2
                    elif "环境变量验证通过" in message:
                        progress_percentage = 0.18
                        current_step_num = 2
                    elif "配置分析参数" in message or "配置" in message:
                        progress_percentage = 0.2
                        current_step_num = 3
                    elif "创建必要的目录" in message or "📁" in message:
                        progress_percentage = 0.22
                        current_step_num = 3
                    elif "准备分析" in message and ("A股" in message or "港股" in message or "美股" in message):
                        progress_percentage = 0.25
                        current_step_num = 3
                    elif "初始化分析引擎" in message or "初始化" in message or "引擎" in message:
                        progress_percentage = 0.3
                        current_step_num = 4
                    elif "开始分析" in message and "股票" in message:
                        progress_percentage = 0.35
                        current_step_num = 4
                    # 新增：更详细的分析步骤识别
                    elif "市场分析师" in message or "市场数据" in message or "技术指标" in message:
                        progress_percentage = 0.4
                        current_step_num = 5
                    elif "基本面分析师" in message or "财务数据" in message or "财务比率" in message:
                        progress_percentage = 0.5
                        current_step_num = 6
                    elif "技术分析师" in message or "技术形态" in message or "MACD" in message or "RSI" in message:
                        progress_percentage = 0.6
                        current_step_num = 7
                    elif "情绪分析师" in message or "新闻分析" in message or "情绪" in message:
                        progress_percentage = 0.65
                        current_step_num = 7
                    elif "智能体" in message or "协作分析" in message or "多智能体" in message:
                        progress_percentage = 0.7
                        current_step_num = 8
                    elif "分析完成，正在整理结果" in message or "整理结果" in message:
                        progress_percentage = 0.75
                        current_step_num = 8
                    elif "生成图表" in message or "可视化" in message:
                        progress_percentage = 0.8
                        current_step_num = 9
                    elif "编写报告" in message or "生成报告" in message:
                        progress_percentage = 0.85
                        current_step_num = 9
                    elif "记录使用成本" in message:
                        progress_percentage = 0.88
                        current_step_num = 9
                    elif "正在保存分析报告" in message or "保存分析报告" in message:
                        progress_percentage = 0.9
                        current_step_num = 9
                    elif "报告已保存" in message or "本地报告已保存" in message:
                        progress_percentage = 0.95
                        current_step_num = 10
                    elif "分析成功完成" in message or "✅ 分析成功完成" in message:
                        progress_percentage = 1.0
                        current_step_num = 10
                    elif "完成" in message:
                        progress_percentage = 1.0
                        current_step_num = 10
                    else:
                        # 根据当前进度平滑递增，避免跳跃
                        current_progress = analysis_progress_store[analysis_id].get("progress_percentage", 0)
                        if current_progress < 0.7:  # 分析阶段，缓慢递增
                            progress_percentage = min(current_progress + 0.02, 0.7)
                        else:  # 后期阶段，保持当前进度
                            progress_percentage = current_progress
                        current_step_num = analysis_progress_store[analysis_id].get("current_step", 1)

                # 心跳消息：仅更新时间与提示，不改变百分比（保证前端看到“在进行”但不编造进度）
                if isinstance(message, str) and "HEARTBEAT" in message:
                    progress_percentage = analysis_progress_store[analysis_id].get("progress_percentage", 0)
                    # 保持当前步骤不变
                    current_step_num = analysis_progress_store[analysis_id].get("current_step", current_step_num)
                    
                    total_step_num = 10
                
                # 确保进度不会倒退
                current_progress = analysis_progress_store[analysis_id].get("progress_percentage", 0)
                progress_percentage = max(progress_percentage, current_progress)
                
                # 确保步骤数也不会倒退
                current_step_stored = analysis_progress_store[analysis_id].get("current_step", 0)
                current_step_num = max(current_step_num, current_step_stored)
                
                # 计算预计剩余时间
                if progress_percentage > 0 and progress_percentage < 1.0:
                    estimated_total_time = elapsed_time / progress_percentage
                    estimated_remaining = max(0, estimated_total_time - elapsed_time)
                else:
                    estimated_remaining = 0
                
                # 更新进度数据
                # 构建步骤结构化信息（等权）。如果具体权重未来可用，可在此替换为权重表。
                steps_list = []
                for idx in range(1, total_step_num + 1):
                    if progress_percentage >= 1.0 or idx < current_step_num:
                        step_status = "completed"
                    elif idx == current_step_num and progress_percentage < 1.0:
                        step_status = "running"
                    else:
                        step_status = "pending"
                    steps_list.append({
                        "index": idx,
                        "name": f"步骤 {idx}",
                        "status": step_status
                    })

                progress_data = {
                    "status": "running" if progress_percentage < 1.0 else "completed",
                    "current_step": current_step_num,
                    "total_steps": total_step_num,
                    "progress_percentage": progress_percentage,  # 保持0-1之间的小数
                    "progress": progress_percentage * 100,  # 同时提供0-100格式供兼容
                    "current_step_name": message.split("...")[0] if "..." in message else message[:50],
                    "message": message,
                    "elapsed_time": int(elapsed_time),
                    "estimated_time_remaining": int(estimated_remaining),
                    "estimated_remaining": estimated_remaining,  # 保留旧字段兼容性
                    "steps": steps_list,
                    "last_update": current_time,
                    "timestamp": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                
                # 更新内存存储
                analysis_progress_store[analysis_id].update(progress_data)
                
                # 同时写入Redis，供前端API读取
                if redis_client:
                    try:
                        import json
                        # 使用与backend API相同的Redis键格式
                        redis_key = f"analysis_progress:{analysis_id}"
                        redis_client.setex(redis_key, 3600, json.dumps(progress_data))  # 1小时过期
                    except Exception as redis_error:
                        # Redis写入失败不应该影响分析继续进行
                        logger.warning(f"Failed to write progress to Redis: {redis_error}")
                
                # 记录进度变化，包括调试信息
                progress_percent_display = int(progress_percentage * 100)
                current_percent_display = int(current_progress * 100)
                
                # 如果进度有变化，记录详细日志
                if progress_percent_display != current_percent_display:
                    logger.info(f"分析 {analysis_id} 进度更新: {current_percent_display}% -> {progress_percent_display}% - {message}")
                elif progress_percent_display % 20 == 0 or progress_percentage >= 1.0:
                    # 每20%或完成时记录一次
                    logger.info(f"分析 {analysis_id} 进度: {progress_percent_display}% - {message}")
                else:
                    # 其他情况只记录debug级别
                    logger.debug(f"分析 {analysis_id} 进度保持: {progress_percent_display}% - {message}")
            
            # 设置分析参数
            analysis_date = datetime.now().strftime("%Y-%m-%d")
            analysts = ["market", "fundamentals", "technical", "sentiment", "risk"]  # 默认分析师
            research_depth = 2  # 基础分析
            llm_provider = "deepseek"  # 使用DeepSeek
            llm_model = "deepseek-chat"
            
            # 根据market_type设置
            if market_type.upper() == "CN":
                market_type_name = "A股"
            elif market_type.upper() == "HK":
                market_type_name = "港股"
            else:
                market_type_name = "美股"
            
            # 记录开始时间
            analysis_progress_store[analysis_id]["start_time"] = time.time()
            
            logger.info(f"开始真实分析: {symbol} ({market_type_name}) - 用户: {username}")
            
            # 在开始分析前检查是否已被取消
            if analysis_progress_store[analysis_id].get("status") == "cancelled":
                logger.info(f"Analysis {analysis_id} was cancelled before execution")
                return
            
            # 执行真实分析
            result = run_stock_analysis(
                stock_symbol=symbol,
                analysis_date=analysis_date,
                analysts=analysts,
                research_depth=research_depth,
                llm_provider=llm_provider,
                llm_model=llm_model,
                market_type=market_type_name,
                progress_callback=progress_callback
            )
            
            # 保存分析结果
            final_status = "completed" if result.get("success", False) else "failed"
            final_message = "分析完成！" if result.get("success", False) else f"分析失败: {result.get('error', '未知错误')}"
            
            final_progress_data = {
                "status": final_status,
                "progress_percentage": 1.0,
                "progress": 100,
                "current_step": 10,
                "total_steps": 10,
                "message": final_message,
                "current_step_name": final_message,
                "last_message": final_message,
                "results": result,
                "last_update": time.time(),
                "timestamp": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "elapsed_time": int(time.time() - analysis_progress_store[analysis_id].get("start_time", time.time())),
                "estimated_time_remaining": 0,
                "estimated_remaining": 0
            }
            
            analysis_progress_store[analysis_id].update(final_progress_data)
            
            # 同时写入Redis
            if redis_client:
                try:
                    import json
                    redis_key = f"analysis_progress:{analysis_id}"
                    redis_client.setex(redis_key, 3600, json.dumps(final_progress_data))
                    logger.info(f"✅ 分析完成状态已写入Redis: {analysis_id}")
                except Exception as redis_error:
                    logger.warning(f"Failed to write completion status to Redis: {redis_error}")
            
            # 更新MongoDB数据库状态
            if mongodb_db is not None:
                try:
                    import asyncio
                    from bson import ObjectId
                    
                    update_data = {
                        "status": final_status,
                        "progress": 100.0,
                        "completed_at": datetime.utcnow()
                    }
                    
                    # 如果分析成功，保存结果
                    if result.get('success', False):
                        update_data["result_data"] = result
                    else:
                        update_data["error_message"] = result.get('error', '未知错误')
                    
                    # 使用asyncio运行异步更新
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(
                        mongodb_db.analyses.update_one(
                            {"_id": ObjectId(analysis_id)},
                            {"$set": update_data}
                        )
                    )
                    loop.close()
                    
                    logger.info(f"✅ 分析完成状态已更新到数据库: {analysis_id}")
                except Exception as db_error:
                    logger.warning(f"⚠️ 更新数据库状态失败: {db_error}")
            
            logger.info(f"分析 {analysis_id} 完成，成功: {result.get('success', False)}")
            
        except Exception as e:
            logger.error(f"分析 {analysis_id} 执行失败: {e}")
            error_progress_data = {
                "status": "failed",
                "progress_percentage": 0,
                "progress": 0,
                "message": f"分析失败: {str(e)}",
                "last_message": f"分析失败: {str(e)}",
                "error": str(e),
                "last_update": time.time(),
                "timestamp": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            analysis_progress_store[analysis_id].update(error_progress_data)
            
            # 同时写入Redis
            if redis_client:
                try:
                    import json
                    redis_key = f"analysis_progress:{analysis_id}"
                    redis_client.setex(redis_key, 3600, json.dumps(error_progress_data))
                except Exception as redis_error:
                    logger.warning(f"Failed to write error status to Redis: {redis_error}")
            
            # 更新MongoDB数据库状态
            if mongodb_db is not None:
                try:
                    import asyncio
                    from bson import ObjectId
                    
                    # 使用asyncio运行异步更新
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(
                        mongodb_db.analyses.update_one(
                            {"_id": ObjectId(analysis_id)},
                            {"$set": {
                                "status": "failed",
                                "error_message": str(e),
                                "completed_at": datetime.utcnow()
                            }}
                        )
                    )
                    loop.close()
                    
                    logger.info(f"✅ 分析失败状态已更新到数据库: {analysis_id}")
                except Exception as db_error:
                    logger.warning(f"⚠️ 更新数据库状态失败: {db_error}")
    
    # 启动后台线程
    thread = threading.Thread(target=analysis_worker, daemon=True)
    thread.start()
    logger.info(f"启动真实分析: {analysis_id} - {symbol} ({market_type})")

# 获取支持的股票市场
@app.get("/api/v1/markets")
async def get_supported_markets():
    """获取支持的股票市场"""
    return {
        "markets": [
            {
                "code": "US",
                "name": "美股",
                "description": "美国股票市场",
                "examples": ["AAPL", "GOOGL", "MSFT", "TSLA"]
            },
            {
                "code": "CN",
                "name": "A股",
                "description": "中国A股市场", 
                "examples": ["000001", "000002", "600000", "600036"]
            },
            {
                "code": "HK",
                "name": "港股",
                "description": "香港股票市场",
                "examples": ["0700", "0941", "1299", "2318"]
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 TradingAgents-CN 服务器启动中...")
    print("📈 智能股票分析平台 - 企业级 API 服务")
    print("🌐 API 文档: http://localhost:8000/api/v1/docs")
    print("🔧 健康检查: http://localhost:8000/api/v1/health")
    print("⚙️ 配置检查: http://localhost:8000/api/v1/config/check")
    print("🔐 认证支持: 用户名密码 + Authing SSO")
    print("📊 支持市场: A股 + 美股 + 港股")
    print("=" * 50)
    
    uvicorn.run(
        "tradingagents_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="critical"  # 几乎不显示日志
    )