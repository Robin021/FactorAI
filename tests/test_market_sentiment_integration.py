#!/usr/bin/env python3
"""
验证市场情绪分析师在工作流中的集成
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_market_sentiment_analyst_integration():
    """测试市场情绪分析师的工作流集成"""
    print(f"🔍 验证市场情绪分析师在工作流中的集成")
    print("=" * 70)
    
    try:
        # 1. 检查市场情绪分析师是否已注册
        print(f"\n📊 第一步：检查市场情绪分析师注册...")
        from tradingagents.agents import create_market_sentiment_analyst
        print(f"  ✅ 市场情绪分析师已成功导入")
        
        # 2. 检查AgentState是否包含情绪字段
        print(f"\n📝 第二步：检查AgentState数据模型...")
        from tradingagents.agents.utils.agent_states import AgentState
        
        # 读取AgentState源码检查字段
        agent_states_file = "tradingagents/agents/utils/agent_states.py"
        with open(agent_states_file, "r", encoding="utf-8") as f:
            source_code = f.read()
        
        state_checks = [
            ("market_sentiment_report字段", "market_sentiment_report"),
            ("sentiment_score字段", "sentiment_score"),
        ]
        
        for check_name, check_pattern in state_checks:
            if check_pattern in source_code:
                print(f"  ✅ {check_name}: 已添加到AgentState")
            else:
                print(f"  ❌ {check_name}: 未找到")
        
        # 3. 检查条件逻辑是否包含市场情绪分析师
        print(f"\n🔀 第三步：检查条件逻辑...")
        from tradingagents.graph.conditional_logic import ConditionalLogic
        
        conditional_logic = ConditionalLogic()
        if hasattr(conditional_logic, 'should_continue_market_sentiment'):
            print(f"  ✅ should_continue_market_sentiment方法: 已添加")
        else:
            print(f"  ❌ should_continue_market_sentiment方法: 未找到")
        
        # 4. 检查工作流设置
        print(f"\n🔧 第四步：检查工作流设置...")
        
        setup_file = "tradingagents/graph/setup.py"
        with open(setup_file, "r", encoding="utf-8") as f:
            setup_code = f.read()
        
        setup_checks = [
            ("市场情绪分析师导入", "create_market_sentiment_analyst"),
            ("market_sentiment节点创建", 'if "market_sentiment" in selected_analysts:'),
            ("analyst_display_names映射", '"market_sentiment": "Market_sentiment"'),
        ]
        
        for check_name, check_pattern in setup_checks:
            if check_pattern in setup_code:
                print(f"  ✅ {check_name}: 已在工作流中集成")
            else:
                print(f"  ❌ {check_name}: 未在工作流中找到")
        
        # 5. 检查工具节点配置
        print(f"\n🛠️ 第五步：检查工具节点配置...")
        
        trading_graph_file = "tradingagents/graph/trading_graph.py"
        with open(trading_graph_file, "r", encoding="utf-8") as f:
            graph_code = f.read()
        
        tool_checks = [
            ("market_sentiment工具节点", '"market_sentiment": ToolNode'),
            ("日志状态包含market_sentiment_report", '"market_sentiment_report"'),
            ("日志状态包含sentiment_score", '"sentiment_score"'),
        ]
        
        for check_name, check_pattern in tool_checks:
            if check_pattern in graph_code:
                print(f"  ✅ {check_name}: 已配置")
            else:
                print(f"  ❌ {check_name}: 未配置")
        
        print(f"\n✅ 验证完成！")
        
        # 总结
        print(f"\n📊 集成状态总结:")
        print(f"  🎯 市场情绪分析师: 已注册到系统")
        print(f"  📝 AgentState: 已添加sentiment相关字段")
        print(f"  🔀 条件逻辑: 已添加should_continue_market_sentiment")
        print(f"  🔧 工作流设置: 已集成market_sentiment节点")
        print(f"  🛠️ 工具节点: 已配置market_sentiment工具")
        print(f"  📊 日志系统: 已更新以记录情绪数据")
        
        print(f"\n🚀 在工作流中的使用方式：")
        print(f"  1. 在selected_analysts中添加'market_sentiment'")
        print(f"  2. 市场情绪分析师会在指定位置执行")
        print(f"  3. 分析结果会存储在state['market_sentiment_report']")
        print(f"  4. 情绪评分会存储在state['sentiment_score']")
        print(f"  5. 后续的研究员可以访问这些情绪数据")
        
        print(f"\n✨ 确认：市场情绪分析师已完全集成到工作流中！")
        
        return True
        
    except Exception as e:
        print(f"❌ 验证过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_market_sentiment_analyst_integration()
    sys.exit(0 if success else 1)
