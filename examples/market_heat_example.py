"""
市场热度计算器使用示例

演示如何使用市场热度计算器来：
1. 评估当前市场热度
2. 动态调整风险控制参数
3. 根据市场状态调整交易策略
"""

import sys
sys.path.append('..')

from tradingagents.agents.utils.market_heat_calculator import MarketHeatCalculator


def example_1_normal_market():
    """示例1：正常市场状态"""
    print("=" * 80)
    print("示例1：正常市场状态")
    print("=" * 80)
    
    result = MarketHeatCalculator.calculate_market_heat(
        volume_ratio=1.0,        # 成交量正常
        limit_up_ratio=0.01,     # 1%涨停（正常）
        turnover_rate=5.0,       # 5%换手率（正常）
        market_breadth=0.5,      # 50%股票上涨
        volatility=2.0,          # 2%波动率（正常）
        money_flow=0.0           # 资金平衡
    )
    
    print(f"\n📊 市场热度评分: {result['heat_score']:.1f}")
    print(f"🌡️  热度等级: {result['heat_level_cn']}")
    print(f"\n💡 策略建议:\n{result['recommendation']}")
    print(f"\n⚙️  风险控制参数:")
    print(f"   - 仓位倍数: {result['risk_adjustment']['position_multiplier']:.2f}")
    print(f"   - 止损收紧系数: {result['risk_adjustment']['stop_loss_tightness']:.2f}")
    print(f"   - 风险辩论轮次: {result['risk_adjustment']['risk_rounds']}")
    print()


def example_2_hot_market():
    """示例2：火热市场（牛市）"""
    print("=" * 80)
    print("示例2：火热市场（牛市）")
    print("=" * 80)
    
    result = MarketHeatCalculator.calculate_market_heat(
        volume_ratio=2.5,        # 成交量放大2.5倍
        limit_up_ratio=0.05,     # 5%涨停（活跃）
        turnover_rate=12.0,      # 12%换手率（活跃）
        market_breadth=0.75,     # 75%股票上涨
        volatility=4.0,          # 4%波动率（较高）
        money_flow=0.6           # 大量资金流入
    )
    
    print(f"\n📊 市场热度评分: {result['heat_score']:.1f}")
    print(f"🌡️  热度等级: {result['heat_level_cn']}")
    print(f"\n💡 策略建议:\n{result['recommendation']}")
    print(f"\n⚙️  风险控制参数:")
    print(f"   - 仓位倍数: {result['risk_adjustment']['position_multiplier']:.2f}")
    print(f"   - 止损收紧系数: {result['risk_adjustment']['stop_loss_tightness']:.2f}")
    print(f"   - 风险辩论轮次: {result['risk_adjustment']['risk_rounds']}")
    
    # 演示仓位和止损调整
    base_position = 0.3  # 基础30%仓位
    base_stop_loss = 0.05  # 基础5%止损
    
    adjusted_position = MarketHeatCalculator.adjust_position_size(
        base_position, result['heat_score']
    )
    adjusted_stop_loss = MarketHeatCalculator.adjust_stop_loss(
        base_stop_loss, result['heat_score']
    )
    
    print(f"\n📈 仓位调整:")
    print(f"   基础仓位: {base_position:.1%} -> 调整后: {adjusted_position:.1%}")
    print(f"\n🛡️  止损调整:")
    print(f"   基础止损: {base_stop_loss:.1%} -> 调整后: {adjusted_stop_loss:.1%}")
    print()


