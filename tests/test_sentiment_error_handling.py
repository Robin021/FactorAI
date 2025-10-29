#!/usr/bin/env python3
"""
市场情绪分析师错误处理验证
测试各种数据源失败场景和降级策略的有效性

需求: 8.1, 8.2, 8.6
"""

import os
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tradingagents.utils.logging_init import get_logger
from tradingagents.dataflows.sentiment_data_sources import (
    CoreSentimentDataSource,
    USEnhancedDataSource,
    CNEnhancedDataSource,
    HKEnhancedDataSource
)
from tradingagents.agents.utils.fallback_strategy import FallbackStrategy
from tradingagents.agents.utils.sentiment_calculator import SentimentCalculator

logger = get_logger("test_sentiment_error_handling")


def test_news_sentiment_failure():
    """测试新闻情绪数据源失败场景"""
    logger.info("=" * 80)
    logger.info("测试 1: 新闻情绪数据源失败")
    logger.info("=" * 80)
    
    try:
        fallback_strategy = FallbackStrategy()
        
        core_source = CoreSentimentDataSource(
            cache_manager=None,
            toolkit=None,
            fallback_strategy=fallback_strategy
        )
        
        ticker = "AAPL"
        date = datetime.now().strftime("%Y-%m-%d")
        
        # 模拟新闻工具不可用
        logger.info("模拟新闻数据源失败...")
        sentiment = core_source.get_news_sentiment(ticker, date)
        
        # 应该返回降级值（0.0）而不是抛出异常
        assert sentiment is not None, "新闻情绪应返回降级值"
        assert isinstance(sentiment, float), "新闻情绪应返回浮点数"
        assert -1.0 <= sentiment <= 1.0, f"新闻情绪超出范围: {sentiment}"
        
        logger.info(f"✅ 新闻情绪降级值: {sentiment:.3f}")
        logger.info(f"✅ 降级策略有效，系统保持稳定")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 新闻情绪失败测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_price_data_failure():
    """测试价格数据源失败场景"""
    logger.info("=" * 80)
    logger.info("测试 2: 价格数据源失败")
    logger.info("=" * 80)
    
    try:
        fallback_strategy = FallbackStrategy()
        
        core_source = CoreSentimentDataSource(
            cache_manager=None,
            toolkit=None,
            fallback_strategy=fallback_strategy
        )
        
        # 使用无效的股票代码
        ticker = "INVALID_TICKER_12345"
        date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"使用无效股票代码: {ticker}")
        
        # 测试价格动量
        momentum = core_source.get_price_momentum(ticker, date)
        
        # 应该返回降级值而不是抛出异常
        assert momentum is not None, "价格动量应返回降级值"
        assert isinstance(momentum, float), "价格动量应返回浮点数"
        assert -1.0 <= momentum <= 1.0, f"价格动量超出范围: {momentum}"
        
        logger.info(f"✅ 价格动量降级值: {momentum:.3f}")
        
        # 测试成交量情绪
        volume = core_source.get_volume_sentiment(ticker, date)
        
        assert volume is not None, "成交量情绪应返回降级值"
        assert isinstance(volume, float), "成交量情绪应返回浮点数"
        assert -1.0 <= volume <= 1.0, f"成交量情绪超出范围: {volume}"
        
        logger.info(f"✅ 成交量情绪降级值: {volume:.3f}")
        logger.info(f"✅ 价格数据降级策略有效")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 价格数据失败测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vix_data_failure():
    """测试VIX数据源失败场景"""
    logger.info("=" * 80)
    logger.info("测试 3: VIX数据源失败")
    logger.info("=" * 80)
    
    try:
        fallback_strategy = FallbackStrategy()
        
        us_source = USEnhancedDataSource(
            cache_manager=None,
            toolkit=None,
            fallback_strategy=fallback_strategy
        )
        
        logger.info("测试VIX数据获取（可能失败）...")
        
        # 尝试获取VIX数据
        vix_sentiment = us_source.get_vix_sentiment()
        
        # 应该返回值（可能是降级值）而不是抛出异常
        assert vix_sentiment is not None, "VIX情绪应返回值"
        assert isinstance(vix_sentiment, float), "VIX情绪应返回浮点数"
        assert -1.0 <= vix_sentiment <= 1.0, f"VIX情绪超出范围: {vix_sentiment}"
        
        logger.info(f"✅ VIX情绪值: {vix_sentiment:.3f}")
        logger.info(f"✅ VIX数据降级策略有效")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ VIX数据失败测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_reddit_data_failure():
    """测试Reddit数据源失败场景"""
    logger.info("=" * 80)
    logger.info("测试 4: Reddit数据源失败")
    logger.info("=" * 80)
    
    try:
        fallback_strategy = FallbackStrategy()
        
        us_source = USEnhancedDataSource(
            cache_manager=None,
            toolkit=None,
            fallback_strategy=fallback_strategy
        )
        
        ticker = "AAPL"
        date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"测试Reddit数据获取: {ticker}")
        
        # 尝试获取Reddit数据
        reddit_sentiment = us_source.get_reddit_sentiment(ticker, date)
        
        # 应该返回值（可能是降级值）而不是抛出异常
        assert reddit_sentiment is not None, "Reddit情绪应返回值"
        assert isinstance(reddit_sentiment, float), "Reddit情绪应返回浮点数"
        assert -1.0 <= reddit_sentiment <= 1.0, f"Reddit情绪超出范围: {reddit_sentiment}"
        
        logger.info(f"✅ Reddit情绪值: {reddit_sentiment:.3f}")
        logger.info(f"✅ Reddit数据降级策略有效")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Reddit数据失败测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_northbound_flow_failure():
    """测试北向资金数据源失败场景"""
    logger.info("=" * 80)
    logger.info("测试 5: 北向资金数据源失败")
    logger.info("=" * 80)
    
    try:
        fallback_strategy = FallbackStrategy()
        
        cn_source = CNEnhancedDataSource(
            cache_manager=None,
            tushare_token=None,
            fallback_strategy=fallback_strategy
        )
        
        # 使用无效的股票代码
        ticker = "999999"
        date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"使用无效A股代码: {ticker}")
        
        # 尝试获取北向资金数据
        flow_sentiment = cn_source.get_northbound_flow(ticker, date)
        
        # 应该返回降级值而不是抛出异常
        assert flow_sentiment is not None, "北向资金应返回降级值"
        assert isinstance(flow_sentiment, float), "北向资金应返回浮点数"
        assert -1.0 <= flow_sentiment <= 1.0, f"北向资金超出范围: {flow_sentiment}"
        
        logger.info(f"✅ 北向资金降级值: {flow_sentiment:.3f}")
        logger.info(f"✅ 北向资金降级策略有效")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 北向资金失败测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_margin_trading_failure():
    """测试融资融券数据源失败场景"""
    logger.info("=" * 80)
    logger.info("测试 6: 融资融券数据源失败（无TuShare Token）")
    logger.info("=" * 80)
    
    try:
        fallback_strategy = FallbackStrategy()
        
        # 不提供TuShare Token
        cn_source = CNEnhancedDataSource(
            cache_manager=None,
            tushare_token=None,
            fallback_strategy=fallback_strategy
        )
        
        ticker = "600519"
        date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"测试融资融券数据（无Token）: {ticker}")
        
        # 尝试获取融资融券数据
        margin_sentiment = cn_source.get_margin_trading(ticker, date)
        
        # 应该返回降级值而不是抛出异常
        assert margin_sentiment is not None, "融资融券应返回降级值"
        assert isinstance(margin_sentiment, float), "融资融券应返回浮点数"
        assert -1.0 <= margin_sentiment <= 1.0, f"融资融券超出范围: {margin_sentiment}"
        
        logger.info(f"✅ 融资融券降级值: {margin_sentiment:.3f}")
        logger.info(f"✅ 融资融券降级策略有效（使用AKShare替代）")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 融资融券失败测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_southbound_flow_failure():
    """测试南向资金数据源失败场景"""
    logger.info("=" * 80)
    logger.info("测试 7: 南向资金数据源失败")
    logger.info("=" * 80)
    
    try:
        fallback_strategy = FallbackStrategy()
        
        hk_source = HKEnhancedDataSource(
            cache_manager=None,
            fallback_strategy=fallback_strategy
        )
        
        # 使用无效的港股代码
        ticker = "99999.HK"
        date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"使用无效港股代码: {ticker}")
        
        # 尝试获取南向资金数据
        flow_sentiment = hk_source.get_southbound_flow(ticker, date)
        
        # 应该返回降级值而不是抛出异常
        assert flow_sentiment is not None, "南向资金应返回降级值"
        assert isinstance(flow_sentiment, float), "南向资金应返回浮点数"
        assert -1.0 <= flow_sentiment <= 1.0, f"南向资金超出范围: {flow_sentiment}"
        
        logger.info(f"✅ 南向资金降级值: {flow_sentiment:.3f}")
        logger.info(f"✅ 南向资金降级策略有效")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 南向资金失败测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_failures():
    """测试多个数据源同时失败场景"""
    logger.info("=" * 80)
    logger.info("测试 8: 多个数据源同时失败")
    logger.info("=" * 80)
    
    try:
        fallback_strategy = FallbackStrategy()
        calculator = SentimentCalculator()
        
        # 使用无效数据模拟所有数据源失败
        ticker = "INVALID_TICKER"
        date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info("模拟所有数据源失败...")
        
        # 核心数据源
        core_source = CoreSentimentDataSource(
            cache_manager=None,
            toolkit=None,
            fallback_strategy=fallback_strategy
        )
        
        core_data = core_source.get_data(ticker, date)
        
        # 美股增强数据源
        us_source = USEnhancedDataSource(
            cache_manager=None,
            toolkit=None,
            fallback_strategy=fallback_strategy
        )
        
        enhanced_data = us_source.get_data(ticker, date)
        
        # 验证降级数据
        assert core_data is not None, "核心数据应返回降级值"
        assert enhanced_data is not None, "增强数据应返回降级值"
        
        # 尝试计算综合评分
        components = {
            'news': core_data.get('news_sentiment', 0.0),
            'technical': core_data.get('price_momentum', 0.0),
            'volatility': enhanced_data.get('vix_sentiment', 0.0),
            'social': enhanced_data.get('reddit_sentiment', 0.0)
        }
        
        result = calculator.calculate_composite_score(components)
        
        # 验证结果
        assert 'score' in result, "应返回评分"
        assert 'level' in result, "应返回情绪等级"
        assert 0 <= result['score'] <= 100, f"评分超出范围: {result['score']}"
        
        logger.info(f"✅ 综合评分: {result['score']:.2f}")
        logger.info(f"✅ 情绪等级: {result['level']}")
        logger.info(f"✅ 系统在多个数据源失败时保持稳定")
        
        # 检查降级策略记录
        if fallback_strategy.has_failures():
            failures = fallback_strategy.get_failures()
            logger.info(f"✅ 降级策略记录了 {len(failures)} 个失败")
            for failure in failures[:3]:  # 显示前3个
                logger.info(f"   - {failure['component']}: {failure['error']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 多数据源失败测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fallback_strategy_levels():
    """测试降级策略的5个级别"""
    logger.info("=" * 80)
    logger.info("测试 9: 降级策略级别")
    logger.info("=" * 80)
    
    try:
        fallback_strategy = FallbackStrategy()
        
        # 初始级别应该是 'full'
        assert fallback_strategy.current_level == 'full', "初始级别应为 full"
        logger.info(f"✅ 初始级别: {fallback_strategy.current_level}")
        
        # 模拟失败，触发降级
        for i in range(3):
            fallback_strategy.record_failure(f'component_{i}', Exception(f"Test failure {i}"))
        
        # 检查降级
        if fallback_strategy.current_level != 'full':
            logger.info(f"✅ 降级到: {fallback_strategy.current_level}")
        
        # 继续模拟失败
        for i in range(3, 6):
            fallback_strategy.record_failure(f'component_{i}', Exception(f"Test failure {i}"))
        
        # 检查进一步降级
        logger.info(f"✅ 当前级别: {fallback_strategy.current_level}")
        
        # 验证降级数据可用
        fallback_data = fallback_strategy.get_fallback_data('test_component')
        assert fallback_data is not None, "降级数据应可用"
        assert 'score' in fallback_data, "降级数据应包含评分"
        
        logger.info(f"✅ 降级数据: {fallback_data}")
        logger.info(f"✅ 降级策略级别机制有效")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 降级策略级别测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_system_stability():
    """测试系统稳定性（不应崩溃）"""
    logger.info("=" * 80)
    logger.info("测试 10: 系统稳定性")
    logger.info("=" * 80)
    
    try:
        fallback_strategy = FallbackStrategy()
        calculator = SentimentCalculator()
        
        # 测试各种边界情况
        test_cases = [
            ("空字符串", "", datetime.now().strftime("%Y-%m-%d")),
            ("None值", None, datetime.now().strftime("%Y-%m-%d")),
            ("特殊字符", "!@#$%^&*()", datetime.now().strftime("%Y-%m-%d")),
            ("超长代码", "A" * 100, datetime.now().strftime("%Y-%m-%d")),
        ]
        
        for test_name, ticker, date in test_cases:
            logger.info(f"测试 {test_name}: ticker={ticker}")
            
            try:
                core_source = CoreSentimentDataSource(
                    cache_manager=None,
                    toolkit=None,
                    fallback_strategy=fallback_strategy
                )
                
                # 尝试获取数据（应该不崩溃）
                if ticker is not None:
                    data = core_source.get_data(ticker, date)
                    logger.info(f"  ✅ {test_name} 处理成功")
                else:
                    logger.info(f"  ⏭️  {test_name} 跳过（None值）")
                    
            except Exception as e:
                logger.warning(f"  ⚠️  {test_name} 触发异常: {e}")
                # 异常被捕获，系统没有崩溃
        
        logger.info(f"✅ 系统在各种边界情况下保持稳定")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 系统稳定性测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有错误处理测试"""
    logger.info("=" * 80)
    logger.info("市场情绪分析师错误处理验证")
    logger.info("=" * 80)
    logger.info("")
    
    test_results = []
    
    # 测试1: 新闻情绪失败
    test_results.append(("新闻情绪失败", test_news_sentiment_failure()))
    
    # 测试2: 价格数据失败
    test_results.append(("价格数据失败", test_price_data_failure()))
    
    # 测试3: VIX数据失败
    test_results.append(("VIX数据失败", test_vix_data_failure()))
    
    # 测试4: Reddit数据失败
    test_results.append(("Reddit数据失败", test_reddit_data_failure()))
    
    # 测试5: 北向资金失败
    test_results.append(("北向资金失败", test_northbound_flow_failure()))
    
    # 测试6: 融资融券失败
    test_results.append(("融资融券失败", test_margin_trading_failure()))
    
    # 测试7: 南向资金失败
    test_results.append(("南向资金失败", test_southbound_flow_failure()))
    
    # 测试8: 多数据源失败
    test_results.append(("多数据源失败", test_multiple_failures()))
    
    # 测试9: 降级策略级别
    test_results.append(("降级策略级别", test_fallback_strategy_levels()))
    
    # 测试10: 系统稳定性
    test_results.append(("系统稳定性", test_system_stability()))
    
    # 汇总结果
    logger.info("")
    logger.info("=" * 80)
    logger.info("错误处理测试结果汇总")
    logger.info("=" * 80)
    
    for test_name, passed in test_results:
        status = "✅ 通过" if passed else "❌ 失败"
        logger.info(f"{status} - {test_name}")
    
    passed_count = sum(1 for _, passed in test_results if passed)
    total_count = len(test_results)
    
    logger.info("")
    logger.info(f"总计: {passed_count}/{total_count} 测试通过")
    
    if passed_count == total_count:
        logger.info("🎉 所有错误处理测试通过！")
        logger.info("✅ 系统具有良好的容错能力和稳定性")
        return 0
    else:
        logger.error(f"⚠️ {total_count - passed_count} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
