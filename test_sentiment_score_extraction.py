#!/usr/bin/env python3
"""
测试情绪评分提取功能
"""

def test_extract_sentiment_score():
    """测试情绪评分提取函数"""
    
    # 导入函数
    import sys
    import os
    sys.path.insert(0, os.path.abspath('.'))
    
    from tradingagents.agents.analysts.market_sentiment_analyst import _extract_sentiment_score
    
    print("=" * 80)
    print("测试情绪评分提取功能")
    print("=" * 80)
    
    # 测试用例
    test_cases = [
        # 标准格式
        ("- **综合情绪评分**: 65.50 / 100", 65.50),
        ("综合情绪评分: 72.3 / 100", 72.3),
        ("情绪评分：80.0", 80.0),
        
        # Markdown格式
        ("**综合情绪评分**: 55.5", 55.5),
        ("**情绪评分**: 45.2 / 100", 45.2),
        
        # 中文格式
        ("市场情绪：68.5", 68.5),
        ("评分：75.0 / 100", 75.0),
        ("综合评分为 82.3 分", 82.3),
        
        # 英文格式
        ("sentiment score: 60.5", 60.5),
        ("score: 70.0 / 100", 70.0),
        
        # 复杂报告
        ("""
        # 市场情绪数据
        
        **股票代码**: AAPL
        **分析日期**: 2024-10-27
        
        ## 综合情绪评估
        
        - **综合情绪评分**: 65.50 / 100
        - **情绪等级**: 乐观
        """, 65.50),
        
        # 无法提取的情况
        ("这是一个没有评分的报告", 50.0),
        ("", 50.0),
    ]
    
    passed = 0
    failed = 0
    
    for i, (report, expected) in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}:")
        print(f"  输入: {report[:50]}..." if len(report) > 50 else f"  输入: {report}")
        print(f"  期望: {expected}")
        
        try:
            result = _extract_sentiment_score(report)
            print(f"  结果: {result}")
            
            if abs(result - expected) < 0.01:  # 允许小的浮点误差
                print(f"  ✅ 通过")
                passed += 1
            else:
                print(f"  ❌ 失败 (期望 {expected}, 得到 {result})")
                failed += 1
        except Exception as e:
            print(f"  ❌ 异常: {e}")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 80)
    
    if failed == 0:
        print("\n✅ 所有测试通过！")
        return True
    else:
        print(f"\n❌ {failed} 个测试失败")
        return False

if __name__ == "__main__":
    success = test_extract_sentiment_score()
    exit(0 if success else 1)
