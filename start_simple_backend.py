#!/usr/bin/env python3
"""
启动简单的后端服务用于测试详细进度显示
"""

import uvicorn
import sys
import os

# 添加backend目录到Python路径
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

if __name__ == "__main__":
    print("🚀 启动简单后端服务...")
    print("📊 支持详细进度显示")
    print("🌐 服务地址: http://localhost:8001")
    print("📖 API文档: http://localhost:8001/docs")
    print("")
    print("按 Ctrl+C 停止服务")
    
    # 使用不同的端口避免冲突
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )