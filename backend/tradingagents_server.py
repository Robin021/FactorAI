#!/usr/bin/env python3
"""
TradingAgents-CN 服务器
智能股票分析平台 - FastAPI 后端服务
"""

from fastapi import FastAPI, HTTPException, Depends, status, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from jose import jwt
from datetime import datetime, timedelta
import hashlib
import time
import uuid

# 设置统一日志系统（优先读取 TRADINGAGENTS_LOG_LEVEL 等环境变量）
try:
    from tradingagents.utils.logging_init import init_logging
    from tradingagents.utils.logging_manager import get_logger
    init_logging()
    logger = get_logger('backend.tradingagents_server')
except Exception:
    # 回退到基础日志，避免启动失败
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# MongoDB支持
try:
    from motor.motor_asyncio import AsyncIOMotorClient
    from bson import ObjectId
    MONGODB_AVAILABLE = True
    logger.info("✅ Motor (异步MongoDB驱动) 可用")
except ImportError:
    try:
        # 如果motor不可用，尝试使用pymongo
        from pymongo import MongoClient
        from bson import ObjectId
        MONGODB_AVAILABLE = True
        logger.info("✅ PyMongo (同步MongoDB驱动) 可用，将使用同步操作")
        # 定义一个简单的异步包装器
        class AsyncIOMotorClient:
            def __init__(self, url):
                self._sync_client = MongoClient(url)
                self._is_sync = True  # 标记这是同步客户端
            
            def __getitem__(self, name):
                return self._sync_client[name]
            
            @property
            def admin(self):
                return self._sync_client.admin
            
            def close(self):
                self._sync_client.close()
        
        # 定义统一的MongoDB操作函数
        def safe_mongodb_operation(operation_func, *args, **kwargs):
            """安全执行MongoDB操作，自动处理同步/异步"""
            try:
                if hasattr(mongodb_client, '_is_sync') and mongodb_client._is_sync:
                    # 同步操作
                    return operation_func(*args, **kwargs)
                else:
                    # 异步操作
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(operation_func(*args, **kwargs))
                    loop.close()
                    return result
            except Exception as e:
                logger.error(f"MongoDB操作失败: {e}")
                raise e
    except ImportError:
        MONGODB_AVAILABLE = False
        logger.warning("⚠️ MongoDB driver not available, analysis history will not be saved")

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载环境变量 - 支持多种路径（尽早加载，便于日志等级等生效）
env_file_paths = [
    project_root / ".env",  # backend/.env (当前目录)
    project_root.parent / ".env",  # 项目根目录/.env
    Path("/app/.env"),  # Docker 环境中的路径
]

env_file_loaded = False
for env_file in env_file_paths:
    if env_file.exists():
        load_dotenv(env_file, override=True)
        print(f"✅ 已加载环境变量文件: {env_file}")
        env_file_loaded = True
        break

if not env_file_loaded:
    print("⚠️ 未找到 .env 文件，使用默认环境变量")

# 依据环境变量初始化统一日志（确保TRADINGAGENTS_LOG_LEVEL生效）
try:
    from tradingagents.utils.logging_init import init_logging
    from tradingagents.utils.logging_manager import get_logger
    init_logging()
    logger = get_logger('backend.tradingagents_server')
    logger.info(f"日志级别: {os.getenv('TRADINGAGENTS_LOG_LEVEL', 'INFO')}")
except Exception:
    pass

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
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://47.239.62.97",  # 生产环境前端
        "http://47.239.62.97:80",  # 明确指定端口
        "https://47.239.62.97",  # 如果使用 HTTPS
    ],
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
        DATABASE_NAME = os.getenv("MONGODB_DB_NAME", os.getenv("DATABASE_NAME", "tradingagents"))
        
        mongodb_client = AsyncIOMotorClient(MONGODB_URL)
        mongodb_db = mongodb_client[DATABASE_NAME]
        
        # 测试连接 - 使用同步方式避免motor依赖问题
        try:
            # 如果motor可用，使用异步测试
            import asyncio
            async def test_connection():
                try:
                    if hasattr(mongodb_client, '_is_sync') and mongodb_client._is_sync:
                        # 同步客户端，直接调用
                        mongodb_client.admin.command('ping')
                        return True
                    else:
                        # 异步客户端
                        await mongodb_client.admin.command('ping')
                        return True
                except Exception as e:
                    logger.error(f"MongoDB ping失败: {e}")
                    return False
            
            # 在新的事件循环中测试连接
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            connection_ok = loop.run_until_complete(test_connection())
            loop.close()
            
            if connection_ok:
                logger.info(f"✅ MongoDB连接成功: {DATABASE_NAME} at {MONGODB_URL}")
            else:
                logger.warning(f"⚠️ MongoDB连接测试失败，分析历史将不会保存")
                mongodb_client = None
                mongodb_db = None
        except Exception as test_error:
            # 如果异步测试失败，尝试同步测试
            logger.warning(f"异步测试失败，尝试同步测试: {test_error}")
            try:
                from pymongo import MongoClient
                sync_client = MongoClient(MONGODB_URL)
                sync_client.admin.command('ping')
                sync_client.close()
                logger.info(f"✅ MongoDB连接成功 (同步测试): {DATABASE_NAME} at {MONGODB_URL}")
            except Exception as sync_error:
                logger.warning(f"⚠️ MongoDB连接失败，分析历史将不会保存: {sync_error}")
                mongodb_client = None
                mongodb_db = None
            
    except Exception as e:
        logger.warning(f"⚠️ MongoDB连接失败，分析历史将不会保存: {e}")
        mongodb_client = None
        mongodb_db = None

# ======== 简易WS广播管理（兼容旧服务）======== #
from threading import Lock
ws_loop = None  # 保存事件循环，便于后台线程调度发送
ws_connections = set()  # 所有兼容WS连接
ws_analysis_subscribers: Dict[str, set] = {}  # analysis_id -> set(WebSocket)
ws_lock = Lock()

def _ws_schedule_send(ws: WebSocket, text: str):
    global ws_loop
    try:
        if ws_loop is None:
            return
        fut = asyncio.run_coroutine_threadsafe(ws.send_text(text), ws_loop)
        _ = fut
    except Exception as e:
        logger.debug(f"WS发送调度失败: {e}")

