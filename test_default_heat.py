#!/usr/bin/env python3
"""测试默认市场热度值"""

from tradingagents.agents.utils.market_heat_calculator import MarketHeatCalculator

# 旧的默认值
old_defaults = {
    'volume_ratio': 1.0,
    'limit_up_ratio': 0.01,
    'turnover_rate': 5.0,
    'market_breadth': 0.5,
    'volatility': 2.0,
    'money_flow': 0.0
}

# 新的默认值（优化后）
new_defaults = {
    'volume_ratio': 1.8,
    'limit_up_ratio': 0.04,
    'turnover_rate': 11.0,
    'market_breadth': 0.6,
    'volatility': 3.0,
    'money_flow': 0.2
}

print("=" * 80)
print("市场热度默认值对比测试")
print("=" * 80)

print("\n📊 旧默认值:")
old_result = MarketHeatCalculator.calculate_market_heat(**old_defaults)
print(f"   热度评分: {old_result['heat_score']}")
print(f"   热度等级: {old_result['heat_level_cn']}")
print(f"   风险辩论: {old_result['risk_adjustment']['risk_rounds']}轮")
print(f"   仓位倍数: {old_result['risk_adjustment']['position_multiplier']}x")

print("\n📊 新默认值:")
new_result = MarketHeatCalculator.calculate_market_heat(**new_defaults)
print(f"   热度评分: {new_result['heat_score']}")
print(f"   热度等级: {new_result['heat_level_cn']}")
print(f"   风险辩论: {new_result['risk_adjustment']['risk_rounds']}轮")
print(f"   仓位倍数: {new_result['risk_adjustment']['position_multiplier']}x")

print("\n" + "=" * 80)
print("✅ 测试完成")
print("=" * 80)
