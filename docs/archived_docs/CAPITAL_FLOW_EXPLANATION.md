# 资金流向和融资融券数据说明

## 为什么数据是 0？

### 1. 北向资金 (Northbound Capital Flow) = 0.0

**原因**: 股票 688256 (寒武纪) 是**科创板股票**

```python
# 代码逻辑
if ticker.startswith('688'):
    logger.info(f"⚠️ 科创板股票 {ticker} 不支持北向资金，返回中性评分")
    return 0.0
```

**解释**:
- 科创板股票（688xxx）不在沪深港通标的范围内
- 只有主板、中小板、创业板的部分股票才有北向资金数据
- 这是**正常现象**，不是bug

**哪些股票有北向资金数据**:
- 上证主板: 600xxx, 601xxx, 603xxx, 605xxx
- 深证主板: 000xxx, 001xxx
- 创业板: 300xxx (部分)
- 科创板: 688xxx ❌ **没有**
- 北交所: 8xxxxx ❌ **没有**

### 2. 融资融券 (Margin Trading) = 0.0

**原因**: 未配置 TuShare Token

```
2025-10-29 13:00:18,811 | sentiment_data_sources | WARNING | TuShare不可用，使用AKShare市场整体数据
2025-10-29 13:00:21,097 | sentiment_data_sources | INFO | 使用市场整体融资融券数据（降级）
```

**解释**:
- 融资融券数据需要 TuShare Pro API
- 如果没有配置 Token，系统会使用降级方案
- 当前降级方案只返回市场整体数据，评分为 0.0

## 解决方案

### 方案1: 配置 TuShare Token (推荐)

1. 注册 TuShare 账号: https://tushare.pro/register
2. 获取 Token: https://tushare.pro/user/token
3. 配置环境变量:

```bash
export TUSHARE_TOKEN="your_token_here"
```

或在代码中配置:

```python
# tradingagents/config/settings.py
TUSHARE_TOKEN = "your_token_here"
```

### 方案2: 改进 AKShare 降级方案

使用 AKShare 获取个股融资融券数据（不需要 Token）:

```python
def _get_margin_trading_fallback(self, ticker: str, date: str) -> float:
    """改进的融资融券降级方案"""
    try:
        import akshare as ak
        
        # 使用 AKShare 获取个股融资融券数据
        # 注意：AKShare 的融资融券接口可能有限制
        df = ak.stock_margin_detail_sse(symbol=ticker)
        
        if df is not None and not df.empty:
            # 获取最新的融资融券余额
            latest = df.iloc[-1]
            rzye = latest.get('融资余额', 0)  # 融资余额
            
            # 计算情绪评分
            # 融资余额越高，说明看多情绪越强
            if rzye > 0:
                # 归一化：假设10亿为中等水平
                sentiment = min(rzye / 1000000000 * 0.5, 1.0)
                logger.info(f"✅ 融资融券评分: {sentiment:.3f} (融资余额: {rzye/100000000:.2f}亿)")
                return sentiment
        
        logger.warning("无法获取融资融券数据，返回中性评分")
        return 0.0
        
    except Exception as e:
        logger.error(f"降级方案失败: {e}")
        return 0.0
```

### 方案3: 使用替代指标

对于科创板股票，可以使用其他指标替代：

1. **机构持仓变化** (替代北向资金)
   - 通过季报数据分析机构持仓变化
   - 反映机构投资者的态度

2. **大单净流入** (替代北向资金)
   - 分析大单（如 > 100万）的净流入情况
   - 反映大资金的动向

3. **融资融券比例** (改进融资融券)
   - 融资买入额 / 成交额
   - 反映杠杆资金的参与度

## 当前影响

### 对评分的影响

使用新权重配置：
```python
WEIGHTS = {
    'news': 0.20,           # 20%
    'money_flow': 0.20,     # 20% ← 北向资金 (688256 = 0)
    'volatility': 0.15,     # 15%
    'technical': 0.20,      # 20%
    'volume': 0.15,         # 15%
    'social': 0.05,         # 5%
    'margin': 0.05          # 5% ← 融资融券 (688256 = 0)
}
```

对于 688256:
- 北向资金 (20%) = 0 → 贡献 0
- 融资融券 (5%) = 0 → 贡献 0
- 总共损失 25% 的权重信息

### 实际计算

```
有效权重 = 0.20 (news) + 0.15 (volatility) + 0.20 (technical) + 0.15 (volume)
         = 0.70 (70%)

缺失权重 = 0.20 (money_flow) + 0.05 (margin)
         = 0.25 (25%)
```

这意味着对于科创板股票，评分主要依赖：
- 新闻情绪 (20%)
- 技术动量 (20%)
- 成交量 (15%)
- 波动率 (15%)

## 建议

### 短期建议
1. 接受科创板没有北向资金是正常现象
2. 配置 TuShare Token 以获取融资融券数据
3. 或者实现改进的 AKShare 降级方案

### 长期建议
1. 为不同板块设计不同的权重配置：
   ```python
   # 主板/中小板/创业板
   WEIGHTS_STANDARD = {
       'news': 0.20,
       'money_flow': 0.20,    # 有北向资金
       'volatility': 0.15,
       'technical': 0.20,
       'volume': 0.15,
       'margin': 0.05,
       'social': 0.05
   }
   
   # 科创板
   WEIGHTS_STAR_MARKET = {
       'news': 0.25,          # 提高新闻权重
       'money_flow': 0.0,     # 无北向资金
       'volatility': 0.20,    # 提高波动率权重
       'technical': 0.25,     # 提高技术权重
       'volume': 0.20,        # 提高成交量权重
       'margin': 0.05,
       'social': 0.05
   }
   ```

2. 添加科创板特有指标：
   - 机构调研次数
   - 研发投入占比
   - 专利数量变化
   - 科创属性评分

## 测试验证

测试不同板块的股票：

```bash
# 主板股票 (有北向资金)
python test_sentiment_quick.py 600519  # 贵州茅台

# 科创板股票 (无北向资金)
python test_sentiment_quick.py 688256  # 寒武纪

# 创业板股票 (部分有北向资金)
python test_sentiment_quick.py 300750  # 宁德时代
```
