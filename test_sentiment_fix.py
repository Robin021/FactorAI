#!/usr/bin/env python3
"""
测试情绪分析修复
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_sentiment_fix():
    """测试情绪分析修复"""
    
    print("=" * 80)
    print("测试情绪分析修复")
    print("=" * 80)
    print()
    
    ticker = "688256"
    date = "2025-10-29"
    
    print(f"📊 测试股票: {ticker}")
    print(f"📅 测试日期: {date}")
    print()
    
    # 1. 测试核心数据源
    print("=" * 80)
    print("1. 测试核心情绪数据源")
    print("=" * 80)
    
    try:
        from tradingagents.dataflows.sentiment_data_sources import CoreSentimentDataSource
        from tradingagents.utils.stock_utils import StockUtils
        
        market_info = StockUtils.get_market_info(ticker)
        print(f"✅ 市场信息: {market_info['market_name']}")
        
        core_source = CoreSentimentDataSource()
        
        # 测试新闻情绪
        print("\n📰 测试新闻情绪...")
        news_sentiment = core_source.get_news_sentiment(ticker, date)
        print(f"   新闻情绪: {news_sentiment:.3f}")
        
        # 测试价格动量
        print("\n📈 测试价格动量...")
        price_momentum = core_source.get_price_momentum(ticker, date)
        print(f"   价格动量: {price_momentum:.3f}")
        
        # 测试成交量情绪
        print("\n📊 测试成交量情绪...")
        volume_sentiment = core_source.get_volume_sentiment(ticker, date)
        print(f"   成交量情绪: {volume_sentiment:.3f}")
        
        print()
        print("✅ 核心数据源测试完成")
        print(f"   新闻情绪: {news_sentiment:.3f}")
        print(f"   价格动量: {price_momentum:.3f}")
        print(f"   成交量情绪: {volume_sentiment:.3f}")
        
    except Exception as e:
        print(f"❌ 核心数据源测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # 2. 测试A股增强数据源
    print("=" * 80)
    print("2. 测试A股增强数据源")
    print("=" * 80)
    
    try:
        from tradingagents.dataflows.sentiment_data_sources import CNEnhancedDataSource
        
        cn_source = CNEnhancedDataSource()
        
        # 测试北向资金
        print("\n💰 测试北向资金...")
        northbound_flow = cn_source.get_northbound_flow(ticker, date)
        print(f"   北向资金: {northbound_flow:.3f}")
        
        # 测试波动率
        print("\n📉 测试波动率情绪...")
        volatility_sentiment = cn_source.get_volatility_sentiment(ticker, date)
        print(f"   波动率情绪: {volatility_sentiment:.3f}")
        
        print()
        print("✅ A股增强数据源测试完成")
        print(f"   北向资金: {northbound_flow:.3f}")
        print(f"   波动率情绪: {volatility_sentiment:.3f}")
        
    except Exception as e:
        print(f"❌ A股增强数据源测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # 3. 测试完整情绪分析
    print("=" * 80)
    print("3. 测试完整情绪分析")
    print("=" * 80)
    
    try:
        from tradingagents.tools.sentiment_tools import create_sentiment_analysis_tool
        from tradingagents.utils.stock_utils import StockUtils
        
        market_info = StockUtils.get_market_info(ticker)
        sentiment_tool = create_sentiment_analysis_tool(toolkit=None, market_info=market_info)
        
        print(f"✅ 情绪工具创建成功: {sentiment_tool.name}")
        print()
        print("🔧 调用情绪分析工具...")
        
        result = sentiment_tool.invoke({
            'ticker': ticker,
            'date': date,
            'market_type': market_info['market_name']
        })
        
        print()
        print("=" * 80)
        print("情绪分析结果")
        print("=" * 80)
        print(result)
        print()
        
        # 检查结果是否包含关键信息
        if "综合情绪评分" in result:
            print("✅ 包含综合情绪评分")
            
            # 提取评分
            import re
            score_match = re.search(r'综合情绪评分[：:]\s*(\d+\.?\d*)', result)
            if score_match:
                score = float(score_match.group(1))
                print(f"   评分: {score:.2f}")
                
                # 检查是否所有组件都是0
                if "技术动量" in result and "成交量" in result:
                    print("✅ 包含技术动量和成交量数据")
                else:
                    print("⚠️ 缺少技术动量或成交量数据")
        else:
            print("⚠️ 缺少综合情绪评分")
            
        if "情绪等级" in result:
            print("✅ 包含情绪等级")
        else:
            print("⚠️ 缺少情绪等级")
        
    except Exception as e:
        print(f"❌ 完整情绪分析测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    test_sentiment_fix()
