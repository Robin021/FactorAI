#!/usr/bin/env python3
"""
TradingAgents 分析启动脚本

使用方法：
    python run_analysis.py --stock 601138
    python run_analysis.py --stock 600519 --date 2025-10-29
"""

import sys
import os

# 确保项目根目录在Python路径中
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入并运行CLI
from cli.main import app

if __name__ == "__main__":
    app()
