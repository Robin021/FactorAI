#!/usr/bin/env python3
"""
情绪数据缓存管理器
专门用于市场情绪分析师的缓存管理，集成现有的Redis缓存基础设施
"""

import hashlib
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from pathlib import Path

from tradingagents.utils.logging_manager import get_logger
from tradingagents.config.database_manager import get_database_manager

logger = get_logger('sentiment_cache')


class SentimentCacheManager:
    """情绪数据缓存管理器"""
    
    # 不同数据源的缓存时长配置（秒）
    CACHE_DURATION = {
        'vix': 300,           # 5分钟 - VIX指数
        'news': 1800,         # 30分钟 - 新闻情绪
        'price': 300,         # 5分钟 - 价格动量
        'volume': 300,        # 5分钟 - 成交量
        'northbound': 3600,   # 1小时 - 北向资金
        'margin': 3600,       # 1小时 - 融资融券
        'southbound': 3600,   # 1小时 - 南向资金
        'reddit': 3600,       # 1小时 - Reddit情绪
        'volatility': 3600,   # 1小时 - 波动率
        'composite': 300,     # 5分钟 - 综合情绪评分
    }
    
    def __init__(self, cache_backend: str = 'auto'):
        """
        初始化缓存管理器
        
        Args:
            cache_backend: 缓存后端 ('redis', 'file', 'auto')
                          'auto' 会自动选择最佳后端
        """
        self.db_manager = get_database_manager()
        
        # 确定缓存后端
        if cache_backend == 'auto':
            if self.db_manager.is_redis_available():
                self.backend = 'redis'
                self.redis_client = self.db_manager.get_redis_client()
            else:
                self.backend = 'file'
                self._init_file_cache()
        elif cache_backend == 'redis':
            if self.db_manager.is_redis_available():
                self.backend = 'redis'
                self.redis_client = self.db_manager.get_redis_client()
            else:
                logger.warning("Redis不可用，降级到文件缓存")
                self.backend = 'file'
                self._init_file_cache()
        else:
            self.backend = 'file'
            self._init_file_cache()
        
        # 缓存命中率统计
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'errors': 0
        }
        
        logger.info(f"情绪缓存管理器初始化完成 - 后端: {self.backend}")
    
    def _init_file_cache(self):
        """初始化文件缓存"""
        self.cache_dir = Path("data/cache/sentiment")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"文件缓存目录: {self.cache_dir}")
    
    def _generate_cache_key(
        self,
        ticker: str,
        data_type: str,
        date: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        生成缓存键
        
        Args:
            ticker: 股票代码
            data_type: 数据类型 (vix, news, price, etc.)
            date: 日期 (YYYY-MM-DD)
            **kwargs: 其他参数
        
        Returns:
            缓存键字符串
        """
        # 使用当前日期如果未提供
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # 构建键字符串
        key_parts = [
            'sentiment',
            ticker,
            data_type,
            date
        ]
        
        # 添加额外参数
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        
        # 生成短哈希以避免键过长
        key_str = "_".join(key_parts)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()[:8]
        
        # 格式: sentiment:ticker:data_type:date:hash
        cache_key = f"sentiment:{ticker}:{data_type}:{date}:{key_hash}"
        
        return cache_key
    
    def get(
        self,
        ticker: str,
        data_type: str,
        date: Optional[str] = None,
        **kwargs
    ) -> Optional[Any]:
        """
        获取缓存数据
        
        Args:
            ticker: 股票代码
            data_type: 数据类型
            date: 日期
            **kwargs: 其他参数
        
        Returns:
            缓存的数据，如果不存在或过期则返回None
        """
        cache_key = self._generate_cache_key(ticker, data_type, date, **kwargs)
        
        try:
            if self.backend == 'redis':
                data = self._get_from_redis(cache_key)
            else:
                data = self._get_from_file(cache_key, data_type)
            
            if data is not None:
                self.stats['hits'] += 1
                logger.debug(f"缓存命中: {cache_key}")
                return data
            else:
                self.stats['misses'] += 1
                logger.debug(f"缓存未命中: {cache_key}")
                return None
                
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"获取缓存失败 {cache_key}: {e}")
            return None
    
    def _get_from_redis(self, cache_key: str) -> Optional[Any]:
        """从Redis获取数据"""
        try:
            serialized_data = self.redis_client.get(cache_key)
            if serialized_data:
                return pickle.loads(serialized_data)
            return None
        except Exception as e:
            logger.error(f"Redis读取失败: {e}")
            return None
    
    def _get_from_file(self, cache_key: str, data_type: str) -> Optional[Any]:
        """从文件获取数据"""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            # 检查是否过期
            ttl = self.CACHE_DURATION.get(data_type, 3600)
            cached_at = cache_data.get('timestamp')
            
            if cached_at:
                age = (datetime.now() - cached_at).total_seconds()
                if age > ttl:
                    # 过期，删除文件
                    cache_file.unlink()
                    logger.debug(f"缓存已过期: {cache_key} (age: {age}s, ttl: {ttl}s)")
                    return None
            
            return cache_data.get('data')
            
        except Exception as e:
            logger.error(f"文件读取失败: {e}")
            return None
    
    def set(
        self,
        ticker: str,
        data_type: str,
        value: Any,
        date: Optional[str] = None,
        ttl: Optional[int] = None,
        **kwargs
    ) -> bool:
        """
        设置缓存数据
        
        Args:
            ticker: 股票代码
            data_type: 数据类型
            value: 要缓存的数据
            date: 日期
            ttl: 过期时间（秒），None则使用默认配置
            **kwargs: 其他参数
        
        Returns:
            是否成功
        """
        cache_key = self._generate_cache_key(ticker, data_type, date, **kwargs)
        
        # 获取TTL
        if ttl is None:
            ttl = self.CACHE_DURATION.get(data_type, 3600)
        
        try:
            if self.backend == 'redis':
                success = self._set_to_redis(cache_key, value, ttl)
            else:
                success = self._set_to_file(cache_key, value)
            
            if success:
                self.stats['sets'] += 1
                logger.debug(f"缓存设置成功: {cache_key} (ttl: {ttl}s)")
            
            return success
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"设置缓存失败 {cache_key}: {e}")
            return False
    
    def _set_to_redis(self, cache_key: str, value: Any, ttl: int) -> bool:
        """设置Redis缓存"""
        try:
            serialized_data = pickle.dumps(value)
            self.redis_client.setex(cache_key, ttl, serialized_data)
            return True
        except Exception as e:
            logger.error(f"Redis写入失败: {e}")
            return False
    
    def _set_to_file(self, cache_key: str, value: Any) -> bool:
        """设置文件缓存"""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        try:
            cache_data = {
                'data': value,
                'timestamp': datetime.now()
            }
            
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            
            return True
            
        except Exception as e:
            logger.error(f"文件写入失败: {e}")
            return False
    
    def invalidate(
        self,
        pattern: str
    ) -> int:
        """
        失效匹配的缓存
        
        Args:
            pattern: 匹配模式 (支持通配符 *)
        
        Returns:
            删除的缓存数量
        """
        try:
            if self.backend == 'redis':
                return self._invalidate_redis(pattern)
            else:
                return self._invalidate_file(pattern)
        except Exception as e:
            logger.error(f"缓存失效失败 {pattern}: {e}")
            return 0
    
    def _invalidate_redis(self, pattern: str) -> int:
        """失效Redis缓存"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Redis缓存失效: {deleted} 个键匹配 {pattern}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Redis缓存失效失败: {e}")
            return 0
    
    def _invalidate_file(self, pattern: str) -> int:
        """失效文件缓存"""
        import fnmatch
        
        deleted = 0
        try:
            for cache_file in self.cache_dir.glob("*.pkl"):
                if fnmatch.fnmatch(cache_file.stem, pattern):
                    cache_file.unlink()
                    deleted += 1
            
            if deleted > 0:
                logger.info(f"文件缓存失效: {deleted} 个文件匹配 {pattern}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"文件缓存失效失败: {e}")
            return 0
    
    def get_hit_rate(self) -> float:
        """
        获取缓存命中率
        
        Returns:
            命中率 (0.0 - 1.0)
        """
        total = self.stats['hits'] + self.stats['misses']
        if total == 0:
            return 0.0
        return self.stats['hits'] / total
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        hit_rate = self.get_hit_rate()
        
        stats = {
            'backend': self.backend,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'sets': self.stats['sets'],
            'errors': self.stats['errors'],
            'hit_rate': f"{hit_rate:.2%}",
            'hit_rate_value': hit_rate
        }
        
        # 添加后端特定统计
        if self.backend == 'redis' and self.redis_client:
            try:
                info = self.redis_client.info()
                stats['redis_memory'] = info.get('used_memory_human', 'N/A')
                stats['redis_keys'] = self.redis_client.dbsize()
            except:
                pass
        elif self.backend == 'file':
            cache_files = list(self.cache_dir.glob("*.pkl"))
            stats['file_count'] = len(cache_files)
            total_size = sum(f.stat().st_size for f in cache_files)
            stats['total_size_mb'] = round(total_size / (1024 * 1024), 2)
        
        return stats
    
    def clear_all(self) -> int:
        """
        清空所有缓存
        
        Returns:
            清除的缓存数量
        """
        try:
            if self.backend == 'redis':
                return self._clear_redis()
            else:
                return self._clear_file()
        except Exception as e:
            logger.error(f"清空缓存失败: {e}")
            return 0
    
    def _clear_redis(self) -> int:
        """清空Redis缓存"""
        try:
            keys = self.redis_client.keys("sentiment:*")
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Redis缓存已清空: {deleted} 个键")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Redis缓存清空失败: {e}")
            return 0
    
    def _clear_file(self) -> int:
        """清空文件缓存"""
        deleted = 0
        try:
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
                deleted += 1
            
            logger.info(f"文件缓存已清空: {deleted} 个文件")
            return deleted
            
        except Exception as e:
            logger.error(f"文件缓存清空失败: {e}")
            return 0
    
    def clear_expired(self) -> int:
        """
        清理过期缓存（仅文件缓存需要）
        
        Returns:
            清除的缓存数量
        """
        if self.backend != 'file':
            logger.debug("Redis缓存自动过期，无需手动清理")
            return 0
        
        deleted = 0
        try:
            for cache_file in self.cache_dir.glob("*.pkl"):
                try:
                    with open(cache_file, 'rb') as f:
                        cache_data = pickle.load(f)
                    
                    # 从文件名提取数据类型
                    # 格式: sentiment:ticker:data_type:date:hash.pkl
                    parts = cache_file.stem.split(':')
                    if len(parts) >= 3:
                        data_type = parts[2]
                        ttl = self.CACHE_DURATION.get(data_type, 3600)
                        
                        cached_at = cache_data.get('timestamp')
                        if cached_at:
                            age = (datetime.now() - cached_at).total_seconds()
                            if age > ttl:
                                cache_file.unlink()
                                deleted += 1
                
                except Exception as e:
                    logger.warning(f"检查缓存文件失败 {cache_file}: {e}")
                    continue
            
            if deleted > 0:
                logger.info(f"清理过期缓存: {deleted} 个文件")
            
            return deleted
            
        except Exception as e:
            logger.error(f"清理过期缓存失败: {e}")
            return 0


