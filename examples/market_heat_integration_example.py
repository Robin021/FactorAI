"""
市场热度集成示例

演示如何将市场热度评估集成到实际的股票分析流程中：
1. 获取实时市场数据
2. 计算市场热度
3. 根据市场热度动态调整风险控制策略
4. 生成投资建议
"""

import sys
sys.path.append('..')

from tradingagents.dataflows.market_heat_data import MarketHeatDataSource
from tradingagents.agents.utils.market_heat_calculator import MarketHeatCalculator


def analyze_with_market_heat(stock_code: str = "600519"):
    """
    结合市场热度进行股票分析
    
    Args:
        stock_code: 股票代码
    """
    print("=" * 80)
    print(f"📊 {stock_code} 股票分析（结合市场热度）")
    print("=" * 80)
    
    # 步骤1：获取市场整体数据
    print("\n🔍 步骤1：获取市场整体数据...")
    market_data = MarketHeatDataSource.get_market_overview()
    
    print(f"\n市场概况:")
    print(f"  - 涨停家数: {market_data['stats']['limit_up_count']}家 ({market_data['limit_up_ratio']:.2%})")
    print(f"  - 上涨家数: {market_data['stats']['up_count']}家 ({market_data['market_breadth']:.2%})")
    print(f"  - 平均换手率: {market_data['turnover_rate']:.2f}%")
    print(f"  - 成交量放大: {market_data['volume_ratio']:.2f}倍")
    print(f"  - 市场波动率: {market_data['volatility']:.2f}%")
    
    # 步骤2：计算市场热度
    print("\n🌡️  步骤2：计算市场热度...")
    heat_result = MarketHeatCalculator.calculate_market_heat(
        volume_ratio=market_data['volume_ratio'],
        limit_up_ratio=market_data['limit_up_ratio'],
        turnover_rate=market_data['turnover_rate'],
        market_breadth=market_data['market_breadth'],
        volatility=market_data['volatility'],
        money_flow=market_data['money_flow']
    )
    
    print(f"\n市场热度评分: {heat_result['heat_score']:.1f} / 100")
    print(f"热度等级: {heat_result['heat_level_cn']}")
    
    # 步骤3：获取风险控制调整参数
    print("\n⚙️  步骤3：风险控制参数调整...")
    risk_adj = heat_result['risk_adjustment']
    
    print(f"\n基于市场热度的风险控制调整:")
    print(f"  - 仓位倍数: {risk_adj['position_multiplier']:.2f}x")
    print(f"  - 止损收紧系数: {risk_adj['stop_loss_tightness']:.2f}x")
    print(f"  - 风险辩论轮次: {risk_adj['risk_rounds']}轮")
    
    # 步骤4：应用到具体交易策略
    print(f"\n📈 步骤4：应用到 {stock_code} 的交易策略...")
    
    # 假设的基础策略参数
    base_position = 0.30  # 基础30%仓位
    base_stop_loss = 0.05  # 基础5%止损
    
    # 根据市场热度调整
    adjusted_position = MarketHeatCalculator.adjust_position_size(
        base_position, heat_result['heat_score']
    )
    adjusted_stop_loss = MarketHeatCalculator.adjust_stop_loss(
        base_stop_loss, heat_result['heat_score']
    )
    
    print(f"\n调整后的交易参数:")
    print(f"  - 建议仓位: {base_position:.1%} → {adjusted_position:.1%}")
    print(f"  - 止损幅度: {base_stop_loss:.1%} → {adjusted_stop_loss:.1%}")
    
    # 步骤5：生成综合建议
    print(f"\n💡 步骤5：综合投资建议...")
    print(f"\n{heat_result['recommendation']}")
    
    # 步骤6：风险提示
    print(f"\n⚠️  风险提示:")
    if heat_result['heat_score'] >= 80:
        print("  ⚠️ 市场过热，注意随时获利了结")
        print("  ⚠️ 警惕追高风险，设置好止盈位")
        print("  ⚠️ 市场可能随时回调，保持警惕")
    elif heat_result['heat_score'] >= 60:
        print("  ✅ 市场活跃，可积极参与")
        print("  ✅ 注意选择优质标的")
        print("  ⚠️ 控制好仓位，不要过度杠杆")
    elif heat_result['heat_score'] >= 40:
        print("  😐 市场平稳，按常规策略操作")
        print("  ✅ 适合中长期布局")
    elif heat_result['heat_score'] >= 20:
        print("  ⚠️ 市场冷淡，降低仓位")
        print("  ⚠️ 避免追涨，等待机会")
        print("  ✅ 可关注超跌优质股")
    else:
        print("  🚨 市场极度低迷，大幅降低仓位")
        print("  🚨 以防守为主，保存实力")
        print("  🚨 等待市场转暖信号")
    
    print("\n" + "=" * 80)
    print("✅ 分析完成！")
    print("=" * 80)
    
    return {
        'market_data': market_data,
        'heat_result': heat_result,
        'adjusted_position': adjusted_position,
        'adjusted_stop_loss': adjusted_stop_loss
    }


