#!/usr/bin/env python3
"""
在服务器环境中运行调试脚本
模拟 tradingagents_server.py 的环境
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径（模拟服务器启动）
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 初始化日志系统（模拟服务器）
try:
    from tradingagents.utils.logging_init import init_logging
    init_logging()
except Exception:
    pass

print("=" * 80)
print("🖥️  模拟服务器环境")
print("=" * 80)

# 运行调试脚本
exec(open('debug_akshare_env.py').read())

print("\n" + "=" * 80)
print("现在测试实际的 akshare 调用...")
print("=" * 80)

try:
    import akshare as ak
    import time
    
    print("\n📊 测试 stock_zh_a_spot()...")
    start = time.time()
    df = ak.stock_zh_a_spot()
    elapsed = time.time() - start
    
    if df is not None and not df.empty:
        print(f"   ✅ 成功获取 {len(df)} 条数据 (耗时 {elapsed:.2f}秒)")
    else:
        print(f"   ⚠️ 返回空数据")
        
except Exception as e:
    print(f"   ❌ 失败: {e}")
    import traceback
    traceback.print_exc()