def _broadcast_analysis_progress(analysis_id: str, payload: Dict[str, Any]):
    try:
        with ws_lock:
            subscribers = list(ws_analysis_subscribers.get(analysis_id, set()))
        if not subscribers:
            return
        import json
        text = json.dumps({
            "type": "analysis_progress",
            "data": payload,
        })
        for ws in subscribers:
            _ws_schedule_send(ws, text)
    except Exception as e:
        logger.debug(f"WS广播失败: {e}")

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
    analysts: Optional[list] = None
    research_depth: Optional[int] = None

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
    except jwt.JWTError:
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
                    "analysts": request.analysts or [],
                    "research_depth": request.research_depth or 2,
                    "username": current_user["username"],
                },
                "created_at": datetime.utcnow(),
                "result_data": None,
                "error_message": None
            }
            
            # 使用统一的MongoDB操作函数
            if hasattr(mongodb_client, '_is_sync') and mongodb_client._is_sync:
                result = mongodb_db.analyses.insert_one(analysis_doc)
            else:
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
        "analysis_type": request.analysis_type,
        "analysts": request.analysts or [],
        "research_depth": request.research_depth or 2,
    }
    
    # 启动真实分析（start_real_analysis 内部会创建后台线程）
    start_real_analysis(
        analysis_id,
        request.symbol.upper(),
        request.market_type,
        request.analysis_type,
        current_user["username"],
        analysts=request.analysts or [],
        research_depth=request.research_depth or 2,
    )
    
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
    # 优先从内存进度读取
    progress_data = analysis_progress_store.get(analysis_id)
    if not progress_data:
        # 兼容：尝试从Redis读取
        if redis_client:
            try:
                import json
                key = f"analysis_progress:{analysis_id}"
                raw = redis_client.get(key)
                if raw:
                    progress_data = json.loads(raw)
            except Exception:
                progress_data = None

    if progress_data:
        return {
            "analysis_id": analysis_id,
            "status": progress_data.get("status", "running"),
            "progress": progress_data.get("progress", 0),
            "message": progress_data.get("message", progress_data.get("current_step_name", "分析中")),
            "user": current_user["username"],
            "created_at": progress_data.get("timestamp"),
            "completed_at": progress_data.get("updated_at") if progress_data.get("status") == "completed" else None,
        }

    # 未找到，返回404
    raise HTTPException(status_code=404, detail="分析未找到")

# 分析结果获取 (需要认证)
@app.get("/api/v1/analysis/{analysis_id}/results")
async def get_analysis_results(analysis_id: str, current_user: dict = Depends(get_current_user)):
    """获取分析结果 (需要登录)

    兼容多来源：
    1) 内存进度存储 analysis_progress_store
    2) Redis 进度缓存（完成时写入）
    3) MongoDB 持久化记录（result_data 字段）
    """

    # 1) 优先从内存读取
    progress_data = analysis_progress_store.get(analysis_id)
    if progress_data:
        if progress_data.get("status") != "completed":
            raise HTTPException(status_code=400, detail="分析尚未完成")

        results = progress_data.get("results") or progress_data.get("result_data") or {}
        if results:
            return {
                "analysis_id": analysis_id,
                "symbol": progress_data.get("symbol"),
                "status": progress_data.get("status"),
                "user": current_user["username"],
                "results": results,
                "created_at": progress_data.get("timestamp"),
                "completed_at": progress_data.get("updated_at") or progress_data.get("timestamp"),
            }
        # 继续尝试其他来源

    # 2) Redis 回退（仅在完成时会写入完整结构）
    if redis_client:
        try:
            import json as _json
            redis_key = f"analysis_progress:{analysis_id}"
            raw = redis_client.get(redis_key)
            if raw:
                data = _json.loads(raw)
                if data.get("status") == "completed":
                    results = data.get("results") or data.get("result_data") or {}
                    if results:
                        return {
                            "analysis_id": analysis_id,
                            "symbol": data.get("symbol"),
                            "status": data.get("status"),
                            "user": current_user["username"],
                            "results": results,
                            "created_at": data.get("timestamp"),
                            "completed_at": data.get("updated_at") or data.get("timestamp"),
                        }
        except Exception as _e:
            logger.debug(f"Redis 回退读取失败: {_e}")

    # 3) MongoDB 回退（读取持久化的 result_data）
    if mongodb_db is not None:
        try:
            from bson import ObjectId
            mongodb_id = None
            try:
                mongodb_id = ObjectId(analysis_id)
            except Exception:
                mongodb_id = None

            if mongodb_id is not None:
                # 根据客户端类型选择同步/异步
                if hasattr(mongodb_client, '_is_sync') and getattr(mongodb_client, '_is_sync'):
                    doc = mongodb_db.analyses.find_one({"_id": mongodb_id})
                else:
                    doc = await mongodb_db.analyses.find_one({"_id": mongodb_id})

                if doc:
                    status = doc.get("status")
                    if status != "completed":
                        raise HTTPException(status_code=400, detail="分析尚未完成")
                    results = doc.get("result_data") or {}
                    if results:
                        return {
                            "analysis_id": analysis_id,
                            "symbol": doc.get("stock_code") or doc.get("symbol"),
                            "status": status,
                            "user": current_user["username"],
                            "results": results,
                            "created_at": doc.get("created_at"),
                            "completed_at": doc.get("completed_at"),
                        }
        except Exception as _e:
            logger.warning(f"⚠️ MongoDB 回退读取失败: {_e}")

    # 未找到任何结果
    if progress_data:
        # 友好降级：如果任务已完成但结果尚未可读，返回占位数据，避免前端报错
        status_val = progress_data.get("status")
        if status_val == "completed":
            return {
                "analysis_id": analysis_id,
                "symbol": progress_data.get("symbol"),
                "status": status_val,
                "user": current_user["username"],
                "results": None,  # 占位，前端将展示“正在加载结果”
                "created_at": progress_data.get("timestamp"),
                "completed_at": progress_data.get("updated_at") or progress_data.get("timestamp"),
                "message": "结果生成中，请稍后刷新"
            }
        # 其他情况保持原有错误
        raise HTTPException(status_code=404, detail="分析结果未找到")
    else:
        raise HTTPException(status_code=404, detail="分析未找到")

# WebSocket统计（兼容前端探测），避免404噪音
@app.get("/api/v1/ws/stats")
async def get_ws_stats():
    try:
        total = len(analysis_progress_store)
        running = sum(1 for v in analysis_progress_store.values() if v.get("status") in ("starting", "running"))
        completed = sum(1 for v in analysis_progress_store.values() if v.get("status") == "completed")
        failed = sum(1 for v in analysis_progress_store.values() if v.get("status") == "failed")
        return {
            "connections": 0,
            "connected_clients": 0,
            "subscriptions": {},
            "analysis_subscribers": {},
            "analysis_counts": {
                "total": total,
                "running": running,
                "completed": completed,
                "failed": failed,
            },
            "message": "compat stub"
        }
    except Exception:
        return {"connections": 0, "connected_clients": 0, "analysis_counts": {"total": 0}}

