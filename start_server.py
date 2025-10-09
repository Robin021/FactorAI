#!/usr/bin/env python3
"""
TradingAgents-CN 服务器启动脚本
智能股票分析平台 - 企业级启动管理器
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def check_environment():
    """检查运行环境"""
    print("🔍 检查运行环境...")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ Python版本过低，需要Python 3.8+")
        return False
    
    print(f"✅ Python版本: {sys.version.split()[0]}")
    
    # 检查虚拟环境
    in_venv = (
        hasattr(sys, 'real_prefix') or 
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    )
    
    if in_venv:
        print("✅ 虚拟环境: 已激活")
    else:
        print("⚠️ 虚拟环境: 未激活 (建议使用虚拟环境)")
    
    # 检查必要的包
    try:
        import fastapi
        import uvicorn
        print(f"✅ FastAPI: {fastapi.__version__}")
        print(f"✅ Uvicorn: {uvicorn.__version__}")
    except ImportError as e:
        print(f"❌ 缺少依赖包: {e}")
        return False
    
    # 检查环境变量文件
    env_file = Path(".env")
    if env_file.exists():
        print("✅ 环境配置: .env 文件存在")
    else:
        print("⚠️ 环境配置: .env 文件不存在")
    
    return True

def start_server(host="0.0.0.0", port=8000, reload=True, workers=1):
    """启动服务器"""
    print("\n🚀 启动 TradingAgents-CN 服务器...")
    print("=" * 60)
    print("📈 智能股票分析平台 - 企业级 API 服务")
    print(f"🌐 服务地址: http://{host}:{port}")
    print(f"📚 API 文档: http://{host}:{port}/api/v1/docs")
    print(f"🔧 健康检查: http://{host}:{port}/api/v1/health")
    print("🔐 认证方式: 用户名密码 + Authing SSO")
    print("📊 支持市场: A股 + 美股 + 港股")
    print("=" * 60)
    
    # 构建启动命令 - 确保使用当前激活的Python环境
    python_executable = sys.executable
    print(f"🐍 使用Python: {python_executable}")
    
    cmd = [
        python_executable, "-m", "uvicorn",
        "backend.tradingagents_server:app",
        "--host", host,
        "--port", str(port),
        "--log-level", "info"
    ]
    
    if reload:
        cmd.append("--reload")
    
    if workers > 1:
        cmd.extend(["--workers", str(workers)])
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n⏹️ 服务器已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="TradingAgents-CN 服务器启动脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python start_server.py                    # 开发模式启动
  python start_server.py --prod             # 生产模式启动
  python start_server.py --port 8080        # 指定端口
  python start_server.py --workers 4        # 多进程模式
        """
    )
    
    parser.add_argument("--host", default="0.0.0.0", help="服务器地址 (默认: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="服务器端口 (默认: 8000)")
    parser.add_argument("--workers", type=int, default=1, help="工作进程数 (默认: 1)")
    parser.add_argument("--prod", action="store_true", help="生产模式 (禁用热重载)")
    parser.add_argument("--no-check", action="store_true", help="跳过环境检查")
    
    args = parser.parse_args()
    
    # 环境检查
    if not args.no_check:
        if not check_environment():
            print("\n❌ 环境检查失败，请修复后重试")
            sys.exit(1)
    
    # 启动服务器
    start_server(
        host=args.host,
        port=args.port,
        reload=not args.prod,
        workers=args.workers
    )

if __name__ == "__main__":
    main()