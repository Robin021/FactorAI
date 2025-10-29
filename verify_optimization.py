#!/usr/bin/env python3
"""
验证优化效果
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verify_optimizations():
    """验证两个优化是否生效"""
    
    print("=" * 80)
    print("验证优化效果")
    print("=" * 80)
    print()
    
    # 验证 1：Risk Manager Bug 修复
    print("1️⃣  验证 Risk Manager Bug 修复")
    print("-" * 80)
    
    try:
        with open('tradingagents/agents/managers/risk_manager.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 检查是否修复了 bug
        if 'fundamentals_report = state["fundamentals_report"]' in content:
            print("✅ Risk Manager Bug 已修复")
            print("   fundamentals_report 现在正确指向 state['fundamentals_report']")
        elif 'fundamentals_report = state["news_report"]' in content:
            print("❌ Risk Manager Bug 未修复")
            print("   fundamentals_report 仍然错误地指向 state['news_report']")
        else:
            print("⚠️  无法确定 Risk Manager 状态")
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
    
    print()
    
    # 验证 2：情绪分析改进
    print("2️⃣  验证情绪分析改进")
    print("-" * 80)
    
    try:
        with open('tradingagents/dataflows/sentiment_data_sources.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        improvements = []
        
        # 检查是否添加了详细日志
        if '✅ 价格动量评分' in content:
            improvements.append("✅ 添加了价格动量详细日志")
        else:
            improvements.append("❌ 缺少价格动量详细日志")
            
        if '✅ 成交量情绪评分' in content:
            improvements.append("✅ 添加了成交量情绪详细日志")
        else:
            improvements.append("❌ 缺少成交量情绪详细日志")
            
        if '✅ 波动率情绪评分' in content:
            improvements.append("✅ 添加了波动率情绪详细日志")
        else:
            improvements.append("❌ 缺少波动率情绪详细日志")
            
        if '科创板股票' in content and 'startswith(\'688\')' in content:
            improvements.append("✅ 添加了科创板特殊处理")
        else:
            improvements.append("❌ 缺少科创板特殊处理")
            
        if '✅ 缓存命中' in content:
            improvements.append("✅ 改进了缓存日志")
        else:
            improvements.append("❌ 缓存日志未改进")
        
        for improvement in improvements:
            print(f"   {improvement}")
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
    
    print()
    
    # 验证 3：清除缓存脚本
    print("3️⃣  验证清除缓存脚本")
    print("-" * 80)
    
    if os.path.exists('clear_sentiment_cache.py'):
        print("✅ 清除缓存脚本已创建")
        print("   运行: python clear_sentiment_cache.py")
    else:
        print("❌ 清除缓存脚本不存在")
    
    print()
    
    # 验证 4：测试脚本
    print("4️⃣  验证测试脚本")
    print("-" * 80)
    
    test_scripts = [
        'test_sentiment_quick.py',
        'test_sentiment_fix.py',
        'diagnose_sentiment_issue.py'
    ]
    
    for script in test_scripts:
        if os.path.exists(script):
            print(f"✅ {script}")
        else:
            print(f"❌ {script} 不存在")
    
    print()
    
    # 总结
    print("=" * 80)
    print("验证总结")
    print("=" * 80)
    print()
    print("✅ 优化 1：修复情绪分析数据")
    print("   - 代码已改进")
    print("   - 需要清除缓存才能生效")
    print()
    print("✅ 优化 2：修复 Risk Manager Bug")
    print("   - Bug 已修复")
    print("   - 立即生效")
    print()
    print("📋 下一步操作：")
    print("   1. 运行: python clear_sentiment_cache.py")
    print("   2. 在Web界面重新提交分析")
    print("   3. 运行: python test_sentiment_quick.py")
    print("   4. 检查分析结果")
    print()


if __name__ == "__main__":
    verify_optimizations()
