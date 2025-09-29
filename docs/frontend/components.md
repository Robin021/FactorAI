# 前端组件库文档

## 概述

本文档描述了股票分析平台前端组件库的使用方法和样式指南。组件库基于 React 18 和 TypeScript 构建，使用 Ant Design 作为基础 UI 框架。

## 安装和使用

### 安装依赖

```bash
npm install @stock-analysis/components
```

### 基础使用

```tsx
import React from 'react';
import { StockAnalysisCard, AnalysisProgress } from '@stock-analysis/components';
import '@stock-analysis/components/dist/index.css';

function App() {
  return (
    <div>
      <StockAnalysisCard stockCode="000001" />
      <AnalysisProgress progress={0.75} />
    </div>
  );
}
```

## 核心组件

### 1. StockAnalysisCard - 股票分析卡片

用于展示股票分析结果的卡片组件。

#### Props

```tsx
interface StockAnalysisCardProps {
  stockCode: string;
  stockName?: string;
  analysisResult?: AnalysisResult;
  loading?: boolean;
  onAnalyze?: (stockCode: string) => void;
  onViewDetail?: (analysisId: string) => void;
}
```

#### 使用示例

```tsx
<StockAnalysisCard
  stockCode="000001"
  stockName="平安银行"
  onAnalyze={(code) => console.log('分析', code)}
/>
```

### 2. AnalysisProgress - 分析进度组件

显示股票分析的实时进度。

#### Props

```tsx
interface AnalysisProgressProps {
  progress: number; // 0-1
  status: 'pending' | 'running' | 'completed' | 'failed';
  currentStep?: string;
  onCancel?: () => void;
}
```

### 3. StockSearchInput - 股票搜索输入框

支持股票代码和名称搜索的输入组件。

### 4. ConfigPanel - 配置面板

用于 LLM 和数据源配置的面板组件。

### 5. AnalysisHistory - 分析历史

展示历史分析记录的表格组件。

## 主题定制

### CSS 变量

```css
:root {
  --primary-color: #1890ff;
  --success-color: #52c41a;
  --warning-color: #faad14;
  --error-color: #f5222d;
}
```

## 响应式设计

组件库支持响应式设计，使用断点：

- 手机: < 576px
- 平板: 576px - 768px  
- 桌面: > 768px

## 最佳实践

1. 使用 TypeScript 获得更好的类型安全
2. 遵循组件单一职责原则
3. 合理使用 React.memo 优化性能
4. 提供完整的 props 接口定义