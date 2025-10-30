#!/usr/bin/env python3
"""分析市场热度计算逻辑"""

from tradingagents.agents.utils.market_heat_calculator import MarketHeatCalculator

# 测试不同的输入值
test_cases = [
    {
        'name': '极冷市场',
        'params': {
            'volume_ratio': 0.5,
            'limit_up_ratio': 0.0,
            'turnover_rate': 2.0,
            'market_breadth': 0.3,
            'volatility': 1.0,
            'money_flow': -0.3
        }
    },
    {
        'name': '冷淡市场',
        'params': {
            'volume_ratio': 0.8,
            'limit_up_ratio': 0.005,
            'turnover_rate': 3.0,
            'market_breadth': 0.4,
            'volatility': 1.5,
            'money_flow': -0.1
        }
    },
    {
        'name': '正常市场（目标）',
        'params': {
            'volume_ratio': 1.5,
            'limit_up_ratio': 0.025,
            'turnover_rate': 8.0,
            'market_breadth': 0.55,
            'volatility': 3.5,
            'money_flow': 0.1
        }
    },
    {
        'name': '火热市场',
        'params': {
            'volume_ratio': 2.0,
            'limit_up_ratio': 0.05,
            'turnover_rate': 12.0,
            'market_breadth': 0.7,
            'volatility': 5.0,
            'money_flow': 0.3
        }
    },
    {
        'name': '沸腾市场',
        'params': {
            'volume_ratio': 3.0,
            'limit_up_ratio': 0.08,
            'turnover_rate': 15.0,
            'market_breadth': 0.8,
            'volatility': 7.0,
            'money_flow': 0.5
        }
    }
]

print("=" * 80)
print("市场热度计算逻辑分析")
print("=" * 80)

for case in test_cases:
    print(f"\n📊 {case['name']}:")
    result = MarketHeatCalculator.calculate_market_heat(**case['params'])
    
    print(f"   热度评分: {result['heat_score']:.1f}")
    print(f"   热度等级: {result['heat_level_cn']}")
    print(f"   风险辩论: {result['risk_adjustment']['risk_rounds']}轮")
    
    print(f"   标准化组件:")
    for comp, value in result['components'].items():
        print(f"      {comp}: {value:.3f}")

print("\n" + "=" * 80)
print("✅ 分析完成")
print("=" * 80)
