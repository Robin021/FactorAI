#!/usr/bin/env python3
"""
快速测试情绪分析核心组件
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_core_sentiment():
    """测试核心情绪数据源"""
    
    print("=" * 80)
    print("快速测试情绪分析核心组件")
    print("=" * 80)
    print()
    
    ticker = "688256"
    date = "2025-10-29"
    
    print(f"📊 测试股票: {ticker}")
    print(f"📅 测试日期: {date}")
    print()
    
    try:
        from tradingagents.dataflows.sentiment_data_sources import CoreSentimentDataSource
        
        print("1. 创建核心数据源...")
        core_source = CoreSentimentDataSource()
        print("   ✅ 核心数据源创建成功")
        print()
        
        print("2. 获取核心情绪数据...")
        core_data = core_source.get_data(ticker, date)
        print("   ✅ 核心数据获取成功")
        print()
        
        print("3. 核心数据内容:")
        print(f"   新闻情绪: {core_data.get('news_sentiment', 0.0):.3f}")
        print(f"   价格动量: {core_data.get('price_momentum', 0.0):.3f}")
        print(f"   成交量情绪: {core_data.get('volume_sentiment', 0.0):.3f}")
        print()
        
        # 检查是否所有值都是0
        if (core_data.get('price_momentum', 0.0) == 0.0 and 
            core_data.get('volume_sentiment', 0.0) == 0.0):
            print("⚠️  警告: 价格动量和成交量情绪都是0，可能存在问题")
        else:
            print("✅ 数据正常，至少有一个非零值")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_core_sentiment()
