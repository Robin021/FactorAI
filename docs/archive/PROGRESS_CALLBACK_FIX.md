# Progress Callback 参数修复

## 问题描述
```
2025-10-09 21:14:06,368 | backend.tradingagents_server | ERROR | ❌ 分析执行失败: start_real_analysis.<locals>.analysis_worker.<locals>.progress_callback() missing 1 required positional argument: 'total_steps'
```

## 根本原因
TradingAgents 内部调用 `progress_callback` 时只传递两个参数：
```python
# TradingAgents 源码中的调用
self.progress_callback("🔍 开始识别股票类型并获取基本信息", 0)
self.progress_callback(f"✅ 股票识别完成: {market_info['market_name']} - {company_name}", 0)
```

但我们的函数定义期望三个参数：
```python
def progress_callback(message, step, total_steps):  # ❌ 不兼容
```

## 修复方案 ✅

**修复前**:
```python
def progress_callback(message, step, total_steps):
```

**修复后**:
```python
def progress_callback(message, step=0, total_steps=7):
```

## 兼容性说明

现在 `progress_callback` 函数支持两种调用方式：

1. **TradingAgents 内部调用** (2个参数):
   ```python
   progress_callback("🔍 开始识别股票类型并获取基本信息", 0)
   # step=0, total_steps=7 (默认值)
   ```

2. **我们的手动调用** (3个参数):
   ```python
   progress_callback("✅ 分析完成，正在整理结果", 6, 7)
   # 明确指定所有参数
   ```

## 验证
- ✅ 兼容 TradingAgents 的两参数调用
- ✅ 支持我们的三参数调用
- ✅ 默认值确保向后兼容
- ✅ 错误处理保持不变

## 结果
现在 TradingAgents 分析可以正常运行，不会再出现参数缺失错误。