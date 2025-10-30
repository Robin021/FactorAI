#!/usr/bin/env python3
"""检查指数数据的列名"""

import akshare as ak

print("检查指数数据列名:")
print("=" * 80)

indices = {
    'sh000001': '上证指数',
    'sz399001': '深证成指',
    'sz399006': '创业板指'
}

for symbol, name in indices.items():
    print(f"\n{name} ({symbol}):")
    try:
        df = ak.stock_zh_index_daily(symbol=symbol)
        print(f"  ✅ 获取成功，{len(df)} 条记录")
        print(f"  列名: {list(df.columns)}")
        if not df.empty:
            print(f"  最新一行:")
            print(df.iloc[-1])
    except Exception as e:
        print(f"  ❌ 失败: {e}")

print("\n" + "=" * 80)
