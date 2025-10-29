#!/usr/bin/env python3
"""
基础测试：情绪缓存管理器
验证核心功能是否正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tradingagents.dataflows.sentiment_cache import SentimentCacheManager, get_sentiment_cache


def test_cache_initialization():
    """测试缓存管理器初始化"""
    print("测试1: 缓存管理器初始化")
    cache = SentimentCacheManager(cache_backend='file')
    assert cache.backend == 'file', "缓存后端应为file"
    print("✅ 缓存管理器初始化成功")


def test_cache_key_generation():
    """测试缓存键生成"""
    print("\n测试2: 缓存键生成")
    cache = SentimentCacheManager(cache_backend='file')
    
    # 测试基本键生成
    key1 = cache._generate_cache_key('AAPL', 'vix', '2024-10-27')
    assert key1.startswith('sentiment:AAPL:vix:2024-10-27:'), f"键格式错误: {key1}"
    print(f"  生成的键: {key1}")
    
    # 测试相同参数生成相同键
    key2 = cache._generate_cache_key('AAPL', 'vix', '2024-10-27')
    assert key1 == key2, "相同参数应生成相同键"
    print(f"  相同参数生成相同键: ✅")
    
    # 测试不同参数生成不同键
    key3 = cache._generate_cache_key('AAPL', 'news', '2024-10-27')
    assert key1 != key3, "不同参数应生成不同键"
    print(f"  不同参数生成不同键: ✅")
    
    print("✅ 缓存键生成测试通过")


def test_cache_set_and_get():
    """测试缓存设置和获取"""
    print("\n测试3: 缓存设置和获取")
    cache = SentimentCacheManager(cache_backend='file')
    
    # 设置缓存
    test_data = {'value': 18.5, 'level': 'normal'}
    success = cache.set('AAPL', 'vix', test_data, date='2024-10-27')
    assert success, "缓存设置应该成功"
    print(f"  设置缓存: ✅")
    
    # 获取缓存
    cached_data = cache.get('AAPL', 'vix', date='2024-10-27')
    assert cached_data is not None, "应该能获取到缓存数据"
    assert cached_data['value'] == 18.5, "缓存数据应该匹配"
    print(f"  获取缓存: ✅")
    print(f"  缓存数据: {cached_data}")
    
    print("✅ 缓存设置和获取测试通过")


def test_cache_miss():
    """测试缓存未命中"""
    print("\n测试4: 缓存未命中")
    cache = SentimentCacheManager(cache_backend='file')
    
    # 获取不存在的缓存
    cached_data = cache.get('NONEXISTENT', 'vix', date='2024-10-27')
    assert cached_data is None, "不存在的缓存应返回None"
    print(f"  缓存未命中返回None: ✅")
    
    print("✅ 缓存未命中测试通过")


def test_cache_stats():
    """测试缓存统计"""
    print("\n测试5: 缓存统计")
    cache = SentimentCacheManager(cache_backend='file')
    
    # 执行一些操作
    cache.set('AAPL', 'vix', {'value': 18.5}, date='2024-10-27')
    cache.get('AAPL', 'vix', date='2024-10-27')  # 命中
    cache.get('TSLA', 'vix', date='2024-10-27')  # 未命中
    
    # 获取统计
    stats = cache.get_stats()
    print(f"  统计信息: {stats}")
    
    assert stats['backend'] == 'file', "后端应为file"
    assert stats['hits'] >= 1, "应该有命中记录"
    assert stats['misses'] >= 1, "应该有未命中记录"
    assert stats['sets'] >= 1, "应该有设置记录"
    
    print("✅ 缓存统计测试通过")


def test_global_instance():
    """测试全局实例"""
    print("\n测试6: 全局实例")
    cache1 = get_sentiment_cache()
    cache2 = get_sentiment_cache()
    
    assert cache1 is cache2, "应该返回相同的全局实例"
    print(f"  全局实例单例: ✅")
    
    print("✅ 全局实例测试通过")


def test_cache_duration_config():
    """测试缓存时长配置"""
    print("\n测试7: 缓存时长配置")
    cache = SentimentCacheManager(cache_backend='file')
    
    # 验证配置存在
    assert 'vix' in cache.CACHE_DURATION, "应该有VIX配置"
    assert 'news' in cache.CACHE_DURATION, "应该有新闻配置"
    assert 'northbound' in cache.CACHE_DURATION, "应该有北向资金配置"
    
    print(f"  VIX缓存时长: {cache.CACHE_DURATION['vix']}秒")
    print(f"  新闻缓存时长: {cache.CACHE_DURATION['news']}秒")
    print(f"  北向资金缓存时长: {cache.CACHE_DURATION['northbound']}秒")
    
    print("✅ 缓存时长配置测试通过")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("情绪缓存管理器基础测试")
    print("=" * 60)
    
    try:
        test_cache_initialization()
        test_cache_key_generation()
        test_cache_set_and_get()
        test_cache_miss()
        test_cache_stats()
        test_global_instance()
        test_cache_duration_config()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
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
