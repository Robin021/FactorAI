#!/usr/bin/env python3
"""验证市场热度默认值修复"""

from tradingagents.agents.utils.market_heat_calculator import MarketHeatCalculator
from tradingagents.dataflows.market_heat_data import MarketHeatDataSource

print("=" * 80)
print("🔧 验证市场热度默认值修复")
print("=" * 80)

# 1. 测试默认值
print("\n📊 步骤1：测试默认数据源")
default_data = MarketHeatDataSource._get_default_data("20251029")
print(f"   volume_ratio: {default_data['volume_ratio']}")
print(f"   limit_up_ratio: {default_data['limit_up_ratio']}")
print(f"   turnover_rate: {default_data['turnover_rate']}")
print(f"   market_breadth: {default_data['market_breadth']}")
print(f"   volatility: {default_data['volatility']}")
print(f"   money_flow: {default_data['money_flow']}")

# 2. 计算热度
print("\n🌡️ 步骤2：计算市场热度")
result = MarketHeatCalculator.calculate_market_heat(
    volume_ratio=default_data['volume_ratio'],
    limit_up_ratio=default_data['limit_up_ratio'],
    turnover_rate=default_data['turnover_rate'],
    market_breadth=default_data['market_breadth'],
    volatility=default_data['volatility'],
    money_flow=default_data['money_flow']
)

print(f"   热度评分: {result['heat_score']}")
print(f"   热度等级: {result['heat_level_cn']}")
print(f"   风险辩论: {result['risk_adjustment']['risk_rounds']}轮")
print(f"   仓位倍数: {result['risk_adjustment']['position_multiplier']}x")
print(f"   止损系数: {result['risk_adjustment']['stop_loss_tightness']}x")

# 3. 验证结果
print("\n✅ 步骤3：验证修复效果")
if 40 <= result['heat_score'] <= 60:
    print(f"   ✅ 热度评分在正常范围内 ({result['heat_score']:.1f}分)")
else:
    print(f"   ❌ 热度评分不在正常范围内 ({result['heat_score']:.1f}分)")

if result['heat_level'] == 'normal':
    print(f"   ✅ 热度等级为'正常'")
else:
    print(f"   ⚠️ 热度等级为'{result['heat_level_cn']}'（预期：正常）")

if result['risk_adjustment']['position_multiplier'] == 1.0:
    print(f"   ✅ 仓位倍数为标准值 (1.0x)")
else:
    print(f"   ⚠️ 仓位倍数为 {result['risk_adjustment']['position_multiplier']}x（预期：1.0x）")

# 4. 显示策略建议
print("\n💡 步骤4：策略建议")
print("-" * 80)
print(result['recommendation'])
print("-" * 80)

print("\n" + "=" * 80)
if 40 <= result['heat_score'] <= 60 and result['heat_level'] == 'normal':
    print("✅ 修复成功！默认值现在产生'正常'市场评分")
else:
    print("⚠️ 需要进一步调整")
print("=" * 80)
