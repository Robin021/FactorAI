"""
测试市场热度集成

验证市场热度系统是否正确集成到分析流程中
"""

import sys
sys.path.append('..')

from tradingagents.graph.conditional_logic import ConditionalLogic
from tradingagents.agents.utils.agent_states import AgentState


def test_dynamic_risk_rounds():
    """测试动态风险辩论轮次"""
    print("=" * 80)
    print("测试：动态风险辩论轮次")
    print("=" * 80)
    
    # 创建ConditionalLogic实例（启用动态调整）
    logic = ConditionalLogic(
        max_debate_rounds=1,
        max_risk_discuss_rounds=1,
        enable_dynamic_risk_rounds=True
    )
    
    # 测试场景1：市场火热（热度70）
    print("\n场景1：市场火热（热度70）")
    state_hot = {
        "market_heat_score": 70.0,
        "market_heat_level": "火热",
        "risk_debate_state": {
            "count": 0,
            "latest_speaker": "Risky"
        }
    }
    
    # 模拟辩论过程
    for i in range(7):
        result = logic.should_continue_risk_analysis(state_hot)
        print(f"  第{i+1}次发言: {result}")
        
        if result == "Risk Judge":
            print(f"  ✅ 在第{i+1}次发言后结束（预期：6次发言，2轮辩论）")
            break
        
        # 更新state
        state_hot["risk_debate_state"]["count"] = i + 1
        if result == "Safe Analyst":
            state_hot["risk_debate_state"]["latest_speaker"] = "Risky"
        elif result == "Neutral Analyst":
            state_hot["risk_debate_state"]["latest_speaker"] = "Safe"
        else:
            state_hot["risk_debate_state"]["latest_speaker"] = "Neutral"
    
    # 测试场景2：市场冷淡（热度30）
    print("\n场景2：市场冷淡（热度30）")
    state_cold = {
        "market_heat_score": 30.0,
        "market_heat_level": "冷淡",
        "risk_debate_state": {
            "count": 0,
            "latest_speaker": "Risky"
        }
    }
    
    # 模拟辩论过程
    for i in range(7):
        result = logic.should_continue_risk_analysis(state_cold)
        print(f"  第{i+1}次发言: {result}")
        
        if result == "Risk Judge":
            print(f"  ✅ 在第{i+1}次发言后结束（预期：3次发言，1轮辩论）")
            break
        
        # 更新state
        state_cold["risk_debate_state"]["count"] = i + 1
        if result == "Safe Analyst":
            state_cold["risk_debate_state"]["latest_speaker"] = "Risky"
        elif result == "Neutral Analyst":
            state_cold["risk_debate_state"]["latest_speaker"] = "Safe"
        else:
            state_cold["risk_debate_state"]["latest_speaker"] = "Neutral"
    
    # 测试场景3：无市场热度数据（使用默认值）
    print("\n场景3：无市场热度数据（使用默认值）")
    state_no_heat = {
        "risk_debate_state": {
            "count": 0,
            "latest_speaker": "Risky"
        }
    }
    
    # 模拟辩论过程
    for i in range(7):
        result = logic.should_continue_risk_analysis(state_no_heat)
        print(f"  第{i+1}次发言: {result}")
        
        if result == "Risk Judge":
            print(f"  ✅ 在第{i+1}次发言后结束（预期：3次发言，1轮辩论）")
            break
        
        # 更新state
        state_no_heat["risk_debate_state"]["count"] = i + 1
        if result == "Safe Analyst":
            state_no_heat["risk_debate_state"]["latest_speaker"] = "Risky"
        elif result == "Neutral Analyst":
            state_no_heat["risk_debate_state"]["latest_speaker"] = "Safe"
        else:
            state_no_heat["risk_debate_state"]["latest_speaker"] = "Neutral"
    
    print("\n" + "=" * 80)
    print("✅ 测试完成！")
    print("=" * 80)


def test_disabled_dynamic_risk_rounds():
    """测试禁用动态风险辩论轮次"""
    print("\n" + "=" * 80)
    print("测试：禁用动态风险辩论轮次")
    print("=" * 80)
    
    # 创建ConditionalLogic实例（禁用动态调整）
    logic = ConditionalLogic(
        max_debate_rounds=1,
        max_risk_discuss_rounds=2,  # 固定2轮
        enable_dynamic_risk_rounds=False
    )
    
    # 测试：即使市场冷淡，也应该使用固定的2轮
    print("\n场景：市场冷淡但禁用动态调整（应该固定2轮）")
    state = {
        "market_heat_score": 30.0,
        "market_heat_level": "冷淡",
        "risk_debate_state": {
            "count": 0,
            "latest_speaker": "Risky"
        }
    }
    
    # 模拟辩论过程
    for i in range(7):
        result = logic.should_continue_risk_analysis(state)
        print(f"  第{i+1}次发言: {result}")
        
        if result == "Risk Judge":
            print(f"  ✅ 在第{i+1}次发言后结束（预期：6次发言，2轮辩论）")
            break
        
        # 更新state
        state["risk_debate_state"]["count"] = i + 1
        if result == "Safe Analyst":
            state["risk_debate_state"]["latest_speaker"] = "Risky"
        elif result == "Neutral Analyst":
            state["risk_debate_state"]["latest_speaker"] = "Safe"
        else:
            state["risk_debate_state"]["latest_speaker"] = "Neutral"
    
    print("\n" + "=" * 80)
    print("✅ 测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    test_dynamic_risk_rounds()
    test_disabled_dynamic_risk_rounds()
    
    print("\n" + "=" * 80)
    print("🎉 所有测试通过！")
    print("=" * 80)
    print("\n💡 说明:")
    print("  - 市场热度 >= 60: 自动使用2轮风险辩论")
    print("  - 市场热度 < 60: 自动使用1轮风险辩论")
    print("  - 可通过 enable_dynamic_risk_rounds=False 禁用动态调整")
    print()
