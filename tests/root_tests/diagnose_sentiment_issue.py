#!/usr/bin/env python3
"""
诊断情绪分析数据问题
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def diagnose_sentiment_data():
    """诊断情绪数据获取问题"""
    
    print("=" * 80)
    print("情绪分析数据诊断工具")
    print("=" * 80)
    print()
    
    ticker = "688256"
    date = "2025-10-29"
    
    print(f"📊 测试股票: {ticker}")
    print(f"📅 测试日期: {date}")
    print()
    
    # 1. 测试价格数据获取
    print("=" * 80)
    print("1. 测试价格数据获取")
    print("=" * 80)
    
    try:
        from tradingagents.dataflows.interface import get_stock_data_by_market
        from datetime import datetime, timedelta
        
        end_date = datetime.strptime(date, "%Y-%m-%d")
        start_date = end_date - timedelta(days=30)
        
        price_data = get_stock_data_by_market(
            symbol=ticker,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=date
        )
        
        print(f"✅ 价格数据获取成功")
        print(f"📝 数据类型: {type(price_data)}")
        print(f"📏 数据长度: {len(str(price_data))} 字符")
        print(f"📄 数据预览:")
        print(str(price_data)[:500])
        print()
        
        # 尝试解析涨跌幅
        import re
        change_match = re.search(r'涨跌幅[：:]\s*([-+]?\d+\.?\d*)%', str(price_data))
        if change_match:
            change_pct = float(change_match.group(1))
            print(f"✅ 涨跌幅解析成功: {change_pct}%")
        else:
            print(f"❌ 涨跌幅解析失败")
            print(f"   可能的原因: 数据格式不包含'涨跌幅'字段")
        
    except Exception as e:
        print(f"❌ 价格数据获取失败: {e}")
    
    print()
    
    # 2. 测试成交量数据获取
    print("=" * 80)
    print("2. 测试成交量数据获取")
    print("=" * 80)
    
    try:
        from tradingagents.dataflows.interface import get_stock_data_by_market
        from datetime import datetime, timedelta
        import re
        
        end_date = datetime.strptime(date, "%Y-%m-%d")
        start_date = end_date - timedelta(days=30)
        
        volume_data = get_stock_data_by_market(
            symbol=ticker,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=date
        )
        
        print(f"✅ 成交量数据获取成功")
        print(f"📝 数据类型: {type(volume_data)}")
        print(f"📏 数据长度: {len(str(volume_data))} 字符")
        
        # 尝试解析换手率
        turnover_match = re.search(r'换手率[：:]\s*(\d+\.?\d*)', str(volume_data))
        if turnover_match:
            turnover = float(turnover_match.group(1))
            print(f"✅ 换手率解析成功: {turnover}%")
        else:
            print(f"❌ 换手率解析失败")
            print(f"   可能的原因: 数据格式不包含'换手率'字段")
        
    except Exception as e:
        print(f"❌ 成交量数据获取失败: {e}")
    
    print()
    
    # 3. 测试北向资金数据
    print("=" * 80)
    print("3. 测试北向资金数据")
    print("=" * 80)
    
    try:
        import akshare as ak
        
        df = ak.stock_hsgt_individual_em(symbol=ticker)
        
        if df is not None and not df.empty:
            print(f"✅ 北向资金数据获取成功")
            print(f"📊 数据行数: {len(df)}")
            print(f"📋 数据列: {list(df.columns)}")
            
            if '净流入' in df.columns:
                recent_flow = df['净流入'].iloc[-1]
                print(f"✅ 最近净流入: {recent_flow/100000000:.2f} 亿元")
            else:
                print(f"❌ 数据中没有'净流入'列")
        else:
            print(f"❌ 北向资金数据为空")
            
    except Exception as e:
        print(f"❌ 北向资金数据获取失败: {e}")
        print(f"   可能的原因: 该股票不在沪深港通标的范围内")
    
    print()
    
    # 4. 测试融资融券数据
    print("=" * 80)
    print("4. 测试融资融券数据")
    print("=" * 80)
    
    try:
        # 检查是否有TuShare token
        import os
        tushare_token = os.getenv('TUSHARE_TOKEN')
        
        if not tushare_token:
            print(f"⚠️  未配置TUSHARE_TOKEN环境变量")
            print(f"   融资融券数据需要TuShare Pro权限")
        else:
            import tushare as ts
            pro = ts.pro_api(tushare_token)
            
            # 转换股票代码格式
            if ticker.startswith('6'):
                ts_code = f"{ticker}.SH"
            else:
                ts_code = f"{ticker}.SZ"
            
            df = pro.margin_detail(
                ts_code=ts_code,
                start_date=date.replace('-', ''),
                end_date=date.replace('-', '')
            )
            
            if df is not None and not df.empty:
                print(f"✅ 融资融券数据获取成功")
                print(f"📊 数据行数: {len(df)}")
                print(f"📋 数据列: {list(df.columns)}")
            else:
                print(f"❌ 融资融券数据为空")
                
    except Exception as e:
        print(f"❌ 融资融券数据获取失败: {e}")
    
    print()
    
    # 5. 测试新闻情绪
    print("=" * 80)
    print("5. 测试新闻情绪")
    print("=" * 80)
    
    try:
        from tradingagents.dataflows.interface import get_stock_news_unified
        
        news_data = get_stock_news_unified(ticker=ticker, curr_date=date)
        
        print(f"✅ 新闻数据获取成功")
        print(f"📝 数据类型: {type(news_data)}")
        print(f"📏 数据长度: {len(str(news_data))} 字符")
        print(f"📄 数据预览:")
        print(str(news_data)[:500])
        
        # 简单情绪分析
        positive_keywords = ['上涨', '增长', '盈利', '突破', '创新高', '利好']
        negative_keywords = ['下跌', '亏损', '下滑', '风险', '警告', '利空']
        
        positive_count = sum(1 for kw in positive_keywords if kw in str(news_data))
        negative_count = sum(1 for kw in negative_keywords if kw in str(news_data))
        
        print(f"📊 正面关键词数量: {positive_count}")
        print(f"📊 负面关键词数量: {negative_count}")
        
        if positive_count + negative_count > 0:
            score = (positive_count - negative_count) / (positive_count + negative_count)
            print(f"✅ 新闻情绪评分: {score:.3f}")
        else:
            print(f"⚠️  未检测到情绪关键词")
        
    except Exception as e:
        print(f"❌ 新闻数据获取失败: {e}")
    
    print()
    
    # 6. 总结
    print("=" * 80)
    print("诊断总结")
    print("=" * 80)
    print()
    print("根据以上测试结果，可能的问题包括：")
    print()
    print("1. 如果价格数据获取成功但解析失败：")
    print("   - 数据格式可能不包含'涨跌幅'或'换手率'字段")
    print("   - 需要调整正则表达式或数据解析逻辑")
    print()
    print("2. 如果北向资金数据获取失败：")
    print("   - 该股票可能不在沪深港通标的范围内")
    print("   - 科创板股票(688开头)可能不支持北向资金")
    print()
    print("3. 如果融资融券数据获取失败：")
    print("   - 需要配置TUSHARE_TOKEN环境变量")
    print("   - 需要TuShare Pro权限")
    print()
    print("4. 如果新闻情绪正常但其他数据都是0：")
    print("   - 说明只有新闻数据源正常工作")
    print("   - 其他数据源都触发了降级策略，返回0")
    print()
    print("建议解决方案：")
    print("- 检查数据源API的可用性")
    print("- 验证股票代码是否支持所有数据源")
    print("- 配置必要的API密钥（如TUSHARE_TOKEN）")
    print("- 调整数据解析逻辑以适应实际返回的数据格式")
    print()


if __name__ == "__main__":
    diagnose_sentiment_data()
