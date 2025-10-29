#!/usr/bin/env python3
"""
测试情绪权重修复
验证新的权重配置和背离检测功能
"""

import sys
sys.path.insert(0, '.')

from tradingagents.agents.utils.sentiment_calculator import SentimentCalculator

def test_old_vs_new_weights():
    """测试旧权重 vs 新权重的差异"""
    
    print("=" * 80)
    print("测试案例: 股票 688256 (寒武纪)")
    print("=" * 80)
    
    # 实际数据
    components = {
        'news': 1.0,
        'technical': -0.226,
        'volume': -0.033,
        'money_flow': 0.0,
        'volatility': -0.010,
        'margin': 0.0
    }
    
    print("\n组件评分:")
    for comp, score in components.items():
        print(f"  {comp:15s}: {score:7.3f}")
    
    # 使用新权重计算
    calculator = SentimentCalculator()
    result = calculator.calculate_composite_score(components)
    
    print(f"\n使用新权重配置:")
    print(f"  综合评分: {result['score']:.2f} / 100")
    print(f"  情绪等级: {result['level']}")
    print(f"  原始评分: {result['raw_score']:.3f}")
    print(f"  总权重: {result['total_weight']:.2f}")
    
    print(f"\n组件贡献度:")
    for comp, contribution in result['breakdown'].items():
        print(f"  {comp:15s}: {contribution:7.3f}")
    
    # 检测背离
    print(f"\n背离检测:")
    divergence = calculator.detect_divergence(components)
    
    if divergence['has_divergence']:
        print(f"  ⚠️  检测到背离!")
        print(f"  背离类型: {divergence['divergence_type']}")
        print(f"  背离强度: {divergence['divergence_strength']:.2f}")
        print(f"  调整系数: {divergence['adjustment_factor']:.2f}")
        print(f"\n  {divergence['warning_message']}")
    else:
        print(f"  ✅ 未检测到背离")
    
    print("\n" + "=" * 80)
    print("结论:")
    print("=" * 80)
    
    if result['score'] < 60:
        print("✅ 修复成功! 评分现在更准确地反映了市场实际情况")
        print("   新闻虽然乐观，但价格和成交量都是负面的")
        print("   评分应该是中性或略微悲观，而不是乐观")
    else:
        print("⚠️  评分仍然偏高，可能需要进一步调整")
    
    if divergence['has_divergence']:
        print("✅ 背离检测工作正常! 系统能够识别\"卖出新闻\"模式")
    
    return result, divergence


def test_various_scenarios():
    """测试各种场景"""
    
    print("\n" + "=" * 80)
    print("测试其他场景")
    print("=" * 80)
    
    calculator = SentimentCalculator()
    
    scenarios = [
        {
            'name': '场景1: 全面乐观',
            'components': {
                'news': 0.8,
                'technical': 0.6,
                'volume': 0.5,
                'money_flow': 0.7,
                'volatility': 0.4
            }
        },
        {
            'name': '场景2: 全面悲观',
            'components': {
                'news': -0.8,
                'technical': -0.6,
                'volume': -0.5,
                'money_flow': -0.7,
                'volatility': -0.4
            }
        },
        {
            'name': '场景3: 买入逢低 (新闻悲观但价格强劲)',
            'components': {
                'news': -0.8,
                'technical': 0.5,
                'volume': 0.4,
                'money_flow': 0.3,
                'volatility': 0.2
            }
        },
        {
            'name': '场景4: 中性市场',
            'components': {
                'news': 0.1,
                'technical': -0.05,
                'volume': 0.02,
                'money_flow': 0.0,
                'volatility': -0.03
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}")
        print("-" * 80)
        
        result = calculator.calculate_composite_score(scenario['components'])
        divergence = calculator.detect_divergence(scenario['components'])
        
        print(f"  评分: {result['score']:.2f} / 100")
        print(f"  等级: {result['level']}")
        
        if divergence['has_divergence']:
            print(f"  ⚠️  背离: {divergence['divergence_type']} (强度: {divergence['divergence_strength']:.2f})")
        else:
            print(f"  ✅ 无背离")


def test_weight_distribution():
    """测试权重分布"""
    
    print("\n" + "=" * 80)
    print("权重配置检查")
    print("=" * 80)
    
    weights = SentimentCalculator.WEIGHTS
    
    print("\n当前权重配置:")
    total = 0
    for comp, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
        print(f"  {comp:15s}: {weight:.2%}")
        total += weight
    
    print(f"\n  总权重: {total:.2%}")
    
    if abs(total - 1.0) < 0.001:
        print("  ✅ 权重总和正确 (100%)")
    else:
        print(f"  ⚠️  权重总和不正确: {total:.2%}")
    
    # 检查关键组件
    critical_components = ['news', 'technical', 'volume']
    print(f"\n关键组件权重:")
    for comp in critical_components:
        if comp in weights:
            print(f"  ✅ {comp:15s}: {weights[comp]:.2%}")
        else:
            print(f"  ❌ {comp:15s}: 未配置")


if __name__ == "__main__":
    print("\n🔧 情绪权重修复测试\n")
    
    # 测试权重配置
    test_weight_distribution()
    
    # 测试实际案例
    result, divergence = test_old_vs_new_weights()
    
    # 测试其他场景
    test_various_scenarios()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)
    print("\n下一步:")
    print("1. 清除缓存: python clear_sentiment_cache.py")
    print("2. 重启后端服务")
    print("3. 重新分析股票 688256")
    print("4. 验证新的评分和背离警告")
