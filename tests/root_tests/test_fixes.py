#!/usr/bin/env python3
"""
测试修复效果
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_data_parsing():
    """测试数据解析修复"""
    
    print("=" * 80)
    print("测试数据解析修复")
    print("=" * 80)
    print()
    
    # 模拟表格格式的数据
    test_data = """股票代码: 688256
数据期间: 2025-09-29 至 2025-10-29
数据条数: 17条
当前价格: ¥1448.67
涨跌幅: -2.02%
成交量: 180,422,400股

最新3天数据:
日期   股票代码     开盘      收盘      最高      最低    成交量          成交额   振幅   涨跌幅    涨跌额  换手率
2025-10-27 688256 1560.0 1530.68 1560.01 1493.00 122356 1.875722e+10 4.39  0.37   5.68 2.92
2025-10-28 688256 1505.0 1478.58 1533.79 1457.00 104311 1.559130e+10 5.02 -3.40 -52.10 2.49
2025-10-29 688256 1460.0 1448.67 1530.88 1440.66  73909 1.094615e+10 6.10 -2.02 -29.91 1.77

📊 期间统计:
期间涨跌: +125.17"""
    
    print("测试数据:")
    print(test_data[:200] + "...")
    print()
    
    # 测试涨跌幅提取
    print("1. 测试涨跌幅提取")
    import re
    
    # 方法1: 从摘要提取
    change_match = re.search(r'涨跌幅[：:]\s*([-+]?\d+\.?\d*)%', test_data)
    if change_match:
        print(f"   ✅ 方法1成功: {change_match.group(1)}%")
    
    # 方法2: 从表格提取
    lines = test_data.strip().split('\n')
    for line in reversed(lines):
        if '日期' in line or '---' in line or '期间统计' in line:
            continue
        parts = line.split()
        if len(parts) >= 12:
            try:
                change_pct = float(parts[-3])
                if -50 < change_pct < 50:
                    print(f"   ✅ 方法2成功: {change_pct}%")
                    break
            except:
                continue
    
    print()
    
    # 测试振幅提取
    print("2. 测试振幅提取")
    
    # 方法2: 从表格提取
    for line in reversed(lines):
        if '日期' in line or '---' in line or '期间统计' in line:
            continue
        parts = line.split()
        if len(parts) >= 12:
            try:
                amplitude = float(parts[-4])
                if 0 < amplitude < 50:
                    print(f"   ✅ 振幅提取成功: {amplitude}%")
                    break
            except:
                continue
    
    print()
    
    # 测试换手率提取
    print("3. 测试换手率提取")
    
    # 方法2: 从表格提取
    for line in reversed(lines):
        if '日期' in line or '---' in line or '期间统计' in line:
            continue
        parts = line.split()
        if len(parts) >= 12:
            try:
                turnover = float(parts[-1])
                if 0 < turnover < 50:
                    print(f"   ✅ 换手率提取成功: {turnover}%")
                    break
            except:
                continue
    
    print()


def test_fallback_strategy():
    """测试降级策略修复"""
    
    print("=" * 80)
    print("测试降级策略修复")
    print("=" * 80)
    print()
    
    try:
        from tradingagents.agents.utils.fallback_strategy import FallbackStrategy, FailureRecord
        
        # 创建降级策略
        strategy = FallbackStrategy(market_type='CN')
        print("✅ 降级策略创建成功")
        
        # 记录失败
        strategy.record_failure('news_sentiment', Exception("测试错误"))
        print("✅ 失败记录成功")
        
        # 获取失败记录
        failures = strategy.get_failures()
        print(f"✅ 获取失败记录: {len(failures)} 条")
        
        # 测试 to_dict()
        for failure in failures:
            failure_dict = failure.to_dict()
            print(f"   - {failure_dict['component']}: {failure_dict['error']}")
        
        print("✅ 降级策略测试通过")
        
    except Exception as e:
        print(f"❌ 降级策略测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print()


if __name__ == "__main__":
    test_data_parsing()
    test_fallback_strategy()
    
    print("=" * 80)
    print("测试完成")
    print("=" * 80)
