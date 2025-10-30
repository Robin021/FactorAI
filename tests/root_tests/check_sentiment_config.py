#!/usr/bin/env python3
"""
快速检查情绪分析配置
"""
import os
import sys

def check_config():
    """检查配置"""
    print("=" * 80)
    print("检查情绪分析配置")
    print("=" * 80)
    
    # 检查1: analysis_service.py中的默认分析师列表
    print("\n1. 检查 backend/services/analysis_service.py")
    try:
        with open('backend/services/analysis_service.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'market_sentiment' in content:
            # 查找具体行
            for i, line in enumerate(content.split('\n'), 1):
                if 'selected_analysts' in line and 'market_sentiment' in line:
                    print(f"   ✅ 找到配置 (第{i}行):")
                    print(f"      {line.strip()}")
                    break
        else:
            print("   ❌ 未找到 market_sentiment 配置")
    except Exception as e:
        print(f"   ❌ 读取文件失败: {e}")
    
    # 检查2: market_sentiment_analyst.py是否存在
    print("\n2. 检查市场情绪分析师文件")
    analyst_file = 'tradingagents/agents/analysts/market_sentiment_analyst.py'
    if os.path.exists(analyst_file):
        print(f"   ✅ {analyst_file} 存在")
        # 检查文件大小
        size = os.path.getsize(analyst_file)
        print(f"      文件大小: {size} 字节")
    else:
        print(f"   ❌ {analyst_file} 不存在")
    
    # 检查3: sentiment_tools.py是否存在
    print("\n3. 检查情绪分析工具文件")
    tools_file = 'tradingagents/tools/sentiment_tools.py'
    if os.path.exists(tools_file):
        print(f"   ✅ {tools_file} 存在")
        size = os.path.getsize(tools_file)
        print(f"      文件大小: {size} 字节")
    else:
        print(f"   ❌ {tools_file} 不存在")
    
    # 检查4: sentiment_data_sources.py是否存在
    print("\n4. 检查情绪数据源文件")
    sources_file = 'tradingagents/dataflows/sentiment_data_sources.py'
    if os.path.exists(sources_file):
        print(f"   ✅ {sources_file} 存在")
        size = os.path.getsize(sources_file)
        print(f"      文件大小: {size} 字节")
    else:
        print(f"   ❌ {sources_file} 不存在")
    
    # 检查5: sentiment_calculator.py是否存在
    print("\n5. 检查情绪计算器文件")
    calc_file = 'tradingagents/agents/utils/sentiment_calculator.py'
    if os.path.exists(calc_file):
        print(f"   ✅ {calc_file} 存在")
        size = os.path.getsize(calc_file)
        print(f"      文件大小: {size} 字节")
    else:
        print(f"   ❌ {calc_file} 不存在")
    
    # 检查6: conditional_logic.py中的条件函数
    print("\n6. 检查条件逻辑函数")
    try:
        with open('tradingagents/graph/conditional_logic.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'should_continue_market_sentiment' in content:
            print(f"   ✅ 找到 should_continue_market_sentiment 函数")
        else:
            print(f"   ❌ 未找到 should_continue_market_sentiment 函数")
    except Exception as e:
        print(f"   ❌ 读取文件失败: {e}")
    
    # 检查7: agent_states.py中的状态定义
    print("\n7. 检查状态定义")
    try:
        with open('tradingagents/agents/utils/agent_states.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        has_report = 'market_sentiment_report' in content
        has_score = 'sentiment_score' in content
        
        if has_report and has_score:
            print(f"   ✅ 找到 market_sentiment_report 和 sentiment_score 定义")
        else:
            if not has_report:
                print(f"   ❌ 未找到 market_sentiment_report 定义")
            if not has_score:
                print(f"   ❌ 未找到 sentiment_score 定义")
    except Exception as e:
        print(f"   ❌ 读取文件失败: {e}")
    
    # 检查8: setup.py中的分析师配置
    print("\n8. 检查工作流配置")
    try:
        with open('tradingagents/graph/setup.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'market_sentiment' in content:
            print(f"   ✅ 找到 market_sentiment 配置")
            # 统计出现次数
            count = content.count('market_sentiment')
            print(f"      出现次数: {count}")
        else:
            print(f"   ❌ 未找到 market_sentiment 配置")
    except Exception as e:
        print(f"   ❌ 读取文件失败: {e}")
    
    print("\n" + "=" * 80)
    print("检查完成")
    print("=" * 80)
    
    print("\n📝 总结:")
    print("   如果所有检查都通过（✅），说明情绪分析功能已正确配置")
    print("   重启后端服务后，所有分析请求都会自动包含市场情绪分析")
    print("\n🚀 下一步:")
    print("   1. 重启后端服务")
    print("   2. 运行测试: python test_sentiment_analysis.py")
    print("   3. 或发起一个分析请求，查看结果中的 market_sentiment_report")

if __name__ == "__main__":
    check_config()
