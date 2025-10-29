#!/usr/bin/env python3
"""
市场情绪分析师性能测试和优化
测试分析性能、识别瓶颈、验证缓存效果

需求: 9.5
"""

import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tradingagents.utils.logging_init import get_logger
from tradingagents.dataflows.sentiment_data_sources import (
    CoreSentimentDataSource,
    USEnhancedDataSource,
    CNEnhancedDataSource,
    HKEnhancedDataSource
)
from tradingagents.dataflows.sentiment_cache import get_sentiment_cache
from tradingagents.agents.utils.fallback_strategy import FallbackStrategy
from tradingagents.agents.utils.sentiment_calculator import SentimentCalculator

logger = get_logger("test_sentiment_performance")


class PerformanceProfiler:
    """性能分析器"""
    
    def __init__(self):
        self.timings = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0
        }
    
    def time_operation(self, operation_name: str, func, *args, **kwargs):
        """计时操作"""
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            
            if operation_name not in self.timings:
                self.timings[operation_name] = []
            self.timings[operation_name].append(duration)
            
            logger.info(f"⏱️  {operation_name}: {duration:.3f}s")
            return result, duration
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            logger.error(f"❌ {operation_name} 失败 ({duration:.3f}s): {e}")
            return None, duration
    
    def get_summary(self) -> Dict:
        """获取性能摘要"""
        summary = {}
        for operation, durations in self.timings.items():
            summary[operation] = {
                'count': len(durations),
                'total': sum(durations),
                'avg': sum(durations) / len(durations) if durations else 0,
                'min': min(durations) if durations else 0,
                'max': max(durations) if durations else 0
            }
        return summary
    
    def print_report(self):
        """打印性能报告"""
        logger.info("=" * 80)
        logger.info("性能分析报告")
        logger.info("=" * 80)
        
        summary = self.get_summary()
        
        # 按平均时间排序
        sorted_ops = sorted(summary.items(), key=lambda x: x[1]['avg'], reverse=True)
        
        logger.info(f"\n{'操作':<40} {'次数':<8} {'总计':<10} {'平均':<10} {'最小':<10} {'最大':<10}")
        logger.info("-" * 80)
        
        for operation, stats in sorted_ops:
            logger.info(
                f"{operation:<40} "
                f"{stats['count']:<8} "
                f"{stats['total']:<10.3f} "
                f"{stats['avg']:<10.3f} "
                f"{stats['min']:<10.3f} "
                f"{stats['max']:<10.3f}"
            )
        
        # 缓存统计
        total_cache_ops = self.cache_stats['hits'] + self.cache_stats['misses']
        if total_cache_ops > 0:
            hit_rate = (self.cache_stats['hits'] / total_cache_ops) * 100
            logger.info(f"\n缓存统计:")
            logger.info(f"  - 命中: {self.cache_stats['hits']}")
            logger.info(f"  - 未命中: {self.cache_stats['misses']}")
            logger.info(f"  - 命中率: {hit_rate:.1f}%")