# 轻量级 WebSocket 端点，避免 403，并兼容前端最基本订阅协议
@app.websocket("/api/v1/ws")
async def websocket_compat_endpoint(websocket: WebSocket, token: str = Query(default=None)):
    global ws_loop
    await websocket.accept()
    try:
        # 缓存事件循环（供后台线程广播时使用）
        try:
            ws_loop = asyncio.get_running_loop()
        except Exception:
            ws_loop = None
        with ws_lock:
            ws_connections.add(websocket)
        # 连接确认
        await websocket.send_text('{"type":"authentication","data":{"status":"connected"}}')
        while True:
            try:
                raw = await websocket.receive_text()
            except WebSocketDisconnect:
                break
            except Exception:
                break
            # 简单协议处理：返回心跳或通知，避免前端报错
            try:
                import json
                msg = json.loads(raw)
                mtype = msg.get("type", "")
                if mtype == "subscribe_notifications":
                    await websocket.send_text('{"type":"notification","data":{"title":"WS已连接","type":"info"}}')
                elif mtype == "subscribe_analysis":
                    analysis_id = (msg.get("data") or {}).get("analysis_id")
                    if analysis_id:
                        with ws_lock:
                            ws_analysis_subscribers.setdefault(analysis_id, set()).add(websocket)
                        await websocket.send_text('{"type":"notification","data":{"title":"已订阅分析","type":"success"}}')
                    else:
                        await websocket.send_text('{"type":"error","data":{"error_code":"MISSING_ANALYSIS_ID","error_message":"analysis_id required"}}')
                elif mtype == "unsubscribe_analysis":
                    analysis_id = (msg.get("data") or {}).get("analysis_id")
                    if analysis_id:
                        with ws_lock:
                            subs = ws_analysis_subscribers.get(analysis_id)
                            if subs and websocket in subs:
                                subs.discard(websocket)
                                if not subs:
                                    ws_analysis_subscribers.pop(analysis_id, None)
                        await websocket.send_text('{"type":"notification","data":{"title":"已取消订阅","type":"info"}}')
                    else:
                        await websocket.send_text('{"type":"error","data":{"error_code":"MISSING_ANALYSIS_ID","error_message":"analysis_id required"}}')
                else:
                    await websocket.send_text('{"type":"heartbeat","data":{}}')
            except Exception:
                await websocket.send_text('{"type":"heartbeat","data":{}}')
    finally:
        try:
            with ws_lock:
                ws_connections.discard(websocket)
                # 从所有订阅中移除
                empty_keys = []
                for aid, subs in ws_analysis_subscribers.items():
                    subs.discard(websocket)
                    if not subs:
                        empty_keys.append(aid)
                for k in empty_keys:
                    ws_analysis_subscribers.pop(k, None)
            await websocket.close()
        except Exception:
            pass