def compare_different_market_conditions():
    """
    对比不同市场状态下的策略差异
    """
    print("\n" + "=" * 80)
    print("📊 不同市场状态下的策略对比")
    print("=" * 80)
    
    scenarios = [
        {
            'name': '极冷市场（熊市底部）',
            'volume_ratio': 0.5,
            'limit_up_ratio': 0.001,
            'turnover_rate': 2.0,
            'market_breadth': 0.2,
            'volatility': 1.5,
            'money_flow': -0.5
        },
        {
            'name': '正常市场（震荡市）',
            'volume_ratio': 1.0,
            'limit_up_ratio': 0.01,
            'turnover_rate': 5.0,
            'market_breadth': 0.5,
            'volatility': 2.0,
            'money_flow': 0.0
        },
        {
            'name': '火热市场（牛市中期）',
            'volume_ratio': 2.5,
            'limit_up_ratio': 0.05,
            'turnover_rate': 12.0,
            'market_breadth': 0.75,
            'volatility': 4.0,
            'money_flow': 0.6
        },
        {
            'name': '沸腾市场（牛市顶部）',
            'volume_ratio': 3.5,
            'limit_up_ratio': 0.12,
            'turnover_rate': 18.0,
            'market_breadth': 0.85,
            'volatility': 6.0,
            'money_flow': 0.8
        }
    ]
    
    base_position = 0.30
    base_stop_loss = 0.05
    
    print(f"\n基础策略: 仓位{base_position:.0%}, 止损{base_stop_loss:.0%}\n")
    print(f"{'市场状态':<20} | {'热度':<6} | {'仓位':<8} | {'止损':<8} | {'辩论轮次':<8}")
    print("-" * 80)
    
    for scenario in scenarios:
        result = MarketHeatCalculator.calculate_market_heat(**{
            k: v for k, v in scenario.items() if k != 'name'
        })
        
        adj_pos = MarketHeatCalculator.adjust_position_size(
            base_position, result['heat_score']
        )
        adj_stop = MarketHeatCalculator.adjust_stop_loss(
            base_stop_loss, result['heat_score']
        )
        
        print(
            f"{scenario['name']:<20} | "
            f"{result['heat_score']:>5.1f} | "
            f"{adj_pos:>7.1%} | "
            f"{adj_stop:>7.1%} | "
            f"{result['risk_adjustment']['risk_rounds']:>8}轮"
        )
    
    print("\n💡 关键洞察:")
    print("  1. 市场越热，仓位越高，止损越宽松，给予更多波动空间")
    print("  2. 市场越冷，仓位越低，止损越严格，快速止损保护资金")
    print("  3. 火热市场增加风险辩论轮次，充分讨论机会与风险")
    print("  4. 冷淡市场减少辩论轮次，快速决策避免错失时机")
    print()


if __name__ == "__main__":
    # 示例1：实时市场分析
    print("\n" + "=" * 80)
    print("示例1：基于实时市场数据的分析")
    print("=" * 80)
    
    try:
        result = analyze_with_market_heat("600519")
    except Exception as e:
        print(f"\n⚠️ 无法获取实时数据: {e}")
        print("使用模拟数据进行演示...\n")
    
    # 示例2：不同市场状态对比
    compare_different_market_conditions()
    
    print("\n" + "=" * 80)
    print("✅ 所有示例运行完成！")
    print("=" * 80)
    print("\n💡 总结:")
    print("  - 市场热度量化了市场的活跃程度和情绪")
    print("  - 根据市场热度动态调整风险控制策略更科学")
    print("  - 热市场时可以更激进，冷市场时应该更保守")
    print("  - 这种动态调整避免了'一刀切'的风险控制问题")
    print()
