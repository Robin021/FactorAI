#!/usr/bin/env python3
"""
测试资金流向和融资融券数据获取
"""

import sys
sys.path.insert(0, '.')

from datetime import datetime
from tradingagents.dataflows.sentiment_data_sources import CNEnhancedDataSource
from tradingagents.dataflows.sentiment_cache import get_sentiment_cache
from tradingagents.agents.utils.fallback_strategy import FallbackStrategy

def test_capital_flow():
    """测试资金流向数据"""
    
    print("=" * 80)
    print("测试资金流向和融资融券数据")
    print("=" * 80)
    
    # 初始化数据源
    cache_manager = get_sentiment_cache()
    fallback_strategy = FallbackStrategy()
    
    cn_source = CNEnhancedDataSource(
        cache_manager=cache_manager,
        toolkit=None,
        tushare_token=None,  # 不使用 TuShare
        fallback_strategy=fallback_strategy
    )
    
    # 测试不同类型的股票
    test_cases = [
        {
            'ticker': '688256',
            'name': '寒武纪 (科创板)',
            'expected_northbound': 0.0,  # 科创板无北向资金
            'has_margin': True
        },
        {
            'ticker': '600519',
            'name': '贵州茅台 (主板)',
            'expected_northbound': 'non-zero',  # 应该有北向资金
            'has_margin': True
        },
        {
            'ticker': '300750',
            'name': '宁德时代 (创业板)',
            'expected_northbound': 'non-zero',  # 应该有北向资金
            'has_margin': True
        }
    ]
    
    date = datetime.now().strftime('%Y-%m-%d')
    
    for case in test_cases:
        ticker = case['ticker']
        name = case['name']
        
        print(f"\n{'='*80}")
        print(f"测试股票: {ticker} - {name}")
        print(f"{'='*80}")
        
        # 测试北向资金
        print(f"\n1. 北向资金测试")
        print("-" * 80)
        
        try:
            northbound = cn_source.get_northbound_flow(ticker, date)
            print(f"   北向资金评分: {northbound:.3f}")
            
            if case['expected_northbound'] == 0.0:
                if northbound == 0.0:
                    print(f"   ✅ 符合预期 (科创板无北向资金)")
                else:
                    print(f"   ⚠️  意外: 科创板不应该有北向资金")
            else:
                if northbound != 0.0:
                    print(f"   ✅ 获取到北向资金数据")
                else:
                    print(f"   ⚠️  可能不在沪深港通标的范围内")
                    
        except Exception as e:
            print(f"   ❌ 错误: {e}")
        
        # 测试融资融券
        print(f"\n2. 融资融券测试")
        print("-" * 80)
        
        try:
            margin = cn_source.get_margin_trading(ticker, date)
            print(f"   融资融券评分: {margin:.3f}")
            
            if margin != 0.0:
                print(f"   ✅ 获取到融资融券数据")
            else:
                print(f"   ⚠️  返回中性评分 (可能使用了市场整体数据)")
                
        except Exception as e:
            print(f"   ❌ 错误: {e}")
        
        # 测试波动率
        print(f"\n3. 波动率测试")
        print("-" * 80)
        
        try:
            volatility = cn_source.get_volatility_sentiment(ticker, date)
            print(f"   波动率评分: {volatility:.3f}")
            
            if volatility != 0.0:
                print(f"   ✅ 获取到波动率数据")
            else:
                print(f"   ⚠️  返回中性评分")
                
        except Exception as e:
            print(f"   ❌ 错误: {e}")
    
    print(f"\n{'='*80}")
    print("测试完成")
    print(f"{'='*80}")
    
    print("\n📝 说明:")
    print("1. 科创板股票 (688xxx) 没有北向资金是正常现象")
    print("2. 融资融券数据:")
    print("   - 如果配置了 TuShare Token，可以获取个股数据")
    print("   - 否则使用市场整体数据作为参考")
    print("3. 波动率基于股票的历史价格振幅计算")
    
    print("\n💡 改进建议:")
    print("1. 配置 TuShare Token 以获取个股融资融券数据")
    print("2. 对科创板股票使用不同的权重配置")
    print("3. 添加科创板特有的情绪指标")


def test_margin_fallback():
    """专门测试融资融券降级方案"""
    
    print("\n" + "=" * 80)
    print("测试融资融券降级方案")
    print("=" * 80)
    
    cache_manager = get_sentiment_cache()
    fallback_strategy = FallbackStrategy()
    
    cn_source = CNEnhancedDataSource(
        cache_manager=cache_manager,
        toolkit=None,
        tushare_token=None,  # 强制使用降级方案
        fallback_strategy=fallback_strategy
    )
    
    date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"\n测试日期: {date}")
    print("-" * 80)
    
    try:
        # 直接调用降级方案
        sentiment = cn_source._get_margin_trading_fallback(date)
        
        print(f"\n降级方案返回评分: {sentiment:.3f}")
        
        if sentiment != 0.0:
            print("✅ 降级方案成功获取市场整体数据")
            print("   (评分基于市场整体融资余额的变化)")
        else:
            print("⚠️  降级方案返回中性评分")
            print("   (可能是首次运行，没有历史数据对比)")
            
    except Exception as e:
        print(f"❌ 降级方案失败: {e}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    print("\n🔍 资金流向和融资融券数据测试\n")
    
    # 测试资金流向
    test_capital_flow()
    
    # 测试融资融券降级方案
    test_margin_fallback()
    
    print("\n✅ 所有测试完成")
