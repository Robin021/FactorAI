# 情绪数据缓存管理器

## 概述

`SentimentCacheManager` 是专门为市场情绪分析师设计的缓存管理器，集成了现有的Redis缓存基础设施，支持自动降级到文件缓存。

## 特性

- ✅ **多后端支持**: Redis（主）、文件缓存（降级）
- ✅ **智能TTL配置**: 不同数据类型使用不同的缓存时长
- ✅ **缓存键规范**: 统一的命名规范，支持模式匹配
- ✅ **命中率监控**: 自动跟踪缓存性能指标
- ✅ **自动过期**: Redis自动过期，文件缓存读取时检查
- ✅ **批量失效**: 支持通配符模式批量失效缓存

## 安装和配置

### 环境变量

```bash
# Redis配置（可选，不配置则使用文件缓存）
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
```

### 初始化

```python
from tradingagents.dataflows.sentiment_cache import get_sentiment_cache

# 获取全局缓存实例（自动选择最佳后端）
cache = get_sentiment_cache()

# 或手动指定后端
from tradingagents.dataflows.sentiment_cache import SentimentCacheManager
cache = SentimentCacheManager(cache_backend='redis')  # 'redis', 'file', 'auto'
```

## 使用示例

### 基本操作

```python
from tradingagents.dataflows.sentiment_cache import get_sentiment_cache

cache = get_sentiment_cache()

# 1. 设置缓存
vix_data = {'value': 18.5, 'level': 'normal'}
cache.set('AAPL', 'vix', vix_data, date='2024-10-27')

# 2. 获取缓存
vix_data = cache.get('AAPL', 'vix', date='2024-10-27')
if vix_data:
    print(f"VIX: {vix_data['value']}")
else:
    print("缓存未命中")

# 3. 自定义TTL
cache.set('TSLA', 'news', news_data, ttl=600)  # 10分钟
```

### 不同数据类型示例

```python
# VIX恐慌指数（美股）
vix_data = {'value': 18.5, 'level': 'normal', 'timestamp': '2024-10-27T10:00:00'}
cache.set('AAPL', 'vix', vix_data)

# 新闻情绪
news_sentiment = {'score': 0.65, 'articles': 10, 'positive': 7, 'negative': 3}
cache.set('AAPL', 'news', news_sentiment)

# 北向资金（A股）
northbound_data = {'net_flow': 1500000000, 'sentiment': 0.6, 'date': '2024-10-27'}
cache.set('600519', 'northbound', northbound_data)

# 融资融券（A股）
margin_data = {'margin_balance': 5000000000, 'change_pct': 2.5}
cache.set('600519', 'margin', margin_data)

# 南向资金（港股）
southbound_data = {'net_flow': 800000000, 'sentiment': 0.4}
cache.set('00700', 'southbound', southbound_data)

# Reddit情绪（美股）
reddit_data = {'score': 0.75, 'mentions': 150, 'sentiment': 'bullish'}
cache.set('TSLA', 'reddit', reddit_data)

# 综合情绪评分
composite_data = {
    'score': 65.5,
    'level': '乐观',
    'breakdown': {
        'news': 0.5,
        'money_flow': 0.3,
        'volatility': -0.2,
        'technical': 0.4,
        'social': 0.1
    }
}
cache.set('AAPL', 'composite', composite_data)
```

### 缓存失效

```python
# 失效特定股票的所有缓存
cache.invalidate('sentiment:AAPL:*')

# 失效特定类型的所有缓存
cache.invalidate('sentiment:*:vix:*')

# 失效特定日期的所有缓存
cache.invalidate('sentiment:*:*:2024-10-27:*')

# 清空所有情绪缓存
deleted = cache.clear_all()
print(f"清空了 {deleted} 个缓存")

# 清理过期缓存（仅文件缓存需要）
deleted = cache.clear_expired()
print(f"清理了 {deleted} 个过期缓存")
```

### 监控和统计

```python
# 获取缓存统计
stats = cache.get_stats()
print(f"后端: {stats['backend']}")
print(f"命中率: {stats['hit_rate']}")
print(f"命中: {stats['hits']}, 未命中: {stats['misses']}")
print(f"设置: {stats['sets']}, 错误: {stats['errors']}")

# Redis后端额外信息
if stats['backend'] == 'redis':
    print(f"Redis内存: {stats.get('redis_memory')}")
    print(f"Redis键数: {stats.get('redis_keys')}")

# 文件后端额外信息
if stats['backend'] == 'file':
    print(f"文件数: {stats.get('file_count')}")
    print(f"总大小: {stats.get('total_size_mb')} MB")

# 获取命中率
hit_rate = cache.get_hit_rate()
print(f"当前命中率: {hit_rate:.2%}")
```

