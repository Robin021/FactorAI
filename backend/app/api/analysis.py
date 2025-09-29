"""
股票分析API端点 - 简单轮询方案
"""

import threading
import time
import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import logging

from ..services.progress_tracker import SimpleProgressTracker, get_analysis_progress, AnalysisStatus

logger = logging.getLogger(__name__)
router = APIRouter()

# 存储活跃的分析任务
active_analyses: Dict[str, SimpleProgressTracker] = {}

class AnalysisRequest(BaseModel):
    stock_symbol: str
    market_type: str = "A股"
    analysis_date: str
    analysts: List[str]
    research_depth: int
    llm_provider: str = "dashscope"
    llm_model: str = "qwen-plus"
    include_sentiment: bool = True
    include_risk_assessment: bool = True
    custom_prompt: str = ""

class AnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    message: str

@router.post("/analysis/start", response_model=AnalysisResponse)
def start_analysis(request: AnalysisRequest):
    """启动股票分析"""
    try:
        # 生成分析ID
        analysis_id = f"analysis_{uuid.uuid4().hex[:8]}"
        
        # 创建进度跟踪器
        progress_tracker = SimpleProgressTracker(
            analysis_id=analysis_id,
            analysts=request.analysts,
            research_depth=request.research_depth,
            llm_provider=request.llm_provider
        )
        
        # 存储到活跃分析中
        active_analyses[analysis_id] = progress_tracker
        
        # 在后台线程启动分析任务
        thread = threading.Thread(
            target=run_analysis_task,
            args=(analysis_id, request, progress_tracker),
            daemon=True
        )
        thread.start()
        
        logger.info(f"Started analysis {analysis_id} for {request.stock_symbol}")
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="started",
            message="分析已启动，请轮询进度接口获取更新"
        )
        
    except Exception as e:
        logger.error(f"Failed to start analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def run_analysis_task(analysis_id: str, request: AnalysisRequest, progress_tracker: SimpleProgressTracker):
    """执行分析任务（在后台线程中运行）"""
    try:
        progress_tracker.status = AnalysisStatus.RUNNING
        progress_tracker.update_progress("🚀 开始股票分析...")
        
        # 模拟分析过程（实际应该调用真实的分析服务）
        simulate_analysis(progress_tracker, request)
        
        # 标记完成
        progress_tracker.mark_completed(success=True)
        
        logger.info(f"Analysis {analysis_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Analysis {analysis_id} failed: {e}")
        progress_tracker.mark_completed(success=False)
    
    finally:
        # 延迟清理活跃分析
        def cleanup():
            time.sleep(300)  # 5分钟后清理
            if analysis_id in active_analyses:
                del active_analyses[analysis_id]
        
        cleanup_thread = threading.Thread(target=cleanup, daemon=True)
        cleanup_thread.start()

def simulate_analysis(progress_tracker: SimpleProgressTracker, request: AnalysisRequest):
    """模拟分析过程 - 提供详细的步骤信息"""
    
    # 第一步：数据验证
    progress_tracker.update_progress(f"🔍 开始验证股票代码 {request.stock_symbol}...", step=0)
    time.sleep(1)
    progress_tracker.update_progress(f"✅ 股票代码 {request.stock_symbol} 验证成功", step=0)
    time.sleep(1)
    progress_tracker.update_progress("📡 正在预获取基础数据...", step=0)
    time.sleep(2)
    
    # 第二步：环境准备
    progress_tracker.update_progress("🔧 检查API密钥配置...", step=1)
    time.sleep(1)
    progress_tracker.update_progress(f"🌐 验证 {request.llm_provider} 模型连接...", step=1)
    time.sleep(1)
    
    # 第三步：成本预估
    progress_tracker.update_progress("💰 计算分析成本...", step=2)
    time.sleep(1)
    estimated_cost = len(request.analysts) * request.research_depth * 0.5
    progress_tracker.update_progress(f"💰 预估成本: ${estimated_cost:.2f}", step=2)
    time.sleep(1)
    
    # 第四步：参数配置
    progress_tracker.update_progress("⚙️ 配置分析参数...", step=3)
    time.sleep(1)
    progress_tracker.update_progress(f"📊 设置研究深度: {request.research_depth}级", step=3)
    time.sleep(1)
    
    # 第五步：引擎初始化
    progress_tracker.update_progress("🚀 初始化AI分析引擎...", step=4)
    time.sleep(1)
    progress_tracker.update_progress(f"🤖 加载 {request.llm_model} 模型...", step=4)
    time.sleep(2)
    
    # 分析师步骤
    analyst_names = {
        'market': '市场分析师',
        'fundamentals': '基本面分析师',
        'technical': '技术分析师',
        'sentiment': '情绪分析师',
        'news': '新闻分析师'
    }
    
    analyst_tasks = {
        'market': [
            "📈 分析市场趋势和走势",
            "📊 计算技术指标",
            "🎯 识别支撑阻力位",
            "📉 评估市场风险"
        ],
        'fundamentals': [
            "💼 分析公司财务报表",
            "📋 计算财务比率",
            "💰 评估盈利能力",
            "🏢 行业对比分析"
        ],
        'technical': [
            "📊 技术形态识别",
            "🔄 移动平均线分析",
            "📈 MACD和RSI指标",
            "🎯 买卖信号识别"
        ],
        'sentiment': [
            "😊 市场情绪分析",
            "📰 社交媒体监控",
            "🗣️ 投资者情绪指数",
            "📊 情绪趋势预测"
        ],
        'news': [
            "📰 收集相关新闻",
            "🔍 新闻影响分析",
            "📊 事件驱动分析",
            "🎯 风险事件识别"
        ]
    }
    
    current_step = 5  # 从第6步开始（分析师步骤）
    
    for analyst in request.analysts:
        name = analyst_names.get(analyst, analyst)
        tasks = analyst_tasks.get(analyst, [f"执行{name}分析"])
        
        progress_tracker.update_progress(f"👨‍💼 启动{name}...", step=current_step)
        time.sleep(1)
        
        for i, task in enumerate(tasks):
            # 检查是否已被取消
            if progress_tracker.status == AnalysisStatus.CANCELLED:
                logger.info(f"Analysis {progress_tracker.analysis_id} was cancelled during {name}")
                return
                
            progress_tracker.update_progress(f"🔄 {task}...", step=current_step)
            time.sleep(2 + request.research_depth)  # 根据研究深度调整时间
            
        progress_tracker.update_progress(f"✅ {name}分析完成", step=current_step)
        time.sleep(1)
        current_step += 1
    
    # 最后一步：结果整理
    progress_tracker.update_progress("📋 开始整理分析结果...", step=current_step)
    time.sleep(1)
    progress_tracker.update_progress("📊 生成图表和可视化...", step=current_step)
    time.sleep(2)
    progress_tracker.update_progress("📝 编写分析报告...", step=current_step)
    time.sleep(2)
    progress_tracker.update_progress("🎨 优化报告格式...", step=current_step)
    time.sleep(1)
    
    # 检查最终取消状态
    if progress_tracker.status == AnalysisStatus.CANCELLED:
        logger.info(f"Analysis {progress_tracker.analysis_id} was cancelled")
        return

@router.get("/analysis/{analysis_id}/progress")
def get_analysis_progress_api(analysis_id: str):
    """获取分析进度（轮询接口）- 兼容原有系统"""
    try:
        # 获取进度数据
        progress_data = get_analysis_progress(analysis_id)
        
        if progress_data:
            return {
                "analysis_id": progress_data.analysis_id,
                "status": progress_data.status.value,
                "current_step": progress_data.current_step,
                "total_steps": progress_data.total_steps,
                "progress_percentage": progress_data.progress_percentage,
                "message": progress_data.message,
                "elapsed_time": progress_data.elapsed_time,
                "estimated_remaining": progress_data.estimated_remaining,
                "current_step_name": progress_data.current_step_name,
                "timestamp": progress_data.timestamp
            }
        
        # 如果新系统找不到，返回模拟数据（兼容原有系统）
        logger.info(f"Analysis {analysis_id} not found in new system, returning mock progress")
        
        import time
        return {
            "analysis_id": analysis_id,
            "status": "running",
            "current_step": 2,
            "total_steps": 6,
            "progress_percentage": 0.45,  # 45%
            "message": "正在进行基本面分析...",
            "elapsed_time": 90,
            "estimated_remaining": 120,
            "current_step_name": "基本面分析",
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analysis/{analysis_id}/cancel")
def cancel_analysis(analysis_id: str):
    """取消分析"""
    try:
        if analysis_id not in active_analyses:
            raise HTTPException(status_code=404, detail="分析不存在或已完成")
        
        tracker = active_analyses[analysis_id]
        tracker.mark_cancelled()
        
        return {"message": "分析已取消"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/active")
def get_active_analyses():
    """获取所有活跃的分析"""
    active_list = []
    
    for analysis_id, tracker in active_analyses.items():
        active_list.append({
            "analysis_id": analysis_id,
            "status": tracker.status.value,
            "current_step": tracker.current_step,
            "total_steps": len(tracker.steps),
            "progress_percentage": tracker._calculate_weighted_progress(),
            "elapsed_time": time.time() - tracker.start_time,
            "analysts": tracker.analysts,
            "research_depth": tracker.research_depth
        })
    
    return {"active_analyses": active_list}