def example_3_cold_market():
    """示例3：冷淡市场（熊市）"""
    print("=" * 80)
    print("示例3：冷淡市场（熊市）")
    print("=" * 80)
    
    result = MarketHeatCalculator.calculate_market_heat(
        volume_ratio=0.6,        # 成交量萎缩40%
        limit_up_ratio=0.002,    # 0.2%涨停（极少）
        turnover_rate=2.0,       # 2%换手率（低迷）
        market_breadth=0.25,     # 25%股票上涨（大部分下跌）
        volatility=1.5,          # 1.5%波动率（低）
        money_flow=-0.4          # 资金流出
    )
    
    print(f"\n📊 市场热度评分: {result['heat_score']:.1f}")
    print(f"🌡️  热度等级: {result['heat_level_cn']}")
    print(f"\n💡 策略建议:\n{result['recommendation']}")
    print(f"\n⚙️  风险控制参数:")
    print(f"   - 仓位倍数: {result['risk_adjustment']['position_multiplier']:.2f}")
    print(f"   - 止损收紧系数: {result['risk_adjustment']['stop_loss_tightness']:.2f}")
    print(f"   - 风险辩论轮次: {result['risk_adjustment']['risk_rounds']}")
    
    # 演示仓位和止损调整
    base_position = 0.3
    base_stop_loss = 0.05
    
    adjusted_position = MarketHeatCalculator.adjust_position_size(
        base_position, result['heat_score']
    )
    adjusted_stop_loss = MarketHeatCalculator.adjust_stop_loss(
        base_stop_loss, result['heat_score']
    )
    
    print(f"\n📈 仓位调整:")
    print(f"   基础仓位: {base_position:.1%} -> 调整后: {adjusted_position:.1%}")
    print(f"\n🛡️  止损调整:")
    print(f"   基础止损: {base_stop_loss:.1%} -> 调整后: {adjusted_stop_loss:.1%}")
    print()


def example_4_boiling_market():
    """示例4：沸腾市场（疯牛）"""
    print("=" * 80)
    print("示例4：沸腾市场（疯牛）")
    print("=" * 80)
    
    result = MarketHeatCalculator.calculate_market_heat(
        volume_ratio=3.5,        # 成交量放大3.5倍
        limit_up_ratio=0.12,     # 12%涨停（疯狂）
        turnover_rate=18.0,      # 18%换手率（极度活跃）
        market_breadth=0.85,     # 85%股票上涨
        volatility=6.0,          # 6%波动率（高）
        money_flow=0.8           # 资金疯狂流入
    )
    
    print(f"\n📊 市场热度评分: {result['heat_score']:.1f}")
    print(f"🌡️  热度等级: {result['heat_level_cn']}")
    print(f"\n💡 策略建议:\n{result['recommendation']}")
    print(f"\n⚙️  风险控制参数:")
    print(f"   - 仓位倍数: {result['risk_adjustment']['position_multiplier']:.2f}")
    print(f"   - 止损收紧系数: {result['risk_adjustment']['stop_loss_tightness']:.2f}")
    print(f"   - 风险辩论轮次: {result['risk_adjustment']['risk_rounds']}")
    print()


def example_5_risk_rounds_comparison():
    """示例5：不同市场状态下的风险辩论轮次对比"""
    print("=" * 80)
    print("示例5：风险辩论轮次对比")
    print("=" * 80)
    
    scenarios = [
        ("极冷市场", 15),
        ("冷淡市场", 30),
        ("正常市场", 50),
        ("火热市场", 70),
        ("沸腾市场", 90)
    ]
    
    print("\n市场状态 | 热度评分 | 风险辩论轮次 | 说明")
    print("-" * 80)
    
    for name, score in scenarios:
        rounds = MarketHeatCalculator.get_risk_rounds(score)
        heat_level = MarketHeatCalculator.get_heat_level(score)
        heat_level_cn = MarketHeatCalculator._get_heat_level_cn(heat_level)
        
        explanation = "保守策略，快速决策" if rounds == 1 else "积极策略，充分讨论"
        
        print(f"{name:8} | {score:8.0f} | {rounds:14} | {explanation}")
    
    print("\n💡 说明:")
    print("   - 市场冷淡时（热度<60）：1轮辩论，快速决策，避免过度分析")
    print("   - 市场火热时（热度≥60）：2轮辩论，充分讨论，把握机会")
    print()


if __name__ == "__main__":
    example_1_normal_market()
    example_2_hot_market()
    example_3_cold_market()
    example_4_boiling_market()
    example_5_risk_rounds_comparison()
    
    print("=" * 80)
    print("✅ 所有示例运行完成！")
    print("=" * 80)
