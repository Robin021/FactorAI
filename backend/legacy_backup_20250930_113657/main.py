"""
FastAPI 主应用 - 简单进度跟踪系统
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api.analysis import router as analysis_router

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="股票分析API",
    description="基于轮询的简单进度跟踪系统",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(analysis_router, prefix="/api")

# 注册兼容性路由
from app.api.compatibility import router as compatibility_router
app.include_router(compatibility_router, prefix="/api")

# 注册认证路由
from app.api.auth import router as auth_router
app.include_router(auth_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "股票分析API服务正在运行"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "服务正常"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)