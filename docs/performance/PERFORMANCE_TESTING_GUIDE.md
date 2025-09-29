# 性能测试和优化指南

本文档描述了 TradingAgents 项目的性能测试和优化策略。

## 概述

我们的性能测试策略包括四个主要方面：

1. **API 接口性能测试** - 测试后端 API 的响应时间和吞吐量
2. **并发分析任务压力测试** - 测试系统在高并发分析任务下的表现
3. **前端资源加载和渲染性能优化** - 优化前端加载速度和用户体验
4. **性能监控和报警机制** - 实时监控系统性能并及时报警

## 快速开始

### 运行所有性能测试

```bash
# 运行完整的性能测试套件
python scripts/performance/run_performance_tests.py --all

# 或者分别运行不同类型的测试
python scripts/performance/run_performance_tests.py --backend
python scripts/performance/run_performance_tests.py --frontend  
python scripts/performance/run_performance_tests.py --load
```

### 查看性能监控

```bash
# 启动后端服务
cd backend && uvicorn app.main:app --reload

# 访问性能监控页面
# http://localhost:3000/performance
```

## 详细说明

### 1. API 接口性能测试

#### 测试工具
- **pytest-benchmark**: 用于微基准测试
- **httpx**: 异步 HTTP 客户端测试
- **memory-profiler**: 内存使用分析

#### 测试内容
- 登录接口响应时间
- 分析启动接口性能
- 配置获取接口性能
- 并发请求处理能力
- 内存使用情况

#### 运行测试
```bash
# 安装依赖
pip install -r backend/requirements-dev.txt

# 运行性能测试
pytest backend/tests/performance/test_api_performance.py --benchmark-only

# 生成详细报告
pytest backend/tests/performance/test_api_performance.py \
  --benchmark-json=performance_results/api_benchmark.json \
  --benchmark-columns=min,max,mean,stddev,rounds,iterations
```

#### 性能指标
- **响应时间**: API 接口平均响应时间应 < 200ms
- **并发处理**: 支持至少 50 个并发请求
- **成功率**: 95% 以上的请求成功率
- **内存使用**: 内存增长 < 50MB/1000 请求

### 2. 并发分析任务压力测试

#### 测试工具
- **Locust**: 分布式负载测试工具
- **自定义压力测试脚本**: 针对分析任务的专门测试

#### 测试场景
- **峰值测试**: 100 用户，50 用户/秒启动速率，持续 2 分钟
- **耐久性测试**: 20 用户，2 用户/秒启动速率，持续 10 分钟
- **并发分析测试**: 50 用户同时启动分析任务，持续 5 分钟

#### 运行测试
```bash
# 安装 Locust
pip install locust

# 运行单个测试场景
locust -f backend/tests/performance/locustfile.py \
  --host http://localhost:8000 \
  --users 50 --spawn-rate 10 --run-time 5m \
  --headless --html performance_results/load_test.html

# 运行完整压力测试套件
python backend/tests/performance/stress_test_runner.py --host http://localhost:8000
```

#### 性能目标
- **吞吐量**: 每秒处理 ≥ 10 个分析请求
- **响应时间**: 95% 的请求在 5 秒内完成
- **错误率**: < 5% 的请求失败
- **资源使用**: CPU < 80%, 内存 < 85%

### 3. 前端性能优化

#### 优化策略

##### 资源加载优化
- **代码分割**: 按路由和功能模块分割代码
- **懒加载**: 图片和非关键组件懒加载
- **预加载**: 关键资源预加载
- **缓存策略**: 合理的缓存头设置

##### 渲染性能优化
- **虚拟滚动**: 大列表使用虚拟滚动
- **防抖节流**: 高频事件使用防抖和节流
- **内存管理**: 避免内存泄漏
- **组件优化**: React.memo 和 useMemo 优化

#### 构建优化
```bash
# 使用性能优化配置构建
npm run build -- --config vite.config.performance.ts

# 分析构建结果
npm run build:analyze

# 运行 Lighthouse 审计
npm run lighthouse
```

#### 性能指标
- **首次内容绘制 (FCP)**: < 2 秒
- **最大内容绘制 (LCP)**: < 4 秒
- **首次输入延迟 (FID)**: < 100ms
- **累积布局偏移 (CLS)**: < 0.25
- **构建大小**: < 10MB

### 4. 性能监控和报警

#### 监控指标

##### 系统指标
- CPU 使用率
- 内存使用率
- 磁盘使用率
- 网络 I/O

##### 应用指标
- API 响应时间
- 请求成功率
- 活跃用户数
- 分析任务队列长度

##### 前端指标
- 页面加载时间
- 用户交互响应时间
- JavaScript 错误率
- 资源加载失败率

#### 报警规则

```python
# 默认报警规则
alert_rules = [
    {
        "name": "High CPU Usage",
        "metric": "system.cpu.usage",
        "threshold": 80,  # 80%
        "duration": 300,  # 5分钟
        "severity": "high"
    },
    {
        "name": "High Memory Usage",
        "metric": "system.memory.usage", 
        "threshold": 85,  # 85%
        "duration": 300,  # 5分钟
        "severity": "high"
    },
    {
        "name": "Slow API Response",
        "metric": "api.response_time.avg",
        "threshold": 5000,  # 5秒
        "duration": 60,   # 1分钟
        "severity": "medium"
    }
]
```

#### 启动监控
```python
# 在应用启动时启动性能监控
from backend.app.monitoring.performance_monitor import performance_monitor

# 启动监控
await performance_monitor.start_monitoring()

# 添加自定义报警规则
performance_monitor.alert_manager.add_rule(custom_rule)
```

## 性能测试最佳实践

### 1. 测试环境
- 使用与生产环境相似的硬件配置
- 确保网络条件稳定
- 隔离其他应用程序的影响

### 2. 测试数据
- 使用真实的数据量级
- 模拟真实的用户行为模式
- 包含边界情况和异常情况

### 3. 测试执行
- 预热系统后再开始正式测试
- 多次运行取平均值
- 记录详细的测试环境信息

### 4. 结果分析
- 关注平均值、95分位数、99分位数
- 分析性能瓶颈的根本原因
- 制定具体的优化计划

## 持续集成

### GitHub Actions 配置

```yaml
name: Performance Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  performance:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Install dependencies
      run: |
        pip install -r backend/requirements-dev.txt
        cd frontend && npm install
    
    - name: Run performance tests
      run: |
        python scripts/performance/run_performance_tests.py --all
    
    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: performance-results
        path: performance_results/
```

## 故障排除

### 常见问题

1. **测试超时**
   - 检查网络连接
   - 增加超时时间
   - 检查系统资源

2. **内存不足**
   - 减少并发用户数
   - 检查内存泄漏
   - 增加系统内存

3. **测试不稳定**
   - 检查系统负载
   - 使用固定的测试数据
   - 增加测试重试次数

### 性能调优建议

1. **数据库优化**
   - 添加适当的索引
   - 优化查询语句
   - 使用连接池

2. **缓存策略**
   - Redis 缓存热点数据
   - HTTP 缓存静态资源
   - 应用层缓存计算结果

3. **异步处理**
   - 使用异步 I/O
   - 任务队列处理耗时操作
   - 批量处理减少开销

## 参考资料

- [Locust 文档](https://docs.locust.io/)
- [pytest-benchmark 文档](https://pytest-benchmark.readthedocs.io/)
- [Lighthouse 性能审计](https://developers.google.com/web/tools/lighthouse)
- [Web Vitals 指标](https://web.dev/vitals/)
- [FastAPI 性能优化](https://fastapi.tiangolo.com/advanced/performance/)