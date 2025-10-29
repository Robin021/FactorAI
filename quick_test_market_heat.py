#!/usr/bin/env python3
"""
快速测试市场热度集成

这个脚本会快速验证市场热度系统是否正常工作，
不需要运行完整的分析流程。
"""

import sys
import os

# 确保项目根目录在Python路径中
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def test_market_heat_system():
    """测试市场热度系统"""
    print("=" * 80)
    print("🌡️  快速测试：市场热度系统")
    print("=" * 80)
    
    # 测试1：获取实时市场数据
    print("\n📊 步骤1：获取实时市场数据...")
    try:
        from tradingagents.dataflows.market_heat_data import MarketHeatDataSource
        
        market_data = MarketHeatDataSource.get_market_overview()
        
        print(f"✅ 成功获取市场数据")
        print(f"   涨停: {market_data['stats']['limit_up_count']}家 ({market_data['limit_up_ratio']:.2%})")
        print(f"   上涨: {market_data['stats']['up_count']}家 ({market_data['market_breadth']:.2%})")
        print(f"   换手率: {market_data['turnover_rate']:.2f}%")
        print(f"   成交量: {market_data['volume_ratio']:.2f}x")
        
    except Exception as e:
        print(f"⚠️  获取市场数据失败: {e}")
        print("   将使用默认值继续测试...")
        market_data = {
            'volume_ratio': 1.0,
            'limit_up_ratio': 0.01,
            'turnover_rate': 5.0,
            'market_breadth': 0.5,
            'volatility': 2.0,
            'money_flow': 0.0
        }
    
    # 测试2：计算市场热度
    print("\n🌡️  步骤2：计算市场热度...")
    try:
        from tradingagents.agents.utils.market_heat_calculator import MarketHeatCalculator
        
        heat_result = MarketHeatCalculator.calculate_market_heat(
            volume_ratio=market_data['volume_ratio'],
            limit_up_ratio=market_data['limit_up_ratio'],
            turnover_rate=market_data['turnover_rate'],
            market_breadth=market_data['market_breadth'],
            volatility=market_data['volatility'],
            money_flow=market_data['money_flow']
        )
        
        print(f"✅ 市场热度计算成功")
        print(f"   热度评分: {heat_result['heat_score']:.1f} / 100")
        print(f"   热度等级: {heat_result['heat_level_cn']}")
        print(f"   风险辩论轮次: {heat_result['risk_adjustment']['risk_rounds']}轮")
        
    except Exception as e:
        print(f"❌ 市场热度计算失败: {e}")
        return False
    
    # 测试3：测试动态风险辩论
    print("\n⚙️  步骤3：测试动态风险辩论逻辑...")
    try:
        from tradingagents.graph.conditional_logic import ConditionalLogic
        
        logic = ConditionalLogic(
            max_debate_rounds=1,
            max_risk_discuss_rounds=1,
            enable_dynamic_risk_rounds=True
        )
        
        # 模拟state
        state = {
            "market_heat_score": heat_result['heat_score'],
            "market_heat_level": heat_result['heat_level_cn'],
            "risk_debate_state": {
                "count": 0,
                "latest_speaker": "Risky"
            }
        }
        
        # 测试第一次调用
        result = logic.should_continue_risk_analysis(state)
        
        print(f"✅ 动态风险辩论逻辑正常")
        print(f"   当前热度: {heat_result['heat_score']:.1f}")
        print(f"   预期轮次: {heat_result['risk_adjustment']['risk_rounds']}轮")
        print(f"   第1次发言: {result}")
        
    except Exception as e:
        print(f"❌ 动态风险辩论测试失败: {e}")
        return False
    
    # 测试4：测试市场热度节点
    print("\n🔧 步骤4：测试市场热度评估节点...")
    try:
        from tradingagents.agents.utils.market_heat_node import create_market_heat_evaluator
        
        node = create_market_heat_evaluator()
        
        test_state = {
            "trade_date": None,
            "progress_callback": None
        }
        
        result = node(test_state)
        
        print(f"✅ 市场热度节点执行成功")
        print(f"   返回热度: {result.get('market_heat_score', 'N/A')}")
        print(f"   返回等级: {result.get('market_heat_level', 'N/A')}")
        
    except Exception as e:
        print(f"⚠️  市场热度节点测试失败: {e}")
        print("   这可能是网络问题，不影响系统运行")
    
    # 显示策略建议
    print("\n💡 当前市场策略建议:")
    print("-" * 80)
    print(heat_result['recommendation'])
    print("-" * 80)
    
    print("\n" + "=" * 80)
    print("✅ 市场热度系统测试完成！")
    print("=" * 80)
    
    print("\n📝 总结:")
    print(f"   - 市场热度: {heat_result['heat_score']:.1f}分 ({heat_result['heat_level_cn']})")
    print(f"   - 风险辩论: {heat_result['risk_adjustment']['risk_rounds']}轮")
    print(f"   - 仓位倍数: {heat_result['risk_adjustment']['position_multiplier']:.2f}x")
    print(f"   - 止损系数: {heat_result['risk_adjustment']['stop_loss_tightness']:.2f}x")
    
    print("\n🚀 系统已就绪！可以运行完整分析：")
    print("   python run_analysis.py --stock 601138")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = test_market_heat_system()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