# 获取用户的分析历史 (需要认证) - 优先MongoDB，回退内存
@app.get("/api/v1/analysis/history")
async def get_analysis_history(
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
):
    """获取用户的分析历史 (需要登录)"""

    # 优先MongoDB持久化数据
    if mongodb_db is not None:
        try:
            user_key = current_user.get("sub") or current_user.get("username")
            query = {"$or": [
                {"user_id": user_key},
                {"user_id": str(user_key)},
                {"user_id": current_user.get("username")},
            ]}

            page = max(1, int(page))
            page_size = max(1, min(100, int(page_size)))
            skip = (page - 1) * page_size

            analyses = []
            total = 0

            # 根据客户端类型（同步/异步）选择不同实现
            if hasattr(mongodb_client, '_is_sync') and getattr(mongodb_client, '_is_sync'):
                # 同步 PyMongo
                total = mongodb_db.analyses.count_documents(query)
                cursor = (
                    mongodb_db.analyses
                    .find(query)
                    .sort("created_at", -1)
                    .skip(skip)
                    .limit(page_size)
                )
                for doc in cursor:
                    analyses.append({
                        "id": str(doc.get("_id")),
                        "user_id": doc.get("user_id"),
                        "stock_code": doc.get("stock_code") or doc.get("symbol"),
                        "status": doc.get("status", "unknown"),
                        "progress": doc.get("progress", 0.0),
                        "created_at": doc.get("created_at"),
                        "started_at": doc.get("started_at"),
                        "completed_at": doc.get("completed_at"),
                        "market_type": doc.get("market_type"),
                        "analysis_type": (doc.get("config") or {}).get("analysis_type", "comprehensive"),
                        "result_data": doc.get("result_data"),
                        "error_message": doc.get("error_message"),
                    })
            else:
                # 异步 Motor
                total = await mongodb_db.analyses.count_documents(query)
                cursor = (
                    mongodb_db.analyses
                    .find(query)
                    .sort("created_at", -1)
                    .skip(skip)
                    .limit(page_size)
                )
                async for doc in cursor:
                    analyses.append({
                        "id": str(doc.get("_id")),
                        "user_id": doc.get("user_id"),
                        "stock_code": doc.get("stock_code") or doc.get("symbol"),
                        "status": doc.get("status", "unknown"),
                        "progress": doc.get("progress", 0.0),
                        "created_at": doc.get("created_at"),
                        "started_at": doc.get("started_at"),
                        "completed_at": doc.get("completed_at"),
                        "market_type": doc.get("market_type"),
                        "analysis_type": (doc.get("config") or {}).get("analysis_type", "comprehensive"),
                        "result_data": doc.get("result_data"),
                        "error_message": doc.get("error_message"),
                    })

            return {
                "analyses": analyses,
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        except Exception as e:
            logger.warning(f"⚠️ MongoDB查询分析历史失败，回退内存: {e}")

    # 回退到内存（仅当前进程）
    user_analyses = []
    current_username = current_user["username"]
    current_user_sub = current_user.get("sub", "")

    for analysis_id, data in analysis_progress_store.items():
        analysis_user = data.get("user", "")
        analysis_user_sub = data.get("user_sub", "")
        if (analysis_user == current_username or (current_user_sub and analysis_user_sub == current_user_sub)):
            user_analyses.append({
                "analysis_id": analysis_id,
                "symbol": data.get("symbol", ""),
                "status": data.get("status", "unknown"),
                "progress_percentage": data.get("progress_percentage", 0),
                "created_at": data.get("timestamp", ""),
                "last_update": data.get("last_update", 0),
                "current_step_name": data.get("current_step_name", ""),
                "elapsed_time": data.get("elapsed_time", 0),
                "market_type": data.get("market_type", ""),
                "analysis_type": data.get("analysis_type", ""),
            })

    user_analyses.sort(key=lambda x: x.get("last_update", 0), reverse=True)
    start = (page - 1) * page_size
    end = start + page_size
    paged = user_analyses[start:end]

    return {
        "analyses": paged,
        "total": len(user_analyses),
        "page": page,
        "page_size": page_size,
    }

# Authing SSO 回调处理
@app.get("/api/v1/auth/authing/callback")
async def authing_callback(code: str, state: str = None):
    """处理 Authing SSO 回调"""
    # 统一重定向到前端回调页，由前端调用 exchange 接口完成令牌交换
    try:
        frontend_callback = f"http://localhost:3000/auth/callback?code={code}"
        if state is not None:
            frontend_callback += f"&state={state}"
        return RedirectResponse(url=frontend_callback, status_code=302)
    except Exception:
        # 兜底：回退到登录页
        return RedirectResponse(url="http://localhost:3000/login", status_code=302)
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

# Authing SSO code 兑换接口（返回JSON，供前端调用）
@app.post("/api/v1/auth/authing/exchange")
async def authing_exchange(payload: dict):
    """将Authing返回的code兑换为本系统access_token并返回JSON"""
    try:
        import requests
        code = payload.get("code")
        state = payload.get("state")  # 可按需校验
        redirect_uri = payload.get("redirect_uri") or os.getenv("AUTHING_REDIRECT_URI")

        if not code:
            raise HTTPException(status_code=400, detail="缺少code参数")

        # 读取 Authing 配置
        authing_app_id = os.getenv("AUTHING_APP_ID")
        authing_app_secret = os.getenv("AUTHING_APP_SECRET")
        authing_app_host = os.getenv("AUTHING_APP_HOST")

        if not all([authing_app_id, authing_app_secret, authing_app_host, redirect_uri]):
            raise HTTPException(status_code=500, detail="Authing 配置不完整")

        # 第一步：用 code 换取 access_token
        token_url = f"{authing_app_host}/oidc/token"
        token_data = {
            "client_id": authing_app_id,
            "client_secret": authing_app_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
        token_response = requests.post(token_url, data=token_data)
        if not token_response.ok:
            raise HTTPException(status_code=400, detail=f"获取token失败: {token_response.text}")
        token_info = token_response.json()
        provider_access_token = token_info.get("access_token")
        if not provider_access_token:
            raise HTTPException(status_code=400, detail="未获取到access_token")

        # 第二步：用 access_token 获取用户信息
        userinfo_url = f"{authing_app_host}/oidc/me"
        headers = {"Authorization": f"Bearer {provider_access_token}"}
        userinfo_response = requests.get(userinfo_url, headers=headers)
        if not userinfo_response.ok:
            raise HTTPException(status_code=400, detail=f"获取用户信息失败: {userinfo_response.text}")
        user_info = userinfo_response.json()

        # 标准化用户信息
        sub = user_info.get("sub")
        if not sub:
            raise HTTPException(status_code=400, detail="用户信息缺少sub")
        username = (
            user_info.get("preferred_username")
            or user_info.get("username")
            or user_info.get("phone_number")
            or sub
        )
        email = user_info.get("email")
        if not email:
            phone = user_info.get("phone_number")
            email = f"{phone}@authing.demo" if phone else f"{username}@authing.demo"
        display_name = user_info.get("name") or user_info.get("nickname") or username

        user_data = {
            "username": username,
            "email": email,
            "name": display_name,
            "phone": user_info.get("phone_number", ""),
            "sub": sub,
            "avatar": user_info.get("picture", ""),
            "roles": user_info.get("roles", []),
            "extended_fields": {
                "unionid": user_info.get("unionid"),
                "external_id": user_info.get("external_id"),
            },
            "role": "user",
            "permissions": ["read"],
            "is_active": True,
            "auth_type": "sso",
            "auth_provider": "authing",
        }

        # 写入/更新模拟用户数据库
        fake_users_db[user_data["username"]] = {**user_data, "password_hash": "sso_user"}

        # 颁发本系统访问令牌
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_data["username"]}, expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "username": user_data["username"],
                "email": user_data["email"],
                "role": user_data["role"],
                "permissions": user_data["permissions"],
            },
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Authing exchange 失败: {e}")
        raise HTTPException(status_code=500, detail="SSO 登录处理失败")

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
    # 1) 内存进度（优先）
    progress_data = analysis_progress_store.get(analysis_id)
    if progress_data:
        # 若已终态，直接返回
        if progress_data.get("status") in ["completed", "failed", "cancelled"]:
            return {"message": f"分析已处于{progress_data.get('status')}状态"}
        # 标记取消
        progress_data.update({
            "status": "cancelled",
            "message": "分析已被用户取消",
            "end_time": time.time(),
            "updated_at": datetime.now().isoformat(),
        })
        analysis_progress_store[analysis_id] = progress_data

    # 2) Redis（用于跨进程/页面读取）
    if redis_client:
        try:
            import json
            redis_key = f"analysis_progress:{analysis_id}"
            existing = redis_client.get(redis_key)
            if existing:
                try:
                    data = json.loads(existing)
                except Exception:
                    data = {}
            else:
                data = {}
            data.update({
                "status": "cancelled",
                "message": "分析已被用户取消",
                "updated_at": datetime.now().isoformat(),
            })
            redis_client.setex(redis_key, 3600, json.dumps(data))
        except Exception:
            pass

    # 3) MongoDB（持久化状态）
    if mongodb_db is not None:
        try:
            from bson import ObjectId
            mongodb_id = None
            try:
                mongodb_id = ObjectId(analysis_id)
            except Exception:
                mongodb_id = None
            if mongodb_id is not None:
                await mongodb_db.analyses.update_one(
                    {"_id": mongodb_id},
                    {"$set": {"status": "cancelled", "completed_at": datetime.utcnow()}}
                )
        except Exception:
            pass

    # 4) 返回幂等成功（即使内存中不存在该任务，也视为取消请求已受理）
    return {"message": "已处理取消请求", "analysis_id": analysis_id, "status": "ok"}

# 获取单个分析（简化版，避免前端偶发GET请求404）
@app.get("/api/v1/analysis/{analysis_id}")
async def get_analysis_brief(analysis_id: str, current_user: dict = Depends(get_current_user)):
    # 先从内存
    data = analysis_progress_store.get(analysis_id)
    if data:
        return {
            "id": analysis_id,
            "symbol": data.get("symbol"),
            "status": data.get("status"),
            "progress": data.get("progress", 0),
            "created_at": data.get("timestamp"),
            "completed_at": data.get("updated_at") if data.get("status") == "completed" else None,
        }
    # 再尝试MongoDB
    if mongodb_db is not None:
        try:
            from bson import ObjectId
            doc = await mongodb_db.analyses.find_one({"_id": ObjectId(analysis_id)})
            if doc:
                return {
                    "id": str(doc.get("_id")),
                    "symbol": doc.get("stock_code") or doc.get("symbol"),
                    "status": doc.get("status"),
                    "progress": doc.get("progress", 0.0),
                    "created_at": doc.get("created_at"),
                    "completed_at": doc.get("completed_at"),
                }
        except Exception:
            pass
    raise HTTPException(status_code=404, detail="Analysis not found")

