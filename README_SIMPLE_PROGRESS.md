# 简单进度跟踪系统

这是一个基于 FastAPI + React 的简单轮询进度跟踪系统，替代原有的 Streamlit WebSocket 方案。

## 核心特点

✅ **简单稳定** - 纯HTTP轮询，没有WebSocket的复杂性  
✅ **容错性强** - 网络断开自动重试，状态持久化  
✅ **易于调试** - 标准HTTP请求，容易排查问题  
✅ **兼容性好** - 支持所有浏览器和网络环境  

## 架构设计

```
前端 (React)     后端 (FastAPI)      存储 (Redis/内存)
     │                  │                    │
     │── 轮询请求 ────→  │                    │
     │                  │── 保存进度 ──────→  │
     │←─── 进度数据 ───── │                    │
     │                  │                    │
     │                  │← 后台线程执行分析    │
```

## 文件结构

```
backend/
├── main.py                          # FastAPI主应用
├── app/
│   ├── api/
│   │   └── analysis.py             # 分析API端点
│   └── services/
│       └── progress_tracker.py     # 进度跟踪服务

frontend/
├── src/
│   ├── components/
│   │   └── SimpleAnalysisProgress.tsx  # 进度组件
│   └── pages/
│       └── AnalysisPage.tsx            # 分析页面
```

## 快速启动

### 1. 启动后端

```bash
cd backend
pip install fastapi uvicorn redis
python main.py
```

后端将在 http://localhost:8000 启动

### 2. 启动前端

```bash
cd frontend
npm install
npm start
```

前端将在 http://localhost:3000 启动

### 3. 测试API

```bash
# 启动分析
curl -X POST "http://localhost:8000/api/analysis/start" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_symbol": "000001",
    "market_type": "A股",
    "analysis_date": "2024-01-01",
    "analysts": ["market", "fundamentals"],
    "research_depth": 2,
    "llm_provider": "dashscope",
    "llm_model": "qwen-plus"
  }'

# 查询进度 (返回的analysis_id)
curl "http://localhost:8000/api/analysis/{analysis_id}/progress"
```

## 核心组件说明

### 1. SimpleProgressTracker (后端)

```python
class SimpleProgressTracker:
    def update_progress(self, message: str, step: Optional[int] = None):
        """更新进度 - 同步方法，简单可靠"""
        
    def _save_progress(self, progress_data: ProgressData):
        """保存到Redis或内存 - 自动fallback"""
        
    def get_progress(self) -> Optional[ProgressData]:
        """获取当前进度"""
```

### 2. SimpleAnalysisProgress (前端)

```typescript
const SimpleAnalysisProgress: React.FC = ({ analysisId }) => {
  // 3秒轮询一次，简单稳定
  useEffect(() => {
    const interval = setInterval(fetchProgress, 3000);
    return () => clearInterval(interval);
  }, []);
}
```

## 与原Streamlit方案对比

| 特性 | Streamlit (原方案) | FastAPI + React (新方案) |
|------|-------------------|-------------------------|
| 实时性 | WebSocket (1-2秒) | HTTP轮询 (3秒) |
| 稳定性 | 连接易断开 | 非常稳定 |
| 复杂度 | 高 (WebSocket管理) | 低 (简单HTTP) |
| 调试难度 | 困难 | 容易 |
| 扩展性 | 受限 | 灵活 |
| 部署复杂度 | 中等 | 简单 |

## 进度数据结构

```typescript
interface ProgressData {
  analysis_id: string;
  current_step: number;           // 当前步骤 (0-based)
  total_steps: number;            // 总步骤数
  progress_percentage: number;    // 进度百分比 (0-1)
  message: string;                // 当前状态消息
  elapsed_time: number;           // 已用时间(秒)
  estimated_remaining: number;    // 预计剩余时间(秒)
  current_step_name: string;      // 当前步骤名称
  timestamp: number;              // 时间戳
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
}
```

## 优势总结

1. **简单可靠** - 没有WebSocket的各种坑
2. **容错性强** - HTTP请求天然支持重试
3. **易于扩展** - 标准REST API，容易集成
4. **调试友好** - 可以直接用curl测试
5. **部署简单** - 不需要特殊的WebSocket配置

这个方案虽然实时性稍差（3秒延迟），但对于股票分析这种长时间任务来说完全够用，而且稳定性和可维护性大大提升。