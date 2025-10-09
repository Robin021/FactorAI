# 🔧 React Hooks 错误修复

## 🚨 错误信息
```
Error: Rendered more hooks than during the previous render.
```

## 🔍 问题分析

这个错误通常由以下原因引起：
1. **条件性hooks使用** - 在if语句中使用hooks
2. **hooks顺序变化** - 不同渲染周期中hooks的数量或顺序不同
3. **依赖数组问题** - useEffect依赖导致的循环渲染

## 🔧 修复内容

### 1. 移除调试useEffect
```typescript
// ❌ 删除了这个可能导致hooks顺序问题的调试代码
React.useEffect(() => {
  if (progressData) {
    console.log('🔍 [SevenStepProgress] 接收到的进度数据:', progressData);
  }
}, [progressData]);
```

### 2. 简化轮询逻辑
```typescript
// ✅ 修复前 - 复杂的轮询逻辑，可能导致依赖问题
useEffect(() => {
  const startPolling = () => {
    intervalRef.current = setInterval(() => {
      if (progressData?.status === 'running') { // 这里使用了progressData但不在依赖中
        fetchProgress();
      }
    }, 1000);
  };
  // ...
}, [analysisId]); // progressData不在依赖中，可能导致问题

// ✅ 修复后 - 简化的轮询逻辑
useEffect(() => {
  fetchProgressRef.current();
  
  intervalRef.current = setInterval(() => {
    fetchProgressRef.current(); // 使用ref避免依赖问题
  }, 1000);

  return () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };
}, [analysisId]); // 只依赖analysisId

// 单独监听状态变化
useEffect(() => {
  if (progressData?.status === 'completed' || progressData?.status === 'failed') {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }
}, [progressData?.status]);
```

## 🎯 修复原理

### 1. Hooks规则遵循
- **固定顺序**: 确保每次渲染时hooks的调用顺序相同
- **无条件调用**: 不在条件语句中使用hooks
- **依赖正确**: useEffect的依赖数组包含所有使用的变量

### 2. 使用Ref避免循环依赖
```typescript
const fetchProgressRef = useRef(fetchProgress);
fetchProgressRef.current = fetchProgress;

// 在useEffect中使用ref而不是直接使用函数
useEffect(() => {
  fetchProgressRef.current(); // ✅ 避免将fetchProgress加入依赖
}, [analysisId]);
```

### 3. 分离关注点
- **轮询逻辑**: 只负责定时调用
- **状态监听**: 单独监听状态变化并停止轮询

## 🧪 验证修复

### 检查点
- [ ] 页面刷新后不再出现hooks错误
- [ ] 进度轮询正常工作
- [ ] 分析完成后轮询正确停止
- [ ] 浏览器控制台无错误信息

### 测试步骤
1. 访问 `/analysis` 页面
2. 启动新的分析任务
3. 观察实时进度是否正常更新
4. 等待分析完成，确认轮询停止

## 📚 React Hooks 最佳实践

### 1. 始终遵循Hooks规则
```typescript
// ❌ 错误 - 条件性使用hooks
if (condition) {
  useEffect(() => {}, []);
}

// ✅ 正确 - 在hooks内部使用条件
useEffect(() => {
  if (condition) {
    // 执行逻辑
  }
}, [condition]);
```

### 2. 正确处理依赖
```typescript
// ❌ 错误 - 遗漏依赖
useEffect(() => {
  doSomething(value); // value应该在依赖中
}, []);

// ✅ 正确 - 包含所有依赖
useEffect(() => {
  doSomething(value);
}, [value]);
```

### 3. 使用Ref避免复杂依赖
```typescript
// ✅ 使用ref存储最新的函数引用
const callbackRef = useRef(callback);
callbackRef.current = callback;

useEffect(() => {
  callbackRef.current(); // 避免将callback加入依赖
}, [otherDeps]);
```

---

**修复完成！现在SevenStepProgress组件应该不会再出现hooks错误。** 🎉