#!/usr/bin/env python3
"""
简化的 FastAPI 测试服务器
用于测试框架迁移后的基础功能
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import jwt
from datetime import datetime, timedelta
import hashlib

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv(project_root / ".env", override=True)

app = FastAPI(
    title="TradingAgents-CN API",
    description="框架迁移测试版本 - FastAPI + React 架构",
    version="0.1.0-migration",
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
        "message": "TradingAgents-CN 框架迁移测试版",
        "version": "0.1.0-migration",
        "architecture": "FastAPI + React",
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
    return User(
        username=current_user["username"],
        email=current_user["email"],
        role=current_user["role"],
        permissions=current_user["permissions"],
        is_active=current_user["is_active"]
    )

# 健康检查
@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        message="TradingAgents-CN API is running",
        version="0.1.0-migration",
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
    
    # 模拟分析ID生成
    import uuid
    analysis_id = str(uuid.uuid4())
    
    # 这里应该调用实际的分析逻辑
    # 目前返回模拟响应
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
    
    # 模拟分析结果
    return {
        "analysis_id": analysis_id,
        "symbol": "AAPL",
        "market_type": "US",
        "analysis_type": "comprehensive",
        "user": current_user["username"],
        "results": {
            "decision": "BUY",
            "confidence": 0.85,
            "target_price": 180.0,
            "current_price": 150.0,
            "reasoning": "基于技术分析和基本面分析，该股票具有良好的投资价值。",
            "risk_level": "Medium",
            "time_horizon": "3-6 months"
        },
        "agents_analysis": {
            "technical_analyst": {
                "decision": "BUY",
                "confidence": 0.8,
                "reasoning": "技术指标显示上升趋势"
            },
            "fundamental_analyst": {
                "decision": "BUY", 
                "confidence": 0.9,
                "reasoning": "财务数据表现优异"
            },
            "risk_manager": {
                "decision": "HOLD",
                "confidence": 0.7,
                "reasoning": "当前市场波动性较高"
            }
        },
        "created_at": "2024-01-01T00:00:00Z",
        "completed_at": "2024-01-01T00:05:00Z"
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
        
        # 这里应该调用 Authing API 来交换 code 获取用户信息
        # 目前返回模拟响应，实际使用时需要调用 Authing 的 token 接口
        
        # 模拟从 Authing 获取的用户信息
        mock_user_info = {
            "sub": f"authing_user_{code[:8]}",
            "username": f"authing_user_{code[:8]}",
            "email": f"user_{code[:8]}@authing.cn",
            "name": "Authing SSO 用户"
        }
        
        # 创建或更新本地用户
        user_data = {
            "username": mock_user_info["username"],
            "email": mock_user_info["email"],
            "role": "user",
            "permissions": ["read"],
            "is_active": True
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
    print("🚀 启动 TradingAgents-CN 框架迁移测试服务器")
    print("📊 架构: FastAPI + React")
    print("🌐 API文档: http://localhost:8000/api/v1/docs")
    print("🔧 健康检查: http://localhost:8000/api/v1/health")
    print("⚙️ 配置检查: http://localhost:8000/api/v1/config/check")
    
    uvicorn.run(
        "test_backend:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )