# 股票名称和分析时长显示问题修复

## 问题描述

从日志和截图中发现两个问题：
1. **股票名称显示为"未指定"** - 应该显示实际的股票名称（如"寒武纪"）
2. **分析时长显示为"未知"** - 应该显示实际的分析耗时（如"2分39秒"）

## 根本原因

### 1. 股票名称问题
- 后端在获取股票信息时，使用了 `stock_api.get_stock_info()` 函数
- 该函数依赖 `stock_data_service`，当数据源不可用时会返回降级数据 `f'股票{stock_code}'`
- 虽然 AKShare 成功获取了股票信息（日志显示"✅ [股票信息] akshare成功获取688256信息"），但股票名称没有正确传递到最终结果
- MongoDB 数据库中没有保存 `stock_name` 字段
- 前端从多个字段尝试获取股票名称，但都没有正确的值

### 2. 分析时长问题
- MongoDB 文档创建时没有明确设置 `completed_at` 为 `None`
- 前端计算时长时，如果 `createdAt` 或 `completedAt` 无效，会返回"未知"
- 时间戳可能没有正确保存或传递

## 修复方案

### 后端修复 (backend/tradingagents_server.py)

#### 1. 改进股票名称获取
```python
# 直接使用 DataSourceManager 获取股票信息，避免降级
from tradingagents.dataflows.data_source_manager import DataSourceManager
manager = DataSourceManager()
stock_info_result = manager.get_stock_info(stock_symbol)

# 从返回结果中解析股票名称
if 'name' in stock_info_result:
    stock_name = stock_info_result['name']
else:
    # 从字符串结果中解析
    if '股票名称:' in info_str:
        stock_name = line.split(':', 1)[1].strip()
```

#### 2. 在 MongoDB 文档中添加股票名称字段
```python
analysis_doc = {
    "stock_code": request.symbol.upper(),
    "stock_name": None,  # 将在分析完成后更新
    "completed_at": None,  # 明确设置为None
    ...
}
```

#### 3. 分析完成时保存股票名称
```python
update_data = {
    "status": final_status,
    "completed_at": datetime.utcnow()
}

if result.get('success', False):
    update_data["result_data"] = result
    # 从结果中提取股票名称
    if result.get('stock_name'):
        update_data["stock_name"] = result.get('stock_name')
```

#### 4. API 响应中包含股票名称
```python
return {
    "symbol": doc.get("stock_code"),
    "stock_name": doc.get("stock_name"),  # 添加股票名称
    "results": results,
    "created_at": doc.get("created_at"),
    "completed_at": doc.get("completed_at"),
}
```

### 前端修复

#### 1. 更新 Analysis 类型定义 (frontend/src/types/index.ts)
```typescript
export interface Analysis {
  stockCode: string;
  stockName?: string;  // 添加股票名称字段
  createdAt: string;
  completedAt?: string;
  ...
}
```

#### 2. 更新分析服务映射 (frontend/src/services/analysis.ts)
```typescript
// 在 getAnalysisResult 中
return {
  stockCode: response.stock_code || response.symbol,
  stockName: response.stock_name || results?.stock_name,  // 添加股票名称
  ...
}

// 在 getAnalysisHistory 中
const mapped = {
  stockCode: item.stock_code || item.symbol,
  stockName: item.stock_name || item.result_data?.stock_name,  // 添加股票名称
  ...
}
```

#### 3. 优化股票名称显示逻辑 (frontend/src/pages/AnalysisReport/AnalysisReport.tsx)
```typescript
const getStockName = () => {
  // 优先使用 analysis 对象中的 stockName（从数据库获取）
  if (analysis?.stockName && !analysis.stockName.startsWith('股票')) {
    return analysis.stockName;
  }
  // 尝试从结果数据中获取
  if (resultData.stock_name && !resultData.stock_name.startsWith('股票')) {
    return resultData.stock_name;
  }
  // 最后使用股票代码
  return analysis?.stockCode || '未指定';
};
```

## 测试验证

修复后，需要验证：

1. **股票名称显示**
   - 启动新的分析
   - 检查分析报告页面是否显示正确的股票名称（如"寒武纪"而不是"股票688256"或"未指定"）
   - 检查历史记录列表是否显示正确的股票名称

2. **分析时长显示**
   - 完成一次分析
   - 检查分析报告页面的"分析时长"字段是否显示正确的时间（如"2分39秒"而不是"未知"）
   - 验证 `createdAt` 和 `completedAt` 时间戳是否正确保存

3. **数据库验证**
   ```javascript
   // 在 MongoDB 中检查
   db.analyses.findOne({stock_code: "688256"})
   // 应该包含：
   // - stock_name: "寒武纪"
   // - created_at: ISODate(...)
   // - completed_at: ISODate(...)
   ```

## 影响范围

- ✅ 后端：`backend/tradingagents_server.py`
- ✅ 前端类型：`frontend/src/types/index.ts`
- ✅ 前端服务：`frontend/src/services/analysis.ts`
- ✅ 前端页面：`frontend/src/pages/AnalysisReport/AnalysisReport.tsx`

## 注意事项

1. 已存在的分析记录可能没有 `stock_name` 字段，需要兼容处理
2. 股票名称获取失败时，应该显示股票代码而不是"未指定"
3. 时间戳应该使用 UTC 时间，前端显示时转换为本地时间