## 缓存键命名规范

### 格式

```
sentiment:ticker:data_type:date:hash
```

### 示例

```
sentiment:AAPL:vix:2024-10-27:a1b2c3d4
sentiment:600519:northbound:2024-10-27:e5f6g7h8
sentiment:00700:southbound:2024-10-27:i9j0k1l2
```

### 组成部分

1. **前缀**: `sentiment` - 标识情绪缓存
2. **股票代码**: `ticker` - 股票代码（AAPL, 600519, 00700等）
3. **数据类型**: `data_type` - 数据类型（vix, news, northbound等）
4. **日期**: `date` - 日期（YYYY-MM-DD格式）
5. **哈希**: `hash` - MD5前8位，避免键过长

## 缓存时长配置

| 数据类型 | TTL | 说明 |
|---------|-----|------|
| vix | 5分钟 | VIX恐慌指数，实时性要求高 |
| news | 30分钟 | 新闻情绪，更新频率中等 |
| price | 5分钟 | 价格动量，实时性要求高 |
| volume | 5分钟 | 成交量，实时性要求高 |
| northbound | 1小时 | 北向资金，日级别数据 |
| margin | 1小时 | 融资融券，日级别数据 |
| southbound | 1小时 | 南向资金，日级别数据 |
| reddit | 1小时 | Reddit情绪，更新频率低 |
| volatility | 1小时 | 波动率，计算密集 |
| composite | 5分钟 | 综合评分，组合数据 |

## 性能优化建议

1. **使用Redis**: Redis性能远优于文件缓存，建议生产环境使用
2. **合理设置TTL**: 平衡实时性和性能，避免过短或过长
3. **定期清理**: 文件缓存需要定期调用 `clear_expired()`
4. **监控命中率**: 命中率低于50%时考虑调整缓存策略
5. **预热缓存**: 对于高频访问的数据，可以预先加载到缓存

## 集成到数据源

```python
from tradingagents.dataflows.sentiment_cache import get_sentiment_cache
from tradingagents.dataflows.sentiment_data_sources import CoreSentimentDataSource

class CoreSentimentDataSource:
    def __init__(self, cache_manager=None, toolkit=None):
        self.cache = cache_manager or get_sentiment_cache()
        self.toolkit = toolkit
    
    def get_news_sentiment(self, ticker: str, date: str = None) -> float:
        # 尝试从缓存获取
        cached = self.cache.get(ticker, 'news', date=date)
        if cached is not None:
            return cached['score']
        
        # 缓存未命中，获取新数据
        news_data = self._fetch_news_sentiment(ticker)
        
        # 缓存结果
        self.cache.set(ticker, 'news', news_data, date=date)
        
        return news_data['score']
```

## 错误处理

缓存管理器设计为永不抛出异常，所有错误都会被捕获并记录：

```python
# 即使Redis不可用，也会自动降级到文件缓存
cache = get_sentiment_cache()

# 获取失败返回None，不会抛出异常
data = cache.get('AAPL', 'vix')
if data is None:
    # 处理缓存未命中
    data = fetch_from_api()
```

## 测试

运行基础测试：

```bash
python tests/test_sentiment_cache_basic.py
```

测试覆盖：
- ✅ 缓存管理器初始化
- ✅ 缓存键生成
- ✅ 缓存设置和获取
- ✅ 缓存未命中
- ✅ 缓存统计
- ✅ 全局实例
- ✅ 缓存时长配置

## 架构设计

```
SentimentCacheManager
├── 后端选择
│   ├── Redis (主)
│   └── File (降级)
├── 缓存操作
│   ├── get() - 获取缓存
│   ├── set() - 设置缓存
│   ├── invalidate() - 失效缓存
│   ├── clear_all() - 清空所有
│   └── clear_expired() - 清理过期
├── 监控统计
│   ├── get_stats() - 获取统计
│   └── get_hit_rate() - 获取命中率
└── 键管理
    └── _generate_cache_key() - 生成缓存键
```

## 依赖

- `redis`: Redis客户端（可选）
- `pickle`: 数据序列化
- `hashlib`: 键哈希生成
- `tradingagents.config.database_manager`: 数据库管理器
- `tradingagents.utils.logging_manager`: 日志管理器

## 许可

与主项目相同
