#!/usr/bin/env python3
"""
测试情绪分析功能
"""
import os
import sys
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.abspath('.'))

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

def test_sentiment_analysis():
    """测试情绪分析功能"""
    
    print("=" * 80)
    print("测试情绪分析功能")
    print("=" * 80)
    
    # 配置
    config = DEFAULT_CONFIG.copy()
    
    # 创建TradingAgentsGraph实例，包含market_sentiment分析师
    selected_analysts = ["market", "news", "fundamentals", "market_sentiment"]
    
    print(f"\n✅ 选择的分析师: {selected_analysts}")
    
    try:
        trading_graph = TradingAgentsGraph(
            selected_analysts=selected_analysts,
            debug=False,
            config=config
        )
        
        print("✅ TradingAgentsGraph 初始化成功")
        
        # 测试股票
        test_stocks = [
            ("AAPL", "2024-10-27"),  # 美股
            ("600519", "2024-10-27"),  # A股
            ("00700", "2024-10-27"),  # 港股
        ]
        
        for stock_code, trade_date in test_stocks:
            print(f"\n{'=' * 80}")
            print(f"测试股票: {stock_code} ({trade_date})")
            print(f"{'=' * 80}")
            
            try:
                # 运行分析
                final_state, signal = trading_graph.propagate(
                    company_name=stock_code,
                    trade_date=trade_date
                )
                
                # 检查结果
                if "market_sentiment_report" in final_state:
                    report = final_state["market_sentiment_report"]
                    score = final_state.get("sentiment_score", 0.0)
                    
                    print(f"\n✅ 情绪分析报告已生成")
                    print(f"   情绪评分: {score:.2f}")
                    print(f"   报告长度: {len(report)} 字符")
                    
                    # 显示报告摘要
                    if report:
                        lines = report.split('\n')
                        print(f"\n   报告摘要 (前10行):")
                        for i, line in enumerate(lines[:10]):
                            print(f"   {line}")
                        if len(lines) > 10:
                            print(f"   ... (共 {len(lines)} 行)")
                    else:
                        print(f"   ⚠️ 报告为空")
                else:
                    print(f"\n❌ 未找到 market_sentiment_report")
                    print(f"   可用的状态键: {list(final_state.keys())}")
                
            except Exception as e:
                print(f"\n❌ 分析失败: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n{'=' * 80}")
        print("测试完成")
        print(f"{'=' * 80}")
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sentiment_analysis()
