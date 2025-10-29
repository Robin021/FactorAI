# 市场情绪分析功能使用指南

## 概述

市场情绪分析功能已经完全实现并集成到系统中。该功能通过整合多维度数据源，提供量化的市场情绪评估。

## 功能特性

### 核心情绪数据（三市场通用）
- ✅ **新闻情绪分析**: 基于新闻内容的情绪评分
- ✅ **价格动量分析**: 基于价格趋势的动量评分
- ✅ **成交量情绪**: 基于成交量变化的情绪评分

### 美股增强数据
- ✅ **VIX恐慌指数**: 市场波动率和恐慌程度
- ✅ **Reddit社交媒体情绪**: 社交媒体讨论情绪

### A股增强数据
- ✅ **北向资金流向**: 外资流入流出情况
- ✅ **融资融券数据**: 杠杆交易情绪
- ✅ **波动率情绪**: 历史波动率百分位

### 港股增强数据
- ✅ **南向资金流向**: 内地资金流入流出情况

### 综合评估
- ✅ **综合情绪评分**: 0-100分的量化评分
- ✅ **情绪等级**: 极度悲观、悲观、中性、乐观、极度乐观
- ✅ **组件贡献度分析**: 各情绪组件的权重和贡献
- ✅ **极端情绪警告**: 当情绪达到极端值时的反向指标提示

## 启用方法

### 方法1: 修改默认配置（推荐）

在 `backend/services/analysis_service.py` 中，默认的分析师列表已经包含了 `market_sentiment`：

```python
selected_analysts = analysis_request.analysts or ["market", "news", "fundamentals", "market_sentiment"]
```

这意味着**所有新的分析请求都会自动包含情绪分析**。

### 方法2: API请求时指定

在发起分析请求时，可以通过 `analysts` 参数指定要使用的分析师：

```json
{
  "stock_code": "AAPL",
  "market_type": "us",
  "analysts": ["market", "news", "fundamentals", "market_sentiment"]
}
```

### 方法3: 命令行指定

如果使用命令行工具，可以通过参数指定：

```bash
python cli/analyze.py --stock AAPL --analysts market,news,fundamentals,market_sentiment
```

## 验证功能

### 运行测试脚本

```bash
python test_sentiment_analysis.py
```

该脚本会测试三个市场的股票：
- 美股: AAPL
- A股: 600519
- 港股: 00700

### 检查分析结果

分析完成后，检查以下内容：

1. **日志文件**: 查看 `logs/` 目录下的日志文件
2. **结果文件**: 查看 `eval_results/{ticker}/TradingAgentsStrategy_logs/full_states_log.json`
3. **数据库记录**: 查看MongoDB中的分析记录

### 预期输出

成功的情绪分析报告应包含：

```markdown
# 市场情绪数据

**股票代码**: AAPL
**分析日期**: 2024-10-27
**市场类型**: 美股

## 综合情绪评估

- **综合情绪评分**: 65.50 / 100
- **情绪等级**: 乐观

## 情绪组件分析

| 组件 | 评分 | 贡献度 |
|------|------|--------|
| 新闻情绪 | 0.650 | 0.300 |
| 技术动量 | 0.450 | 0.200 |
| 成交量 | 0.550 | 0.150 |
| 波动率 | -0.200 | 0.200 |
| 社交媒体 | 0.750 | 0.150 |

## 核心情绪数据

- **新闻情绪**: 0.650
- **价格动量**: 0.450
- **成交量情绪**: 0.550

## 增强情绪数据

- **VIX恐慌指数**: -0.200
- **Reddit情绪**: 0.750

## 数据源信息

- **数据时间戳**: 2024-10-27 10:00:00
- **核心数据源**: 新闻API, 价格数据, 成交量数据
- **增强数据源**: VIX指数, Reddit社交媒体
```

## 架构说明

### 核心组件

1. **情绪分析工具** (`tradingagents/tools/sentiment_tools.py`)
   - `create_sentiment_analysis_tool()`: 创建情绪分析工具
   - `create_vix_tool()`: 创建VIX工具
   - `create_capital_flow_tool()`: 创建资金流向工具

2. **市场情绪分析师** (`tradingagents/agents/analysts/market_sentiment_analyst.py`)
   - `create_market_sentiment_analyst()`: 创建分析师节点
   - 负责调用情绪工具并生成分析报告

3. **情绪数据源** (`tradingagents/dataflows/sentiment_data_sources.py`)
   - `CoreSentimentDataSource`: 核心情绪数据源
   - `USEnhancedDataSource`: 美股增强数据源
   - `CNEnhancedDataSource`: A股增强数据源
   - `HKEnhancedDataSource`: 港股增强数据源

