#!/usr/bin/env python3
"""
清除情绪分析缓存
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def clear_cache():
    """清除情绪缓存"""
    
    print("=" * 80)
    print("清除情绪分析缓存")
    print("=" * 80)
    print()
    
    try:
        from tradingagents.dataflows.sentiment_cache import get_sentiment_cache
        
        print("1. 获取缓存管理器...")
        cache = get_sentiment_cache()
        print(f"   ✅ 缓存后端: {cache.backend}")
        print()
        
        print("2. 清除所有情绪缓存...")
        
        # 清除Redis缓存
        if hasattr(cache, 'redis_client') and cache.redis_client:
            try:
                # 获取所有sentiment相关的键
                keys = cache.redis_client.keys("sentiment:*")
                if keys:
                    print(f"   找到 {len(keys)} 个缓存键")
                    deleted = cache.redis_client.delete(*keys)
                    print(f"   ✅ 已删除 {deleted} 个缓存键")
                else:
                    print("   ℹ️  没有找到缓存键")
            except Exception as e:
                print(f"   ⚠️  Redis清除失败: {e}")
        
        # 清除MongoDB缓存
        if hasattr(cache, 'mongo_client') and cache.mongo_client:
            try:
                db = cache.mongo_client['tradingagents']
                collection = db['sentiment_cache']
                result = collection.delete_many({})
                print(f"   ✅ MongoDB已删除 {result.deleted_count} 条记录")
            except Exception as e:
                print(f"   ⚠️  MongoDB清除失败: {e}")
        
        print()
        print("✅ 缓存清除完成")
        print()
        print("现在可以重新运行情绪分析，将获取最新数据")
        
    except Exception as e:
        print(f"❌ 清除缓存失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    clear_cache()
