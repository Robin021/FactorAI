#!/usr/bin/env python3
"""
集成测试：情绪缓存管理器与数据源集成
验证缓存管理器与情绪数据源的集成
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tradingagents.dataflows.sentiment_cache import SentimentCacheManager


def test_cache_with_data_source_pattern():
    """测试缓存管理器与数据源集成模式"""
    print("测试: 缓存管理器与数据源集成")
    
    # 初始化缓存
    cache = SentimentCacheManager(cache_backend='file')
    
    # 模拟数据源使用缓存的模式
    ticker = 'AAPL'
    date = datetime.now().strftime("%Y-%m-%d")
    
    # 1. 第一次获取（缓存未命中）
    print("\n1. 第一次获取数据（模拟API调用）")
    cached_data = cache.get(ticker, 'news', date=date)
    
    if cached_data is None:
        print("  ✅ 缓存未命中，需要从API获取")
        
        # 模拟从API获取数据
        api_data = {
            'score': 0.65,
            'articles': 10,
            'positive': 7,
            'negative': 3,
            'timestamp': datetime.now().isoformat()
        }
        
        # 存入缓存
        cache.set(ticker, 'news', api_data, date=date)
        print(f"  ✅ 数据已缓存: {api_data}")
    
    # 2. 第二次获取（缓存命中）
    print("\n2. 第二次获取数据（应该命中缓存）")
    cached_data = cache.get(ticker, 'news', date=date)
    
    if cached_data is not None:
        print(f"  ✅ 缓存命中: {cached_data}")
    else:
        print("  ❌ 缓存应该命中但未命中")
        return False
    
    # 3. 验证缓存统计
    print("\n3. 验证缓存统计")
    stats = cache.get_stats()
    print(f"  命中: {stats['hits']}, 未命中: {stats['misses']}")
    print(f"  命中率: {stats['hit_rate']}")
    
    assert stats['hits'] >= 1, "应该有至少1次命中"
    assert stats['misses'] >= 1, "应该有至少1次未命中"
    
    print("\n✅ 集成测试通过")
    return True


def test_multiple_data_types():
    """测试多种数据类型的缓存"""
    print("\n测试: 多种数据类型缓存")
    
    cache = SentimentCacheManager(cache_backend='file')
    date = datetime.now().strftime("%Y-%m-%d")
    
    # 测试不同市场和数据类型
    test_cases = [
        ('AAPL', 'vix', {'value': 18.5, 'level': 'normal'}),
        ('AAPL', 'news', {'score': 0.65, 'articles': 10}),
        ('AAPL', 'reddit', {'score': 0.75, 'mentions': 150}),
        ('600519', 'northbound', {'net_flow': 1500000000, 'sentiment': 0.6}),
        ('600519', 'margin', {'margin_balance': 5000000000, 'change_pct': 2.5}),
        ('00700', 'southbound', {'net_flow': 800000000, 'sentiment': 0.4}),
    ]
    
    print("\n设置缓存:")
    for ticker, data_type, data in test_cases:
        success = cache.set(ticker, data_type, data, date=date)
        status = "✅" if success else "❌"
        print(f"  {status} {ticker} - {data_type}")
    
    print("\n获取缓存:")
    for ticker, data_type, expected_data in test_cases:
        cached = cache.get(ticker, data_type, date=date)
        if cached is not None:
            print(f"  ✅ {ticker} - {data_type}: 命中")
        else:
            print(f"  ❌ {ticker} - {data_type}: 未命中")
            return False
    
    print("\n✅ 多数据类型测试通过")
    return True


def test_cache_invalidation():
    """测试缓存失效"""
    print("\n测试: 缓存失效")
    
    cache = SentimentCacheManager(cache_backend='file')
    date = datetime.now().strftime("%Y-%m-%d")
    
    # 设置一些缓存
    cache.set('AAPL', 'vix', {'value': 18.5}, date=date)
    cache.set('AAPL', 'news', {'score': 0.65}, date=date)
    cache.set('TSLA', 'vix', {'value': 20.0}, date=date)
    
    # 验证缓存存在
    assert cache.get('AAPL', 'vix', date=date) is not None
    assert cache.get('AAPL', 'news', date=date) is not None
    assert cache.get('TSLA', 'vix', date=date) is not None
    print("  ✅ 缓存已设置")
    
    # 失效AAPL的所有缓存
    deleted = cache.invalidate('sentiment:AAPL:*')
    print(f"  ✅ 失效了 {deleted} 个AAPL缓存")
    
    # 验证AAPL缓存已失效
    assert cache.get('AAPL', 'vix', date=date) is None
    assert cache.get('AAPL', 'news', date=date) is None
    print("  ✅ AAPL缓存已失效")
    
    # 验证TSLA缓存仍然存在
    assert cache.get('TSLA', 'vix', date=date) is not None
    print("  ✅ TSLA缓存仍然有效")
    
    print("\n✅ 缓存失效测试通过")
    return True


def test_ttl_configuration():
    """测试TTL配置"""
    print("\n测试: TTL配置")
    
    cache = SentimentCacheManager(cache_backend='file')
    
    # 验证不同数据类型有不同的TTL
    ttl_configs = [
        ('vix', 300, '5分钟'),
        ('news', 1800, '30分钟'),
        ('northbound', 3600, '1小时'),
        ('composite', 300, '5分钟'),
    ]
    
    print("\nTTL配置:")
    for data_type, expected_ttl, description in ttl_configs:
        actual_ttl = cache.CACHE_DURATION.get(data_type)
        status = "✅" if actual_ttl == expected_ttl else "❌"
        print(f"  {status} {data_type}: {actual_ttl}秒 ({description})")
        assert actual_ttl == expected_ttl, f"{data_type} TTL配置错误"
    
    print("\n✅ TTL配置测试通过")
    return True


def main():
    """运行所有集成测试"""
    print("=" * 60)
    print("情绪缓存管理器集成测试")
    print("=" * 60)
    
    try:
        test_cache_with_data_source_pattern()
        test_multiple_data_types()
        test_cache_invalidation()
        test_ttl_configuration()
        
        print("\n" + "=" * 60)
        print("✅ 所有集成测试通过！")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