# 删除分析记录
@app.delete("/api/v1/analysis/{analysis_id}")
async def delete_analysis_record(analysis_id: str, current_user: dict = Depends(get_current_user)):
    deleted = False
    # 先删内存
    if analysis_id in analysis_progress_store:
        analysis_progress_store.pop(analysis_id, None)
        deleted = True
    # 删Redis缓存
    if redis_client:
        try:
            redis_client.delete(f"analysis_progress:{analysis_id}")
            redis_client.delete(f"analysis_result:{analysis_id}")
        except Exception:
            pass
    # 删MongoDB
    if mongodb_db is not None:
        try:
            from bson import ObjectId
            result = await mongodb_db.analyses.delete_one({"_id": ObjectId(analysis_id)})
            if result.deleted_count > 0:
                deleted = True
        except Exception:
            # 可能不是合法ObjectId，忽略
            pass
    if not deleted:
        # 为提升前端体验，返回幂等删除成功（即使不存在也视为已删除）
        return {"message": "Analysis not found or already deleted", "analysis_id": analysis_id, "status": "ok"}
    return {"message": "Analysis deleted", "analysis_id": analysis_id, "status": "ok"}

"""下载与导出相关的工具方法"""


def _safe_filename(name: str) -> bool:
    return not (".." in name or "/" in name or "\\" in name)


def _utf16be_hex(s: str) -> str:
    """Encode text as UTF-16BE hex string for PDF (with BOM)."""
    try:
        data = s.encode("utf-16-be", errors="replace")
    except Exception:
        data = str(s).encode("utf-16-be", errors="replace")
    return "<" + (b"\xfe\xff" + data).hex().upper() + ">"