4. **情绪计算器** (`tradingagents/agents/utils/sentiment_calculator.py`)
   - 计算综合情绪评分
   - 确定情绪等级
   - 分析组件贡献度

5. **缓存管理** (`tradingagents/dataflows/sentiment_cache.py`)
   - Redis缓存（主）
   - 文件缓存（降级）
   - 自动过期和失效

### 工作流集成

情绪分析师被集成到主工作流中：

```
START → Market Analyst → News Analyst → Fundamentals Analyst → Market Sentiment Analyst → Bull Researcher → ...
```

### 状态管理

情绪分析结果保存在 `AgentState` 中：

```python
class AgentState(MessagesState):
    # ... 其他字段 ...
    
    # market sentiment analysis
    market_sentiment_report: str  # 情绪分析报告
    sentiment_score: float  # 情绪评分 (0-100)
```

## 配置选项

### 缓存配置

在 `.env` 文件中配置Redis缓存：

```bash
# Redis配置（可选，不配置则使用文件缓存）
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
```

### 数据源配置

某些数据源需要API密钥：

```bash
# TuShare API Token（用于A股融资融券数据）
TUSHARE_TOKEN=your_token_here
```

### 缓存时长

不同数据类型的缓存时长（在代码中配置）：

| 数据类型 | TTL | 说明 |
|---------|-----|------|
| vix | 5分钟 | VIX恐慌指数 |
| news | 30分钟 | 新闻情绪 |
| price | 5分钟 | 价格动量 |
| volume | 5分钟 | 成交量 |
| northbound | 1小时 | 北向资金 |
| margin | 1小时 | 融资融券 |
| southbound | 1小时 | 南向资金 |
| reddit | 1小时 | Reddit情绪 |
| volatility | 1小时 | 波动率 |
| composite | 5分钟 | 综合评分 |

## 故障排查

### 问题1: 分析结果中没有情绪报告

**原因**: `market_sentiment` 分析师未被包含在分析师列表中

**解决方案**:
1. 检查 `backend/services/analysis_service.py` 第144行
2. 确保默认列表包含 `"market_sentiment"`
3. 或在API请求中显式指定

### 问题2: 情绪评分为0或50（中性）

**原因**: 数据源不可用或获取失败

**解决方案**:
1. 检查日志文件，查看具体错误
2. 验证API密钥配置（如TuShare Token）
3. 检查网络连接
4. 查看降级策略日志

### 问题3: VIX数据获取失败

**原因**: yfinance库未安装或Yahoo Finance不可用

**解决方案**:
```bash
pip install yfinance
```

### 问题4: 北向/南向资金数据获取失败

**原因**: AKShare库未安装或数据源不可用

**解决方案**:
```bash
pip install akshare
```

### 问题5: 缓存未生效

**原因**: Redis未配置或连接失败

**解决方案**:
1. 检查Redis服务是否运行
2. 验证 `.env` 中的Redis配置
3. 系统会自动降级到文件缓存

## 性能优化

### 1. 启用Redis缓存

Redis缓存性能远优于文件缓存：

```bash
# 安装Redis
brew install redis  # macOS
sudo apt-get install redis-server  # Ubuntu

# 启动Redis
redis-server
```

### 2. 调整缓存时长

根据实际需求调整缓存TTL，在 `sentiment_data_sources.py` 中修改 `_get_cache_ttl()` 方法。

### 3. 预热缓存

对于高频访问的股票，可以预先加载数据到缓存：

```python
from tradingagents.dataflows.sentiment_cache import get_sentiment_cache

cache = get_sentiment_cache()
# 预加载数据...
```

### 4. 监控缓存命中率

```python
cache = get_sentiment_cache()
stats = cache.get_stats()
print(f"缓存命中率: {stats['hit_rate']:.2%}")
```

建议命中率保持在50%以上。

## 更新日志

### 2024-10-28
- ✅ 将 `market_sentiment` 添加到默认分析师列表
- ✅ 创建测试脚本 `test_sentiment_analysis.py`
- ✅ 创建使用指南文档

### 之前版本
- ✅ 实现核心情绪分析功能
- ✅ 实现多市场增强数据源
- ✅ 实现缓存管理
- ✅ 实现降级策略
- ✅ 集成到主工作流

## 相关文档

- [情绪缓存管理器文档](../tradingagents/dataflows/README_sentiment_cache.md)
- [API文档](./api/README.md)
- [开发指南](./development/README.md)

## 支持

如有问题，请：
1. 查看日志文件
2. 运行测试脚本
3. 检查配置文件
4. 提交Issue到GitHub仓库
