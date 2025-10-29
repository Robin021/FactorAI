#!/usr/bin/env python3
"""测试完整的情绪分析流程"""

import sys
from datetime import datetime

# 测试情绪工具
def test_sentiment_tool():
    """测试情绪分析工具"""
    print("=" * 80)
    print("测试情绪分析工具")
    print("=" * 80)
    
    try:
        from tradingagents.tools.sentiment_tools import create_sentiment_analysis_tool
        from tradingagents.utils.stock_utils import StockUtils
        
        # 获取市场信息
        ticker = "688256"
        market_info = StockUtils.get_market_info(ticker)
        print(f"✅ 市场信息: {market_info['market_name']}")
        
        # 创建情绪工具
        sentiment_tool = create_sentiment_analysis_tool(toolkit=None, market_info=market_info)
        print(f"✅ 情绪工具创建成功: {sentiment_tool.name}")
        
        # 调用工具
        print(f"\n调用情绪工具获取 {ticker} 的市场情绪...")
        result = sentiment_tool.invoke({
            'ticker': ticker,
            'date': '2025-10-29',
            'market_type': market_info['market_name']
        })
        
        print(f"\n✅ 工具调用成功")
        print(f"结果长度: {len(result)} 字符")
        print(f"\n结果预览 (前500字符):")
        print("-" * 80)
        print(result[:500])
        print("-" * 80)
        
        # 检查结果是否包含关键信息
        if "综合情绪评分" in result:
            print("✅ 包含综合情绪评分")
        else:
            print("⚠️ 缺少综合情绪评分")
            
        if "情绪等级" in result:
            print("✅ 包含情绪等级")
        else:
            print("⚠️ 缺少情绪等级")
            
        if "情绪组件分析" in result:
            print("✅ 包含情绪组件分析")
        else:
            print("⚠️ 缺少情绪组件分析")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_sources():
    """测试数据源"""
    print("\n" + "=" * 80)
    print("测试数据源")
    print("=" * 80)
    
    try:
        from tradingagents.dataflows.sentiment_data_sources import CoreSentimentDataSource
        from tradingagents.dataflows.sentiment_cache import get_sentiment_cache
        from tradingagents.agents.utils.fallback_strategy import FallbackStrategy
        
        # 初始化
        cache = get_sentiment_cache()
        fallback = FallbackStrategy()
        source = CoreSentimentDataSource(
            cache_manager=cache,
            toolkit=None,
            fallback_strategy=fallback
        )
        
        print(f"✅ 数据源初始化成功")
        
        # 测试获取数据
        ticker = "688256"
        date = "2025-10-29"
        print(f"\n获取 {ticker} 的核心情绪数据...")
        
        data = source.get_data(ticker, date)
        
        print(f"✅ 数据获取成功")
        print(f"数据内容: {data}")
        
        # 检查数据结构
        required_keys = ['news_sentiment', 'price_momentum', 'volume_sentiment', 'timestamp']
        for key in required_keys:
            if key in data:
                print(f"✅ 包含 {key}: {data[key]}")
            else:
                print(f"⚠️ 缺少 {key}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("完整情绪分析流程测试")
    print("=" * 80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    results = []
    
    # 测试数据源
    results.append(("数据源测试", test_data_sources()))
    
    # 测试情绪工具
    results.append(("情绪工具测试", test_sentiment_tool()))
    
    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    print("=" * 80)
    print(f"总计: {passed}/{total} 通过")
    print("=" * 80)
    
    sys.exit(0 if passed == total else 1)
