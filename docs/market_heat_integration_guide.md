# 市场热度集成使用指南

## ✅ 集成完成

市场热度动态风险控制系统已成功集成到TradingAgents分析流程中！

## 🎯 核心功能

### 1. 自动市场热度评估

每次分析开始时，系统会自动：
1. 获取实时市场数据（涨停家数、换手率、成交量等）
2. 计算市场热度评分（0-100分）
3. 确定市场热度等级（极冷/冷淡/正常/火热/沸腾）

### 2. 动态风险辩论轮次

根据市场热度自动调整风险辩论轮次：

| 市场热度 | 辩论轮次 | 说明 |
|---------|---------|------|
| ≥ 60分 | **2轮** | 市场火热，充分讨论机会与风险 |
| < 60分 | **1轮** | 市场冷淡，快速决策避免过度分析 |

### 3. 风险控制参数调整

系统会在最终决策中考虑市场热度，调整：
- 仓位建议（市场热时提高，冷时降低）
- 止损建议（市场热时放宽，冷时收紧）

## 📊 工作流程

```
START
  ↓
🌡️ Market Heat Evaluator (新增)
  ├─ 获取市场数据
  ├─ 计算热度评分
  └─ 存入state
  ↓
📊 Market Analyst
  ↓
📱 Social Analyst
  ↓
📰 News Analyst
  ↓
💼 Fundamentals Analyst
  ↓
🐂 Bull Researcher ⟷ 🐻 Bear Researcher
  ↓
👨‍⚖️ Research Manager
  ↓
💼 Trader
  ↓
🎲 Risky Analyst ⟷ 🛡️ Safe Analyst ⟷ ⚖️ Neutral Analyst
  │  (根据市场热度动态调整轮次)
  ↓
👨‍⚖️ Risk Judge
  │  (考虑市场热度给出最终建议)
  ↓
END
```

## 🔧 配置选项

### 启用动态风险辩论（默认）

```python
from tradingagents.graph.conditional_logic import ConditionalLogic

logic = ConditionalLogic(
    max_debate_rounds=1,
    max_risk_discuss_rounds=1,
    enable_dynamic_risk_rounds=True  # 启用动态调整
)
```

### 禁用动态风险辩论

如果你想使用固定的风险辩论轮次：

```python
logic = ConditionalLogic(
    max_debate_rounds=1,
    max_risk_discuss_rounds=2,  # 固定2轮
    enable_dynamic_risk_rounds=False  # 禁用动态调整
)
```

## 📝 State结构变化

新增了以下字段到AgentState：

```python
class AgentState(MessagesState):
    # ... 原有字段 ...
    
    # 新增：市场热度相关字段
    market_heat_score: float          # 市场热度评分 (0-100)
    market_heat_level: str            # 市场热度等级 (极冷/冷淡/正常/火热/沸腾)
    market_heat_data: dict            # 市场热度详细数据
```

## 🎮 使用示例

### 示例1：运行完整分析

```python
from tradingagents import TradingAgents

# 创建分析实例
agent = TradingAgents(
    config={
        'enable_dynamic_risk_rounds': True  # 启用动态风险辩论
    }
)

# 运行分析（会自动评估市场热度）
result = agent.analyze(
    stock_code="600519",
    trade_date="2025-10-29"
)

# 查看市场热度信息
print(f"市场热度: {result['market_heat_score']:.1f}")
print(f"热度等级: {result['market_heat_level']}")
print(f"风险辩论轮次: {result['market_heat_data']['risk_adjustment']['risk_rounds']}")
```

### 示例2：查看市场热度详情

```python
from tradingagents.agents.utils.market_heat_node import get_market_heat_summary

# 从分析结果中获取市场热度摘要
summary = get_market_heat_summary(result)
print(summary)
```

输出示例：
```
## 🌡️ 市场热度分析

### 热度评分
- **评分**: 27.2 / 100
- **等级**: 冷淡

### 市场数据
- 涨停家数: 101家 (1.75%)
- 上涨家数: 2672家 (46.35%)
- 下跌家数: 2621家
- 平均换手率: 3.67%
- 成交量放大: 1.00倍
- 市场波动率: 3.06%

### 风险控制调整
- 仓位倍数: 0.70x
- 止损收紧系数: 1.20x
- 风险辩论轮次: 1轮

### 策略建议
❄️ 市场交投清淡（热度：27.2）
建议：
- 降低仓位至70%左右
- 适当收紧止损
- 谨慎操作，关注市场情绪变化
- 风险控制采用保守策略（1轮辩论）
```

