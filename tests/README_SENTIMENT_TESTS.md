# 市场情绪分析师测试说明

## 测试文件概览

### 1. 工具直接测试 (推荐先运行)

**文件**: `test_sentiment_tool_direct.py`

这个测试直接调用情绪分析工具，不涉及LLM，可以快速验证工具是否正常工作。

```bash
python tests/test_sentiment_tool_direct.py
```

**测试内容**:
- 直接调用情绪工具获取数据
- 验证工具返回的数据格式和内容
- 检查三个市场（美股、A股、港股）的特有指标

**优点**:
- 快速执行（不需要LLM调用）
- 直接验证数据源和工具逻辑
- 容易调试

---

### 2. 端到端测试

**文件**: `test_sentiment_e2e.py`

这个测试模拟完整的分析流程，包括LLM调用和工具使用。

```bash
python tests/test_sentiment_e2e.py
```

**测试内容**:
- 创建市场情绪分析师
- 使用LLM生成完整的分析报告
- 验证报告质量和准确性

**注意事项**:
- 需要配置LLM API密钥
- 执行时间较长（每个测试可能需要10-30秒）
- 报告长度取决于LLM是否正确调用工具

**常见问题**:

#### 问题1: 报告内容过短

**原因**: LLM可能没有正确调用情绪工具

**解决方案**:
1. 先运行 `test_sentiment_tool_direct.py` 确认工具本身正常
2. 检查LLM配置和API密钥
3. 查看日志中的工具调用记录
4. 确认LLM模型支持function calling

#### 问题2: 测试超时

**原因**: 数据源响应慢或网络问题

**解决方案**:
1. 检查网络连接
2. 使用缓存加速（第二次运行会更快）
3. 考虑使用更快的LLM模型

---

### 3. 性能测试

**文件**: `test_sentiment_performance.py`

测试系统性能和缓存效果。

```bash
python tests/test_sentiment_performance.py
```

**测试内容**:
- 各组件性能分析
- 缓存效果验证
- 瓶颈识别

**性能目标**:
- 单个组件: < 3秒
- 缓存加速: > 2x
- 端到端: < 10秒

---

### 4. 错误处理测试

**文件**: `test_sentiment_error_handling.py`

测试系统的容错能力和降级策略。

```bash
python tests/test_sentiment_error_handling.py
```

**测试内容**:
- 各种数据源失败场景
- 降级策略验证
- 系统稳定性测试

**验证要点**:
- 数据源失败时不崩溃
- 返回有效的降级值
- 记录失败信息

---

## 推荐测试顺序

### 快速验证（5分钟）

```bash
# 1. 先测试工具本身
python tests/test_sentiment_tool_direct.py

# 2. 测试错误处理
python tests/test_sentiment_error_handling.py
```

### 完整验证（15-30分钟）

```bash
# 1. 工具测试
python tests/test_sentiment_tool_direct.py

# 2. 性能测试
python tests/test_sentiment_performance.py

# 3. 错误处理测试
python tests/test_sentiment_error_handling.py

# 4. 端到端测试（需要LLM）
python tests/test_sentiment_e2e.py
```

---

## 调试技巧

### 1. 查看详细日志

所有测试都使用统一的日志系统，日志会显示：
- 数据源调用情况
- 工具执行结果
- 错误和警告信息

### 2. 单独测试某个市场

修改测试文件，注释掉不需要的测试：

```python
# 只测试美股
test_results.append(("美股情绪分析", test_us_stock_sentiment()))
# test_results.append(("A股情绪分析", test_china_stock_sentiment()))
# test_results.append(("港股情绪分析", test_hk_stock_sentiment()))
```

### 3. 检查工具返回值

在 `test_sentiment_tool_direct.py` 中，工具的返回值会完整打印出来，可以查看：
- 数据格式是否正确
- 是否包含必要的字段
- 评分是否在有效范围内

### 4. 验证数据源

如果某个数据源总是失败，可以单独测试：

```python
from tradingagents.dataflows.sentiment_data_sources import CoreSentimentDataSource

core_source = CoreSentimentDataSource(cache_manager=None, toolkit=None)
result = core_source.get_news_sentiment("AAPL", "2024-10-27")
print(result)
```

---

## 常见错误和解决方案

### 错误1: ModuleNotFoundError

**错误信息**: `No module named 'tradingagents.xxx'`

**解决方案**:
```bash
# 确保在项目根目录
cd /path/to/TradingAgents-CN

# 激活虚拟环境
source .venv/bin/activate

# 运行测试
python tests/test_sentiment_tool_direct.py
```

### 错误2: API密钥未配置

**错误信息**: `API key not found`

**解决方案**:
1. 检查 `.env` 文件
2. 确认环境变量已设置
3. 对于工具测试，不需要LLM API密钥

### 错误3: 数据源超时

**错误信息**: `Timeout` 或 `Connection error`

**解决方案**:
1. 检查网络连接
2. 使用VPN（如果需要）
3. 增加超时时间
4. 使用缓存的数据

### 错误4: 报告内容为空

**原因**: LLM没有调用工具

**解决方案**:
1. 先运行 `test_sentiment_tool_direct.py` 确认工具正常
2. 检查LLM模型是否支持function calling
3. 查看日志中的工具调用记录
4. 尝试使用不同的LLM模型

---

## 测试数据说明

### 测试股票代码

- **美股**: AAPL (苹果), NVDA (英伟达)
- **A股**: 600519 (贵州茅台)
- **港股**: 00700.HK (腾讯控股)

这些都是流动性好、数据完整的股票，适合测试。

### 测试日期

默认使用昨天的日期（`datetime.now() - timedelta(days=1)`），因为：
- 当天数据可能不完整
- 历史数据更稳定
- 避免盘中数据波动

---

## 性能基准

基于测试结果，以下是性能基准：

| 操作 | 目标时间 | 说明 |
|------|---------|------|
| 新闻情绪获取 | < 2秒 | 首次调用 |
| 价格动量计算 | < 1秒 | 本地计算 |
| VIX指数获取 | < 2秒 | 外部API |
| 缓存命中 | < 0.1秒 | 内存缓存 |
| 综合评分计算 | < 0.001秒 | 纯计算 |
| 端到端分析 | < 10秒 | 包含LLM |

---

## 贡献指南

如果你想添加新的测试：

1. **工具测试**: 添加到 `test_sentiment_tool_direct.py`
2. **端到端测试**: 添加到 `test_sentiment_e2e.py`
3. **性能测试**: 添加到 `test_sentiment_performance.py`
4. **错误处理**: 添加到 `test_sentiment_error_handling.py`

测试命名规范：
- 函数名: `test_xxx_yyy()`
- 清晰的文档字符串
- 详细的日志输出
- 明确的断言信息

---

## 联系和支持

如果测试遇到问题：

1. 查看日志输出
2. 运行 `test_sentiment_tool_direct.py` 验证基础功能
3. 检查网络和API配置
4. 查看本文档的常见错误部分

祝测试顺利！🎉