# 全局缓存管理器实例
_sentiment_cache_manager = None


def get_sentiment_cache() -> SentimentCacheManager:
    """获取全局情绪缓存管理器实例"""
    global _sentiment_cache_manager
    if _sentiment_cache_manager is None:
        _sentiment_cache_manager = SentimentCacheManager()
    return _sentiment_cache_manager



# ============================================================================
# 缓存键命名规范和使用示例
# ============================================================================

"""
缓存键命名规范:
    格式: sentiment:ticker:data_type:date:hash
    
    示例:
    - sentiment:AAPL:vix:2024-10-27:a1b2c3d4
    - sentiment:600519:northbound:2024-10-27:e5f6g7h8
    - sentiment:00700:southbound:2024-10-27:i9j0k1l2

缓存键生成逻辑:
    1. 基础部分: sentiment:ticker:data_type:date
    2. 额外参数: 按字母顺序排序后添加
    3. 哈希: MD5前8位，避免键过长
    
使用示例:

# 1. 缓存VIX数据
cache = get_sentiment_cache()
vix_data = {'value': 18.5, 'level': 'normal'}
cache.set('AAPL', 'vix', vix_data, date='2024-10-27')

# 2. 获取VIX数据
vix_data = cache.get('AAPL', 'vix', date='2024-10-27')

# 3. 缓存北向资金数据
northbound_data = {'net_flow': 1500000000, 'sentiment': 0.6}
cache.set('600519', 'northbound', northbound_data)

# 4. 获取北向资金数据
northbound_data = cache.get('600519', 'northbound')

# 5. 缓存综合情绪评分
composite_data = {
    'score': 65.5,
    'level': '乐观',
    'breakdown': {'news': 0.5, 'money_flow': 0.3}
}
cache.set('TSLA', 'composite', composite_data)

# 6. 失效特定股票的所有缓存
cache.invalidate('sentiment:AAPL:*')

# 7. 失效特定类型的所有缓存
cache.invalidate('sentiment:*:vix:*')

# 8. 失效特定日期的所有缓存
cache.invalidate('sentiment:*:*:2024-10-27:*')

# 9. 获取缓存统计
stats = cache.get_stats()
print(f"命中率: {stats['hit_rate']}")
print(f"总命中: {stats['hits']}, 总未命中: {stats['misses']}")

# 10. 清理过期缓存（文件缓存）
deleted = cache.clear_expired()
print(f"清理了 {deleted} 个过期缓存")

# 11. 清空所有情绪缓存
deleted = cache.clear_all()
print(f"清空了 {deleted} 个缓存")

缓存时长配置:
    - VIX指数: 5分钟 (实时性要求高)
    - 新闻情绪: 30分钟 (更新频率中等)
    - 价格动量: 5分钟 (实时性要求高)
    - 成交量: 5分钟 (实时性要求高)
    - 北向资金: 1小时 (日级别数据)
    - 融资融券: 1小时 (日级别数据)
    - 南向资金: 1小时 (日级别数据)
    - Reddit情绪: 1小时 (更新频率低)
    - 波动率: 1小时 (计算密集)
    - 综合评分: 5分钟 (组合数据)

缓存命中率监控:
    缓存管理器自动跟踪以下指标:
    - hits: 缓存命中次数
    - misses: 缓存未命中次数
    - sets: 缓存设置次数
    - errors: 错误次数
    - hit_rate: 命中率 (hits / (hits + misses))
    
    使用 get_stats() 方法获取实时统计信息

缓存失效策略:
    1. 自动过期:
       - Redis: 使用SETEX自动过期
       - 文件: 读取时检查时间戳
    
    2. 手动失效:
       - invalidate(pattern): 按模式失效
       - clear_all(): 清空所有
       - clear_expired(): 清理过期（文件缓存）
    
    3. 失效场景:
       - 数据更新: 失效相关股票的缓存
       - 日期变更: 失效旧日期的缓存
       - 错误数据: 失效特定类型的缓存

性能优化建议:
    1. 使用Redis作为主缓存后端（性能最佳）
    2. 合理设置TTL，平衡实时性和性能
    3. 定期清理过期缓存（文件缓存）
    4. 监控缓存命中率，优化缓存策略
    5. 对于高频访问的数据，考虑预热缓存
"""