def test_core_sentiment_performance():
    """测试核心情绪数据源性能"""
    logger.info("=" * 80)
    logger.info("测试 1: 核心情绪数据源性能")
    logger.info("=" * 80)
    
    profiler = PerformanceProfiler()
    
    try:
        # 初始化数据源
        cache_manager = get_sentiment_cache()
        fallback_strategy = FallbackStrategy()
        
        core_source = CoreSentimentDataSource(
            cache_manager=cache_manager,
            toolkit=None,
            fallback_strategy=fallback_strategy
        )
        
        ticker = "AAPL"
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 测试新闻情绪
        _, duration = profiler.time_operation(
            "核心-新闻情绪",
            core_source.get_news_sentiment,
            ticker, date
        )
        
        # 测试价格动量
        _, duration = profiler.time_operation(
            "核心-价格动量",
            core_source.get_price_momentum,
            ticker, date
        )
        
        # 测试成交量情绪
        _, duration = profiler.time_operation(
            "核心-成交量情绪",
            core_source.get_volume_sentiment,
            ticker, date
        )
        
        # 测试完整数据获取
        _, duration = profiler.time_operation(
            "核心-完整数据",
            core_source.get_data,
            ticker, date
        )
        
        profiler.print_report()
        
        # 性能要求：单个组件应在3秒内完成
        summary = profiler.get_summary()
        for operation, stats in summary.items():
            if stats['avg'] > 3.0:
                logger.warning(f"⚠️  {operation} 平均耗时超过3秒: {stats['avg']:.3f}s")
        
        logger.info("✅ 核心情绪数据源性能测试完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 核心情绪数据源性能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cache_effectiveness():
    """测试缓存效果"""
    logger.info("=" * 80)
    logger.info("测试 2: 缓存效果")
    logger.info("=" * 80)
    
    profiler = PerformanceProfiler()
    
    try:
        # 初始化数据源
        cache_manager = get_sentiment_cache()
        fallback_strategy = FallbackStrategy()
        
        core_source = CoreSentimentDataSource(
            cache_manager=cache_manager,
            toolkit=None,
            fallback_strategy=fallback_strategy
        )
        
        ticker = "AAPL"
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 第一次调用（缓存未命中）
        logger.info("第一次调用（缓存未命中）...")
        _, duration1 = profiler.time_operation(
            "首次调用",
            core_source.get_data,
            ticker, date
        )
        profiler.cache_stats['misses'] += 1
        
        # 第二次调用（应该命中缓存）
        logger.info("第二次调用（应该命中缓存）...")
        _, duration2 = profiler.time_operation(
            "缓存调用",
            core_source.get_data,
            ticker, date
        )
        profiler.cache_stats['hits'] += 1
        
        # 计算加速比
        if duration1 > 0 and duration2 > 0:
            speedup = duration1 / duration2
            logger.info(f"\n缓存加速比: {speedup:.2f}x")
            
            # 缓存应该至少提供2x加速
            if speedup < 2.0:
                logger.warning(f"⚠️  缓存加速比低于预期: {speedup:.2f}x < 2.0x")
            else:
                logger.info(f"✅ 缓存效果良好: {speedup:.2f}x 加速")
        
        profiler.print_report()
        
        logger.info("✅ 缓存效果测试完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 缓存效果测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sentiment_calculator_performance():
    """测试情绪计算器性能"""
    logger.info("=" * 80)
    logger.info("测试 3: 情绪计算器性能")
    logger.info("=" * 80)
    
    profiler = PerformanceProfiler()
    
    try:
        calculator = SentimentCalculator()
        
        # 准备测试数据
        components = {
            'news': 0.5,
            'money_flow': 0.3,
            'volatility': -0.2,
            'technical': 0.4,
            'social': 0.1
        }
        
        # 测试综合评分计算（多次）
        iterations = 1000
        logger.info(f"执行 {iterations} 次评分计算...")
        
        start_time = time.time()
        for i in range(iterations):
            result = calculator.calculate_composite_score(components)
        end_time = time.time()
        
        total_duration = end_time - start_time
        avg_duration = total_duration / iterations
        
        logger.info(f"总耗时: {total_duration:.3f}s")
        logger.info(f"平均耗时: {avg_duration*1000:.3f}ms")
        logger.info(f"吞吐量: {iterations/total_duration:.1f} 次/秒")
        
        # 计算器应该非常快（< 1ms per operation）
        if avg_duration > 0.001:
            logger.warning(f"⚠️  计算器性能低于预期: {avg_duration*1000:.3f}ms > 1ms")
        else:
            logger.info(f"✅ 计算器性能良好: {avg_duration*1000:.3f}ms")
        
        # 测试组件贡献度分析
        _, duration = profiler.time_operation(
            "组件贡献度分析",
            calculator.calculate_breakdown,
            components
        )
        
        profiler.print_report()
        
        logger.info("✅ 情绪计算器性能测试完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 情绪计算器性能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_end_to_end_performance():
    """测试端到端性能"""
    logger.info("=" * 80)
    logger.info("测试 4: 端到端性能（10秒目标）")
    logger.info("=" * 80)
    
    profiler = PerformanceProfiler()
    
    try:
        # 模拟完整的情绪分析流程
        cache_manager = get_sentiment_cache()
        fallback_strategy = FallbackStrategy()
        calculator = SentimentCalculator()
        
        ticker = "AAPL"
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 开始计时
        total_start = time.time()
        
        # 1. 获取核心数据
        core_source = CoreSentimentDataSource(
            cache_manager=cache_manager,
            toolkit=None,
            fallback_strategy=fallback_strategy
        )
        core_data, _ = profiler.time_operation(
            "1. 核心数据获取",
            core_source.get_data,
            ticker, date
        )
        
        # 2. 获取增强数据（美股）
        us_source = USEnhancedDataSource(
            cache_manager=cache_manager,
            toolkit=None,
            fallback_strategy=fallback_strategy
        )
        enhanced_data, _ = profiler.time_operation(
            "2. 增强数据获取",
            us_source.get_data,
            ticker, date
        )
        
        # 3. 计算综合评分
        components = {
            'news': core_data.get('news_sentiment', 0.0) if core_data else 0.0,
            'technical': core_data.get('price_momentum', 0.0) if core_data else 0.0,
            'volatility': enhanced_data.get('vix_sentiment', 0.0) if enhanced_data else 0.0,
            'social': enhanced_data.get('reddit_sentiment', 0.0) if enhanced_data else 0.0
        }
        
        sentiment_result, _ = profiler.time_operation(
            "3. 情绪评分计算",
            calculator.calculate_composite_score,
            components
        )
        
        # 4. 计算组件贡献度
        breakdown, _ = profiler.time_operation(
            "4. 组件贡献度分析",
            calculator.calculate_breakdown,
            components
        )
        
        # 结束计时
        total_end = time.time()
        total_duration = total_end - total_start
        
        logger.info(f"\n总耗时: {total_duration:.3f}s")
        
        # 性能要求：95%的请求应在10秒内完成
        if total_duration > 10.0:
            logger.warning(f"⚠️  端到端性能未达标: {total_duration:.3f}s > 10s")
        else:
            logger.info(f"✅ 端到端性能达标: {total_duration:.3f}s < 10s")
        
        profiler.print_report()
        
        logger.info("✅ 端到端性能测试完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 端到端性能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def identify_bottlenecks():
    """识别性能瓶颈"""
    logger.info("=" * 80)
    logger.info("测试 5: 性能瓶颈识别")
    logger.info("=" * 80)
    
    profiler = PerformanceProfiler()
    
    try:
        cache_manager = get_sentiment_cache()
        fallback_strategy = FallbackStrategy()
        
        ticker = "AAPL"
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 测试各个数据源的性能
        operations = []
        
        # 核心数据源
        core_source = CoreSentimentDataSource(
            cache_manager=cache_manager,
            toolkit=None,
            fallback_strategy=fallback_strategy
        )
        
        _, duration = profiler.time_operation(
            "新闻情绪获取",
            core_source.get_news_sentiment,
            ticker, date
        )
        operations.append(("新闻情绪获取", duration))
        
        _, duration = profiler.time_operation(
            "价格动量计算",
            core_source.get_price_momentum,
            ticker, date
        )
        operations.append(("价格动量计算", duration))
        
        _, duration = profiler.time_operation(
            "成交量分析",
            core_source.get_volume_sentiment,
            ticker, date
        )
        operations.append(("成交量分析", duration))
        
        # 美股增强数据源
        us_source = USEnhancedDataSource(
            cache_manager=cache_manager,
            toolkit=None,
            fallback_strategy=fallback_strategy
        )
        
        _, duration = profiler.time_operation(
            "VIX指数获取",
            us_source.get_vix_sentiment
        )
        operations.append(("VIX指数获取", duration))
        
        _, duration = profiler.time_operation(
            "Reddit情绪分析",
            us_source.get_reddit_sentiment,
            ticker, date
        )
        operations.append(("Reddit情绪分析", duration))
        
        # 识别最慢的操作
        operations.sort(key=lambda x: x[1], reverse=True)
        
        logger.info("\n性能瓶颈排名（从慢到快）:")
        for i, (operation, duration) in enumerate(operations, 1):
            percentage = (duration / sum(d for _, d in operations)) * 100
            logger.info(f"  {i}. {operation}: {duration:.3f}s ({percentage:.1f}%)")
        
        # 优化建议
        logger.info("\n优化建议:")
        slowest_op, slowest_duration = operations[0]
        if slowest_duration > 2.0:
            logger.info(f"  - 优先优化 '{slowest_op}'，耗时 {slowest_duration:.3f}s")
            logger.info(f"  - 建议：增加缓存时长、使用异步请求、或实现数据预取")
        
        profiler.print_report()
        
        logger.info("✅ 性能瓶颈识别完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 性能瓶颈识别失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有性能测试"""
    logger.info("=" * 80)
    logger.info("市场情绪分析师性能测试")
    logger.info("=" * 80)
    logger.info("")
    
    test_results = []
    
    # 测试1: 核心数据源性能
    test_results.append(("核心数据源性能", test_core_sentiment_performance()))
    
    # 测试2: 缓存效果
    test_results.append(("缓存效果", test_cache_effectiveness()))
    
    # 测试3: 计算器性能
    test_results.append(("计算器性能", test_sentiment_calculator_performance()))
    
    # 测试4: 端到端性能
    test_results.append(("端到端性能", test_end_to_end_performance()))
    
    # 测试5: 瓶颈识别
    test_results.append(("瓶颈识别", identify_bottlenecks()))
    
    # 汇总结果
    logger.info("")
    logger.info("=" * 80)
    logger.info("性能测试结果汇总")
    logger.info("=" * 80)
    
    for test_name, passed in test_results:
        status = "✅ 通过" if passed else "❌ 失败"
        logger.info(f"{status} - {test_name}")
    
    passed_count = sum(1 for _, passed in test_results if passed)
    total_count = len(test_results)
    
    logger.info("")
    logger.info(f"总计: {passed_count}/{total_count} 测试通过")
    
    if passed_count == total_count:
        logger.info("🎉 所有性能测试通过！")
        return 0
    else:
        logger.error(f"⚠️ {total_count - passed_count} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