def _generate_minimal_pdf(title_text: str, meta_text: str, body: str) -> bytes:
    import io as _io
    buf = _io.BytesIO()
    w = buf.write
    w(b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n")
    # 1 Catalog
    pos1 = buf.tell(); w(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    # 2 Pages
    pos2 = buf.tell(); w(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    # 4 Font (CJK-capable Type0 font using UniGB-UCS2-H)
    pos4 = buf.tell(); w(
        b"4 0 obj\n"+
        b"<< /Type /Font /Subtype /Type0 /BaseFont /STSong-Light /Name /F1 "
        b"/Encoding /UniGB-UCS2-H /DescendantFonts [5 0 R] >>\nendobj\n"
    )
    # 5 Descendant CIDFont (minimal)
    pos5 = buf.tell(); w(
        b"5 0 obj\n"+
        b"<< /Type /Font /Subtype /CIDFontType0 /BaseFont /STSong-Light "
        b"/CIDSystemInfo << /Registry (Adobe) /Ordering (GB1) /Supplement 4 >> "
        b"/FontDescriptor 6 0 R /DW 1000 >>\nendobj\n"
    )
    # 6 FontDescriptor (minimal metrics)
    pos6 = buf.tell(); w(
        b"6 0 obj\n"+
        b"<< /Type /FontDescriptor /FontName /STSong-Light /Flags 4 "
        b"/FontBBox [-250 -250 1000 1000] /ItalicAngle 0 /Ascent 1000 /Descent -250 /CapHeight 800 /StemV 80 >>\nendobj\n"
    )
    # 7 Contents
    lines = [
        "BT",
        "/F1 18 Tf",
        "72 740 Td",
        f"{_utf16be_hex(title_text)} Tj",
        "/F1 11 Tf",
        "0 -24 Td",
    ]
    if meta_text:
        for meta_line in meta_text.split("\n"):
            lines.append(f"{_utf16be_hex(meta_line)} Tj")
            lines.append("0 -14 Td")
    if body:
        for body_line in body.split("\n"):
            safe = body_line[:1000]
            lines.append(f"{_utf16be_hex(safe)} Tj")
            lines.append("0 -14 Td")
    lines.append("ET")
    content_stream = "\n".join(lines).encode("ascii")
    pos7 = buf.tell()
    w(f"7 0 obj\n<< /Length {len(content_stream)} >>\nstream\n".encode("ascii"))
    w(content_stream)
    w(b"\nendstream\nendobj\n")
    # 3 Page
    pos3 = buf.tell(); w(b"3 0 obj\n" +
                         b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 7 0 R " +
                         b"/Resources << /Font << /F1 4 0 R >> >> >>\nendobj\n")
    # xref
    xref_pos = buf.tell()
    xref_entries = [0, pos1, pos2, pos3, pos4, pos5, pos6, pos7]
    w(b"xref\n0 8\n")
    w(b"0000000000 65535 f \n")
    for p in xref_entries[1:]:
        w(f"{p:010d} 00000 n \n".encode("ascii"))
    # trailer
    w(b"trailer\n")
    w(b"<< /Size 8 /Root 1 0 R >>\n")
    w(b"startxref\n")
    w(f"{xref_pos}\n".encode("ascii"))
    w(b"%%EOF\n")
    return buf.getvalue()


# PDF报告下载接口（增强：自动查找文件，找不到则在线生成）
@app.get("/api/v1/analysis/{analysis_id}/download/pdf")
async def download_analysis_pdf(analysis_id: str, current_user: dict = Depends(get_current_user)):
    from fastapi.responses import FileResponse, StreamingResponse
    from pathlib import Path
    import io

    # 读取进度
    progress_data = analysis_progress_store.get(analysis_id)
    if not progress_data and mongodb_db is not None:
        # 尝试从MongoDB确认是否存在记录
        try:
            from bson import ObjectId
            oid = None
            try:
                oid = ObjectId(analysis_id)
            except Exception:
                oid = None
            if oid is not None:
                if hasattr(mongodb_client, '_is_sync') and getattr(mongodb_client, '_is_sync'):
                    doc = mongodb_db.analyses.find_one({"_id": oid})
                else:
                    doc = await mongodb_db.analyses.find_one({"_id": oid})
                if doc:
                    # 构造一个最小进度数据用于后续逻辑
                    progress_data = {
                        "status": doc.get("status"),
                        "symbol": doc.get("stock_code") or doc.get("symbol"),
                        "timestamp": doc.get("created_at"),
                        "updated_at": doc.get("completed_at"),
                        "result_data": doc.get("result_data") or {},
                    }
        except Exception:
            pass

    if not progress_data:
        raise HTTPException(status_code=404, detail="分析未找到")

    if progress_data.get("status") != "completed":
        raise HTTPException(status_code=400, detail="分析尚未完成")

    symbol = (progress_data.get("symbol") or "UNKNOWN").upper()

    # 1) 优先尝试在磁盘上查找PDF（不再依赖固定日期路径）
    try:
        candidates = [Path("/app/data") / symbol, Path("results") / symbol]
        found_pdf = None
        for base in candidates:
            if base.exists():
                # 查找 reports 目录下或任意子目录的PDF
                pdf_list = list(base.rglob("reports/*.pdf")) or list(base.rglob("*.pdf"))
                if pdf_list:
                    # 选择最新修改时间的文件
                    pdf_list.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                    found_pdf = pdf_list[0]
                    break
        if found_pdf and found_pdf.exists():
            return FileResponse(
                path=str(found_pdf),
                filename=f"{symbol}_analysis_report.pdf",
                media_type="application/pdf"
            )
    except Exception:
        # 忽略磁盘搜索异常，转为在线生成
        pass

    # 2) 在线生成简要PDF（从结果数据提取摘要）
    # 尝试从多处获取结果
    results = progress_data.get("results") or progress_data.get("result_data") or {}
    if not results and mongodb_db is not None:
        try:
            from bson import ObjectId
            oid = None
            try:
                oid = ObjectId(analysis_id)
            except Exception:
                oid = None
            if oid is not None:
                if hasattr(mongodb_client, '_is_sync') and getattr(mongodb_client, '_is_sync'):
                    doc = mongodb_db.analyses.find_one({"_id": oid})
                else:
                    doc = await mongodb_db.analyses.find_one({"_id": oid})
                if doc:
                    results = doc.get("result_data") or {}
        except Exception:
            pass

    # 做一个简要摘要
    title = f"{symbol} 分析报告"
    created = progress_data.get("timestamp") or ""
    completed = progress_data.get("updated_at") or ""
    meta_lines = []
    if created:
        meta_lines.append(f"创建时间: {created}")
    if completed:
        meta_lines.append(f"完成时间: {completed}")
    meta_text = "\n".join(meta_lines)

    summary_lines = []
    try:
        # 优先从 state 中提取详细字段
        state = {}
        if isinstance(results, dict):
            state = results.get("state") or {}
        # 兼容顶层直接包含字段的情况
        def pick(k: str):
            v = None
            if isinstance(state, dict) and k in state:
                v = state.get(k)
            elif isinstance(results, dict) and k in results:
                v = results.get(k)
            return v

        ordered_keys = [
            "final_trade_decision",
            "trader_investment_plan",
            "investment_plan",
            "fundamentals_report",
            "market_report",
            "sentiment_report",
            "risk_assessment",
        ]

        for key in ordered_keys:
            val = pick(key)
            if not val:
                continue
            if isinstance(val, str):
                txt = val.strip()
                if txt:
                    summary_lines.append(f"【{key}】 {txt[:800]}")
            elif isinstance(val, dict):
                inner = [f"{k}: {str(v)[:200]}" for k, v in list(val.items())[:5]]
                if inner:
                    summary_lines.append(f"【{key}】 " + "; ".join(inner))

        # 决策信息
        decision = None
        if isinstance(results, dict):
            decision = results.get("decision")
        if isinstance(decision, dict):
            action = decision.get("action")
            reason = decision.get("reasoning")
            tp = decision.get("target_price")
            parts = []
            if action: parts.append(f"操作: {action}")
            if tp not in (None, "N/A", "None", ""): parts.append(f"目标价: {tp}")
            if reason: parts.append(f"理由: {str(reason)[:400]}")
            if parts:
                summary_lines.insert(0, "【决策】 " + "; ".join(parts))
    except Exception:
        pass

    if not summary_lines:
        # 如果没有任何内容可用，返回404与原始语义一致
        # 但更友好地提示
        pdf_bytes = _generate_minimal_pdf(title, meta_text, "暂无可导出的报告摘要")
    else:
        body_text = "\n".join(summary_lines)
        pdf_bytes = _generate_minimal_pdf(title, meta_text, body_text)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={symbol}_analysis_report.pdf"
        }
    )

@app.get("/api/v1/analysis/{analysis_id}/files")
async def get_analysis_files(analysis_id: str, current_user: dict = Depends(get_current_user)):
    """获取分析报告文件列表（增强：自动遍历查找）"""
    from pathlib import Path

    progress_data = analysis_progress_store.get(analysis_id)
    if not progress_data:
        raise HTTPException(status_code=404, detail="分析未找到")

    if progress_data.get("status") != "completed":
        raise HTTPException(status_code=400, detail="分析尚未完成")

    symbol = (progress_data.get("symbol") or "UNKNOWN").upper()
    candidates = [Path("/app/data") / symbol, Path("results") / symbol]
    files = []
    try:
        for base in candidates:
            if base.exists():
                for p in list(base.rglob("reports/*")) or list(base.rglob("*")):
                    if p.is_file():
                        files.append({
                            "name": p.name,
                            "type": p.suffix.lower(),
                            "size": p.stat().st_size,
                            "url": f"/api/v1/analysis/{analysis_id}/download/{p.name}"
                        })
                break
    except Exception:
        files = []

    return {"files": files}

@app.get("/api/v1/analysis/{analysis_id}/download/{filename}")
async def download_analysis_file(analysis_id: str, filename: str, current_user: dict = Depends(get_current_user)):
    """下载指定的分析报告文件（增强：自动遍历查找）"""
    from fastapi.responses import FileResponse
    from pathlib import Path

    progress_data = analysis_progress_store.get(analysis_id)
    if not progress_data:
        raise HTTPException(status_code=404, detail="分析未找到")

    # 安全检查
    if not _safe_filename(filename):
        raise HTTPException(status_code=400, detail="无效的文件名")

    symbol = (progress_data.get("symbol") or "UNKNOWN").upper()
    candidates = [Path("/app/data") / symbol, Path("results") / symbol]

    found = None
    try:
        for base in candidates:
            if base.exists():
                for p in base.rglob(filename):
                    if p.is_file():
                        found = p
                        break
            if found:
                break
    except Exception:
        found = None

    if not found or not found.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    # 媒体类型
    media_type = "application/octet-stream"
    if filename.endswith(".pdf"):
        media_type = "application/pdf"
    elif filename.endswith(".md"):
        media_type = "text/markdown"
    elif filename.endswith(".txt"):
        media_type = "text/plain"
    elif filename.endswith(".json"):
        media_type = "application/json"

    return FileResponse(path=str(found), filename=filename, media_type=media_type)

# 启动真实分析 - 重构版本，消除重复执行
def start_real_analysis(
    analysis_id: str,
    symbol: str,
    market_type: str,
    analysis_type: str,
    username: str,
    analysts: Optional[list] = None,
    research_depth: Optional[int] = None,
):
    """启动真实的股票分析 - 修复重复执行问题"""
    import threading
    import time
    from datetime import datetime
    
    def analysis_worker():
        try:
            # 简化的路径设置
            import sys
            import os
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent
            
            if not (project_root / 'tradingagents').exists():
                project_root = Path(os.getcwd()).parent if 'backend' in os.getcwd() else Path(os.getcwd())
                if not (project_root / 'tradingagents').exists():
                    # Try to find tradingagents directory in common locations
                    possible_paths = [
                        Path('/app'),  # Docker container
                        Path.cwd().parent,  # Parent directory
                        Path.cwd(),  # Current directory
                        Path.home() / 'TradingAgents-CN',  # User home
                    ]
                    for path in possible_paths:
                        if (path / 'tradingagents').exists():
                            project_root = path
                            break
                    else:
                        # If still not found, use current directory as fallback
                        project_root = Path(os.getcwd())
            
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            
            # 进度回调在后续统一定义（支持7步权重），此处删除重复定义
            
            # 统一采用run_stock_analysis路径，移除直接执行以避免重复
            # 尝试导入并使用真正的TradingAgents分析引擎
            try:
                # 导入TradingAgents核心组件
                from tradingagents.graph.trading_graph import TradingAgentsGraph
                from tradingagents.default_config import DEFAULT_CONFIG
                
                # 尝试导入result_formatter
                try:
                    from services.result_formatter import format_analysis_results
                except ImportError:
                    # 如果导入失败，创建简单的格式化函数
                    def format_analysis_results(results):
                        return results
                
                def run_stock_analysis(stock_symbol, analysis_date, analysts, research_depth, llm_provider, llm_model, market_type="美股", progress_callback=None):
                    """真正的TradingAgents股票分析函数"""
                    
                    # 创建TradingAgents图实例
                    config = DEFAULT_CONFIG.copy()
                    config['llm_provider'] = llm_provider
                    config['deep_think_llm'] = llm_model
                    config['quick_think_llm'] = llm_model
                    # 强制启用在线工具/新闻，避免本地YFin数据文件缺失导致的数据错误
                    config['online_tools'] = True
                    config['online_news'] = True
                    
                    # 将analysts转换为正确的格式
                    if isinstance(analysts, list):
                        selected_analysts = analysts
                    else:
                        # 默认分析师列表
                        selected_analysts = ["market", "fundamentals", "news", "social"]
                    
                    trading_graph = TradingAgentsGraph(selected_analysts=selected_analysts, config=config)
                    
                    if progress_callback:
                        progress_callback("🔍 初始化TradingAgents分析引擎", 0, 7)
                    
                    try:
                        # 执行真正的股票分析
                        final_state, decision = trading_graph.propagate(
                            company_name=stock_symbol,
                            trade_date=analysis_date,
                            progress_callback=progress_callback
                        )
                        
                        if progress_callback:
                            progress_callback("✅ 分析完成，正在整理结果", 6, 7)
                        
                        # 格式化分析结果
                        analysis_result = {
                            'success': True,
                            'stock_symbol': stock_symbol,
                            'analysis_date': analysis_date,
                            'analysts': analysts,
                            'research_depth': research_depth,
                            'llm_provider': llm_provider,
                            'llm_model': llm_model,
                            'state': final_state,
                            'decision': decision
                        }
                        
                        return format_analysis_results(analysis_result)
                        
                    except Exception as e:
                        logger.error(f"TradingAgents分析执行失败: {e}")
                        # 如果真实分析失败，返回错误结果
                        return {
                            'success': False,
                            'error': f'分析执行失败: {str(e)}',
                            'stock_symbol': stock_symbol
                        }
                
                USE_BACKEND_SERVICE = True
                logger.info("✅ 使用真实TradingAgents分析引擎")
                
            except ImportError as e:
                logger.error(f"❌ 无法导入TradingAgents: {e}")
                result = {
                    "success": False,
                    "error": f"TradingAgents分析引擎导入失败: {str(e)}",
                    "stock_symbol": symbol
                }
                
                USE_BACKEND_SERVICE = False
            
            # 进度回调函数 - 支持7步真实进度系统
            def progress_callback(message, step=None, total_steps=None, llm_result=None, analyst_type=None, *extra_args, **extra_kwargs):
                # 检查是否已被取消
                if analysis_progress_store[analysis_id].get("status") == "cancelled":
                    logger.info(f"Analysis {analysis_id} was cancelled, stopping execution")
                    raise Exception("Analysis was cancelled by user")
                
                # 🔧 添加调试日志
                logger.info(f"🔧 [PROGRESS DEBUG] 收到进度回调: message='{message}', step={step}, total_steps={total_steps}")
                    
                current_time = time.time()
                start_time = analysis_progress_store[analysis_id].get("start_time", current_time)
                elapsed_time = current_time - start_time
                
                # 7步系统的步骤名称和权重
                step_names = [
                    "股票识别",    # 10%
                    "市场分析",    # 15% 
                    "基本面分析",  # 15%
                    "新闻分析",    # 10%
                    "情绪分析",    # 10%
                    "投资辩论",    # 25%
                    "风险评估"     # 15%
                ]
                step_weights = [0.10, 0.15, 0.15, 0.10, 0.10, 0.25, 0.15]
                
                # 计算进度百分比
                if step is not None and step < len(step_names):
                    # 使用7步系统计算精确进度
                    completed_weight = sum(step_weights[:step])  # 已完成步骤的权重
                    current_weight = step_weights[step]          # 当前步骤的权重
                    progress_percentage = completed_weight + current_weight  # 当前步骤算作已完成
                    current_step_num = step + 1  # 显示用的步骤号（从1开始）
                    total_step_num = len(step_names)
                    current_step_name = step_names[step]
                else:
                    # 智能检测步骤（基于消息内容）
                    current_progress = analysis_progress_store[analysis_id].get("progress_percentage", 0)
                    
                    # 7步系统的智能消息匹配逻辑
                    detected_step = None
                    
                    # 步骤0: 股票识别 (10%) - 更精确的匹配，避免与其他步骤冲突
                    if any(keyword in message for keyword in ["股票识别", "识别股票类型", "获取基本信息"]) and not any(analyst in message for analyst in ["分析师", "Analyst"]):
                        detected_step = 0
                    elif "开始分析" in message and not any(analyst in message for analyst in ["市场分析师", "基本面分析师", "新闻分析师", "社交媒体分析师"]):
                        detected_step = 0
                    
                    # 步骤1: 市场分析 (15%)
                    elif any(keyword in message for keyword in ["市场分析师开始", "市场分析师完成", "✅ 市场分析师完成", "📈 市场分析师完成", "Market Analyst", "技术指标分析", "价格走势研究"]):
                        detected_step = 1
                    
                    # 步骤2: 基本面分析 (15%)
                    elif any(keyword in message for keyword in ["基本面分析师开始", "基本面分析师完成", "✅ 基本面分析师完成", "Fundamentals Analyst", "财务数据分析", "估值评估"]):
                        detected_step = 2
                    
                    # 步骤3: 新闻分析 (10%)
                    elif any(keyword in message for keyword in ["新闻分析师开始", "新闻分析师完成", "✅ 新闻分析师完成", "News Analyst", "新闻事件影响", "行业动态分析"]):
                        detected_step = 3
                    
                    # 步骤4: 情绪分析 (10%)
                    elif any(keyword in message for keyword in ["社交媒体分析师开始", "社交媒体分析师完成", "✅ 社交媒体分析师完成", "Social Media Analyst", "情绪分析", "市场热度分析"]):
                        detected_step = 4
                    
                    # 步骤5: 投资辩论 (25%)
                    elif any(keyword in message for keyword in ["Bull Researcher", "Bear Researcher", "Research Manager", "投资辩论", "多空"]):
                        detected_step = 5
                    
                    # 步骤6: 风险评估 (15%)
                    elif any(keyword in message for keyword in ["Risk Judge", "Risky Analyst", "Safe Analyst", "风险评估", "风险管理"]):
                        detected_step = 6
                    
                    # 分析完成
                    elif any(keyword in message for keyword in ["分析成功完成", "✅ 分析", "所有分析师完成", "分析完成，正在整理结果"]):
                        detected_step = 6
                        progress_percentage = 1.0
                    
                    # 根据检测到的步骤计算进度
                    if detected_step is not None:
                        completed_weight = sum(step_weights[:detected_step])
                        current_weight = step_weights[detected_step]
                        progress_percentage = completed_weight + current_weight
                        current_step_num = detected_step + 1
                        current_step_name = step_names[detected_step]
                        total_step_num = len(step_names)
                    else:
                        # 如果没有匹配到特定步骤，保持当前进度或缓慢递增
                        progress_percentage = max(current_progress, 0.05)  # 至少5%
                        current_step_num = analysis_progress_store[analysis_id].get("current_step", 1)
                        current_step_name = analysis_progress_store[analysis_id].get("current_step_name", "分析中")
                        total_step_num = 7
                
                # 在非最终完成消息时，避免将进度设置为100%
                is_final_message = any(k in message for k in ["分析完成", "正在整理结果", "最终决策", "完成！"])  # 仅这些消息允许100%
                if progress_percentage >= 1.0 and not is_final_message:
                    progress_percentage = 0.95

                # 确保所有变量都有默认值
                if 'current_step_name' not in locals():
                    current_step_name = analysis_progress_store[analysis_id].get("current_step_name", "分析中")
                if 'total_step_num' not in locals():
                    total_step_num = 7


                # 心跳消息：仅更新时间与提示，不改变百分比（保证前端看到“在进行”但不编造进度）
                if isinstance(message, str) and "HEARTBEAT" in message:
                    progress_percentage = analysis_progress_store[analysis_id].get("progress_percentage", 0)
                    # 保持当前步骤不变
                    current_step_num = analysis_progress_store[analysis_id].get("current_step", 1)
                    current_step_name = analysis_progress_store[analysis_id].get("current_step_name", "分析中")
                    total_step_num = 7
                
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
                
                # 更新进度数据 - 使用真实的7步名称
                steps_list = []
                for idx in range(total_step_num):
                    step_num = idx + 1
                    if progress_percentage >= 1.0 or step_num < current_step_num:
                        step_status = "completed"
                    elif step_num == current_step_num and progress_percentage < 1.0:
                        step_status = "running"
                    else:
                        step_status = "pending"
                    
                    steps_list.append({
                        "index": step_num,
                        "name": step_names[idx],
                        "status": step_status,
                        "weight": step_weights[idx]
                    })

                # 处理消息显示 - 避免显示HEARTBEAT
                display_message = message
                if "HEARTBEAT" in message:
                    # 心跳消息使用更友好的显示
                    display_message = f"正在执行 {current_step_name}..."
                
                progress_data = {
                    # 只有在最终完成消息时才标记为completed，其他情况保持running
                    "status": "completed" if (progress_percentage >= 1.0 and is_final_message) else "running",
                    "current_step": current_step_num - 1,  # 转换为0-based索引供前端使用
                    "total_steps": total_step_num,
                    "progress_percentage": progress_percentage,  # 保持0-1之间的小数
                    "progress": progress_percentage * 100,  # 同时提供0-100格式供兼容
                    "current_step_name": current_step_name,
                    "message": display_message,
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

                # 通过WS向订阅者广播进度
                try:
                    payload = {
                        "analysisId": analysis_id,
                        "progress": float(progress_percent_display),
                        "status": progress_data.get("status", "running"),
                        "message": progress_data.get("message", ""),
                        "currentStep": progress_data.get("current_step_name", ""),
                        "timestamp": progress_data.get("timestamp"),
                    }
                    _broadcast_analysis_progress(analysis_id, payload)
                except Exception as _e:
                    logger.debug(f"WS进度广播失败: {_e}")
                
                # 记录LLM阶段结果，供前端调试查看
                if llm_result:
                    llm_results = analysis_progress_store[analysis_id].setdefault("llm_results", {})
                    analyst_key = analyst_type or (f"step_{current_step_num}" if current_step_num else "unknown")
                    llm_results[analyst_key] = {
                        "result": llm_result,
                        "timestamp": datetime.now().isoformat()
                    }
            
            # 设置分析参数 - 使用与TradingAgentsGraph相同的分析师配置
            analysis_date = datetime.now().strftime("%Y-%m-%d")
            # 使用前端传入的分析师列表，默认仅包含已选择的；若为空则退回到基础三人组
            analysts_list = analysts if analysts else ["market", "fundamentals"]
            depth = int(research_depth) if research_depth else 2
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
                analysts=analysts_list,
                research_depth=depth,
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
            
            # WS广播最终完成
            try:
                payload = {
                    "analysisId": analysis_id,
                    "progress": 100.0,
                    "status": final_status,
                    "message": final_message,
                    "currentStep": final_message,
                    "timestamp": final_progress_data.get("timestamp"),
                }
                _broadcast_analysis_progress(analysis_id, payload)
            except Exception as _e:
                logger.debug(f"WS完成广播失败: {_e}")
            
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
                    
                    # 使用统一的MongoDB操作函数
                    safe_mongodb_operation(
                        mongodb_db.analyses.update_one,
                        {"_id": ObjectId(analysis_id)},
                        {"$set": update_data}
                    )
                    
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
                    
                    # 使用统一的MongoDB操作函数
                    safe_mongodb_operation(
                        mongodb_db.analyses.update_one,
                        {"_id": ObjectId(analysis_id)},
                        {"$set": {
                            "status": "failed",
                            "error_message": str(e),
                            "completed_at": datetime.utcnow()
                        }}
                    )
                    
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
        log_level=os.getenv("TRADINGAGENTS_LOG_LEVEL", "info").lower()
    )