## 🧪 测试验证

运行测试脚本验证集成：

```bash
# 测试动态风险辩论轮次
python tests/test_market_heat_integration.py

# 测试市场热度数据获取
python tradingagents/dataflows/market_heat_data.py

# 测试完整示例
python examples/market_heat_integration_example.py
```

## 📊 实际效果对比

### 场景1：牛市（市场热度70）

**传统固定策略**：
- 风险辩论：1轮
- 可能错失机会，分析不够充分

**动态调整策略**：
- 风险辩论：**2轮** ✅
- 充分讨论，把握牛市机会
- 仓位建议提高30%
- 止损放宽20%

### 场景2：熊市（市场热度30）

**传统固定策略**：
- 风险辩论：1轮
- 快速决策

**动态调整策略**：
- 风险辩论：**1轮** ✅
- 快速决策，避免过度分析
- 仓位建议降低30%
- 止损收紧20%

## 🔍 日志输出

启用后，你会在日志中看到：

```
🔧 ConditionalLogic初始化: 投资辩论=1轮, 风险辩论基础=1轮, 动态调整=启用
🌡️ 市场热度评估：开始获取市场数据
✅ 市场数据获取成功: 涨停=101家, 上涨=2672家, 换手率=3.67%
✅ 市场热度评估完成: 评分=27.2, 等级=冷淡, 风险辩论轮次=1轮
🌡️ 市场热度27.2（冷淡），风险辩论轮次: 1轮（快速决策）
✅ 风险辩论完成: 3次发言 (目标: 3次, 1轮)
```

## ⚠️ 注意事项

### 1. 数据依赖

市场热度评估依赖AKShare实时数据：
- 需要网络连接
- 交易时间外可能数据不完整
- 如果获取失败，会使用默认值（正常市场，1轮辩论）

### 2. 性能影响

- 市场热度评估增加约2-3秒的初始化时间
- 对整体分析流程影响很小
- 可以通过禁用动态调整来跳过评估

### 3. 兼容性

- 完全向后兼容
- 不影响现有分析流程
- 可以随时启用/禁用

## 🚀 高级用法

### 自定义市场热度阈值

如果你想调整热度阈值（默认60分）：

```python
# 修改 conditional_logic.py 中的阈值
def should_continue_risk_analysis(self, state: AgentState) -> str:
    heat_score = state.get("market_heat_score", 50.0)
    
    # 自定义阈值：70分以上才用2轮
    if heat_score >= 70:  # 原来是60
        max_rounds = 2
    else:
        max_rounds = 1
```

### 自定义热度权重

如果你想调整热度计算的权重：

```python
from tradingagents.agents.utils.market_heat_calculator import MarketHeatCalculator

# 自定义权重
custom_weights = {
    'volume_ratio': 0.30,      # 提高成交量权重
    'limit_up_ratio': 0.25,    # 提高涨停权重
    'turnover_rate': 0.15,
    'market_breadth': 0.15,
    'volatility': 0.10,
    'money_flow': 0.05
}

# 使用自定义权重计算
heat_result = MarketHeatCalculator.calculate_market_heat(
    volume_ratio=2.0,
    limit_up_ratio=0.05,
    # ... 其他参数
    weights=custom_weights
)
```

## 📚 相关文档

- [市场热度计算器](../tradingagents/agents/utils/market_heat_calculator.py)
- [市场热度数据源](../tradingagents/dataflows/market_heat_data.py)
- [市场热度节点](../tradingagents/agents/utils/market_heat_node.py)
- [条件逻辑](../tradingagents/graph/conditional_logic.py)
- [使用指南](./market_heat_guide.md)

## 🎉 总结

市场热度动态风险控制系统已完全集成！现在你的分析系统会：

✅ 自动评估市场热度
✅ 动态调整风险辩论轮次
✅ 根据市场状态调整风险控制策略
✅ 在报告中包含市场热度信息

这解决了"市场热时风险控制失灵"的问题，让系统更智能、更适应不同市场环境！
