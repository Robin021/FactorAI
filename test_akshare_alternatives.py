#!/usr/bin/env python3
"""测试 akshare 的替代接口"""

import akshare as ak
import pandas as pd

print("=" * 80)
print("测试 AKShare 不同的市场数据接口")
print("=" * 80)

# 测试1：stock_zh_a_spot_em (当前使用的，失败的)
print("\n🔍 测试1: stock_zh_a_spot_em() - 当前使用的接口")
try:
    df = ak.stock_zh_a_spot_em()
    print(f"✅ 成功！获取到 {len(df)} 只股票")
    print(f"   列名: {df.columns.tolist()[:5]}...")
except Exception as e:
    print(f"❌ 失败: {type(e).__name__}: {e}")

# 测试2：stock_zh_a_hist (历史数据接口)
print("\n🔍 测试2: stock_zh_a_hist() - 历史数据接口")
try:
    # 获取上证指数最近的数据
    df = ak.stock_zh_index_daily(symbol="sh000001")
    if not df.empty:
        latest = df.iloc[-1]
        print(f"✅ 成功！上证指数最新数据:")
        print(f"   日期: {latest['日期']}")
        print(f"   收盘: {latest['收盘']}")
        print(f"   成交量: {latest['成交量']}")
except Exception as e:
    print(f"❌ 失败: {type(e).__name__}: {e}")

# 测试3：stock_zh_a_spot (另一个实时行情接口)
print("\n🔍 测试3: stock_zh_a_spot() - 另一个实时接口")
try:
    df = ak.stock_zh_a_spot()
    print(f"✅ 成功！获取到 {len(df)} 只股票")
    print(f"   列名: {df.columns.tolist()[:5]}...")
except Exception as e:
    print(f"❌ 失败: {type(e).__name__}: {e}")

# 测试4：stock_zh_a_new (新浪财经接口)
print("\n🔍 测试4: stock_zh_a_new() - 新浪财经接口")
try:
    df = ak.stock_zh_a_new()
    print(f"✅ 成功！获取到 {len(df)} 只股票")
    print(f"   列名: {df.columns.tolist()[:5]}...")
except Exception as e:
    print(f"❌ 失败: {type(e).__name__}: {e}")

# 测试5：stock_zh_a_minute (分钟数据)
print("\n🔍 测试5: stock_zh_index_spot() - 指数实时数据")
try:
    df = ak.stock_zh_index_spot()
    print(f"✅ 成功！获取到 {len(df)} 个指数")
    print(f"   列名: {df.columns.tolist()}")
    if not df.empty:
        print(f"   上证指数数据: {df[df['代码'] == '000001'].to_dict('records')}")
except Exception as e:
    print(f"❌ 失败: {type(e).__name__}: {e}")

print("\n" + "=" * 80)
print("📋 建议")
print("=" * 80)
print("""
如果 stock_zh_a_spot_em() 持续失败，可以考虑：

1. 使用其他成功的接口作为替代
2. 使用指数数据估算市场整体情况
3. 使用缓存的历史数据
4. 继续使用默认值（系统已有容错机制）
""")
