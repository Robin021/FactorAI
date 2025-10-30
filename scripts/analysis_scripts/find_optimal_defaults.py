#!/usr/bin/env python3
"""寻找最优的默认值，使热度评分接近50分（正常市场）"""

from tradingagents.agents.utils.market_heat_calculator import MarketHeatCalculator

def test_params(volume_ratio, limit_up_ratio, turnover_rate, market_breadth, volatility, money_flow):
    """测试一组参数"""
    result = MarketHeatCalculator.calculate_market_heat(
        volume_ratio=volume_ratio,
        limit_up_ratio=limit_up_ratio,
        turnover_rate=turnover_rate,
        market_breadth=market_breadth,
        volatility=volatility,
        money_flow=money_flow
    )
    return result['heat_score']

print("=" * 80)
print("寻找最优默认值（目标：热度评分 = 50分）")
print("=" * 80)

# 尝试不同的组合
candidates = []

for volume_ratio in [1.0, 1.2, 1.5, 1.8, 2.0]:
    for limit_up_ratio in [0.01, 0.02, 0.03, 0.04]:
        for turnover_rate in [5.0, 7.0, 9.0, 11.0]:
            for market_breadth in [0.5, 0.55, 0.6]:
                for volatility in [2.0, 3.0, 4.0]:
                    for money_flow in [0.0, 0.1, 0.2]:
                        score = test_params(
                            volume_ratio, limit_up_ratio, turnover_rate,
                            market_breadth, volatility, money_flow
                        )
                        
                        # 找接近50分的
                        if 48 <= score <= 52:
                            candidates.append({
                                'score': score,
                                'volume_ratio': volume_ratio,
                                'limit_up_ratio': limit_up_ratio,
                                'turnover_rate': turnover_rate,
                                'market_breadth': market_breadth,
                                'volatility': volatility,
                                'money_flow': money_flow
                            })

# 按评分排序，找最接近50的
candidates.sort(key=lambda x: abs(x['score'] - 50))

print(f"\n找到 {len(candidates)} 组接近50分的参数组合\n")

if candidates:
    print("前5个最优组合：\n")
    for i, c in enumerate(candidates[:5], 1):
        print(f"{i}. 热度评分: {c['score']:.2f}")
        print(f"   volume_ratio: {c['volume_ratio']}")
        print(f"   limit_up_ratio: {c['limit_up_ratio']}")
        print(f"   turnover_rate: {c['turnover_rate']}")
        print(f"   market_breadth: {c['market_breadth']}")
        print(f"   volatility: {c['volatility']}")
        print(f"   money_flow: {c['money_flow']}")
        print()

print("=" * 80)
print("✅ 搜索完成")
print("=" * 80)
