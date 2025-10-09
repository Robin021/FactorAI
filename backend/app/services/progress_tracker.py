"""
简单进度跟踪服务 - 轮询方案
"""

import time
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import redis
import logging

logger = logging.getLogger(__name__)

class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ProgressStep:
    name: str
    description: str
    weight: float
    status: str = "pending"  # pending, running, completed, failed

@dataclass
class ProgressData:
    analysis_id: str
    current_step: int
    total_steps: int
    progress_percentage: float
    message: str
    elapsed_time: float
    estimated_remaining: float
    current_step_name: str
    timestamp: float
    status: AnalysisStatus
    step_results: Dict[str, Any] = None  # 存储每个步骤的结果

class SimpleProgressTracker:
    """简单进度跟踪器 - 轮询方案"""
    
    def __init__(self, analysis_id: str, analysts: List[str], research_depth: int, 
                 llm_provider: str):
        self.analysis_id = analysis_id
        self.analysts = analysts
        self.research_depth = research_depth
        self.llm_provider = llm_provider
        
        self.start_time = time.time()
        self.current_step = 0
        self.status = AnalysisStatus.PENDING
        
        # 动态生成分析步骤
        self.steps = self._generate_dynamic_steps()
        self.estimated_duration = self._estimate_total_duration()
        
        # Redis连接用于状态持久化
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            # 测试连接
            self.redis_client.ping()
            self.use_redis = True
        except:
            logger.warning("Redis连接失败，使用内存存储")
            self.use_redis = False
            # 使用类变量作为内存存储
            if not hasattr(SimpleProgressTracker, '_memory_store'):
                SimpleProgressTracker._memory_store = {}
        
    def _generate_dynamic_steps(self) -> List[ProgressStep]:
        """根据实际分析流程生成7个真实步骤"""
        # 真实的7步分析流程
        steps = [
            ProgressStep("股票识别", "🔍 识别股票类型并获取基本信息", 0.10),
            ProgressStep("市场分析", "📈 技术指标分析和价格走势研究", 0.15),
            ProgressStep("基本面分析", "📊 财务数据分析和估值评估", 0.15),
            ProgressStep("新闻分析", "📰 新闻事件影响和行业动态分析", 0.10),
            ProgressStep("情绪分析", "💭 社交媒体情绪和市场热度分析", 0.10),
            ProgressStep("投资辩论", "⚖️ 多空观点辩论和投资决策制定", 0.25),
            ProgressStep("风险评估", "🛡️ 风险管理评估和最终决策优化", 0.15),
        ]
        
        return steps
    
    def _estimate_total_duration(self) -> float:
        """预估总时长（秒）"""
        base_time = 60
        
        analyst_base_time = {
            1: 120,  # 快速分析
            2: 180,  # 基础分析  
            3: 240   # 标准分析
        }.get(self.research_depth, 180)
        
        analyst_time = len(self.analysts) * analyst_base_time
        
        model_multiplier = {
            'dashscope': 1.0,
            'deepseek': 0.7,
            'google': 1.3
        }.get(self.llm_provider, 1.0)
        
        depth_multiplier = {
            1: 0.8,
            2: 1.0, 
            3: 1.3
        }.get(self.research_depth, 1.0)
        
        return (base_time + analyst_time) * model_multiplier * depth_multiplier
    
    def update_progress(self, message: str, step: Optional[int] = None):
        """更新进度"""
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        
        # 智能步骤检测
        if step is None:
            step = self._detect_step_from_message(message)
        
        if step is not None and step >= self.current_step:
            self.current_step = step
            if step < len(self.steps):
                self.steps[step].status = "running"
        
        # 计算进度百分比
        progress_percentage = self._calculate_weighted_progress()
        
        # 预估剩余时间
        remaining_time = self._estimate_remaining_time(progress_percentage, elapsed_time)
        
        # 创建进度数据
        progress_data = ProgressData(
            analysis_id=self.analysis_id,
            current_step=self.current_step,
            total_steps=len(self.steps),
            progress_percentage=progress_percentage,
            message=message,
            elapsed_time=elapsed_time,
            estimated_remaining=remaining_time,
            current_step_name=self.steps[self.current_step].name if self.current_step < len(self.steps) else "完成",
            timestamp=current_time,
            status=self.status
        )
        
        # 保存进度
        self._save_progress(progress_data)
        
        logger.info(f"Progress updated for {self.analysis_id}: {progress_percentage:.1%} - {message}")
    
    def update_step_result(self, step_name: str, result_data: Dict[str, Any]):
        """更新步骤结果"""
        # 获取当前进度数据
        current_progress = self.get_progress()
        if current_progress:
            if current_progress.step_results is None:
                current_progress.step_results = {}
            current_progress.step_results[step_name] = result_data
            self._save_progress(current_progress)
            logger.info(f"Step result updated for {self.analysis_id}: {step_name}")
    
    def complete_step(self, step_index: int, result_summary: str, detailed_result: Dict[str, Any] = None):
        """完成一个步骤并保存结果"""
        if step_index < len(self.steps):
            self.steps[step_index].status = "completed"
            step_name = self.steps[step_index].name
            
            # 更新进度
            progress_percentage = self._calculate_weighted_progress()
            message = f"✅ {step_name}完成: {result_summary}"
            
            self.update_progress(message, step_index + 1)  # 移动到下一步
            
            # 保存步骤结果
            if detailed_result:
                self.update_step_result(step_name, {
                    "summary": result_summary,
                    "details": detailed_result,
                    "completed_at": time.time()
                })
    
    def _detect_step_from_message(self, message: str) -> Optional[int]:
        """智能检测当前步骤 - 基于真实分析流程"""
        message_lower = message.lower()
        
        # 优先匹配更具体的关键词，避免误判
        
        # 步骤1: 市场分析 (优先检测，避免被步骤0误判)
        if any(keyword in message for keyword in ["市场分析师开始", "市场分析师完成", "Market Analyst", "技术指标分析", "价格走势研究"]):
            return 1
        
        # 步骤2: 基本面分析  
        elif any(keyword in message for keyword in ["基本面分析师开始", "基本面分析师完成", "Fundamentals Analyst", "财务数据分析", "估值评估"]):
            return 2
        
        # 步骤3: 新闻分析
        elif any(keyword in message for keyword in ["新闻分析师开始", "新闻分析师完成", "News Analyst", "新闻事件影响", "行业动态分析"]):
            return 3
        
        # 步骤4: 情绪分析
        elif any(keyword in message for keyword in ["社交媒体分析师开始", "社交媒体分析师完成", "Social Media Analyst", "情绪分析", "市场热度分析"]):
            return 4
        
        # 步骤5: 投资辩论
        elif any(keyword in message for keyword in ["Bull Researcher", "Bear Researcher", "Research Manager", "投资辩论", "多空观点", "投资决策制定"]):
            return 5
        
        # 步骤6: 风险评估
        elif any(keyword in message for keyword in ["Risk Judge", "Risky Analyst", "Safe Analyst", "Neutral Analyst", "风险管理", "风险评估", "最终决策优化"]):
            return 6
        
        # 步骤0: 股票识别 (放在后面，避免过度匹配)
        elif any(keyword in message for keyword in ["股票识别", "识别股票类型", "获取基本信息", "开始分析"]):
            return 0
        
        # 分析完成 - 设置为最后一步
        elif any(keyword in message for keyword in ["分析成功完成", "✅ 分析", "分析结束"]):
            return len(self.steps) - 1
            
        return None
    
    def _calculate_weighted_progress(self) -> float:
        """根据步骤权重计算进度"""
        if self.current_step >= len(self.steps):
            return 1.0
            
        # 计算已完成步骤的权重 + 当前步骤的权重
        completed_weight = sum(step.weight for step in self.steps[:self.current_step])
        if self.current_step < len(self.steps):
            # 当前步骤也算作已完成的权重
            completed_weight += self.steps[self.current_step].weight
            
        total_weight = sum(step.weight for step in self.steps)
        
        return min(completed_weight / total_weight, 1.0)
    
    def _estimate_remaining_time(self, progress: float, elapsed_time: float) -> float:
        """预估剩余时间"""
        if progress <= 0:
            return self.estimated_duration
            
        if progress > 0.2:
            estimated_total = elapsed_time / progress
            return max(estimated_total - elapsed_time, 0)
        else:
            return max(self.estimated_duration - elapsed_time, 0)
    
    def _save_progress(self, progress_data: ProgressData):
        """保存进度数据"""
        key = f"analysis_progress:{self.analysis_id}"
        data = asdict(progress_data)
        
        if self.use_redis:
            try:
                # 保存到Redis，1小时过期
                self.redis_client.setex(key, 3600, json.dumps(data, default=str))
            except Exception as e:
                logger.error(f"Failed to save progress to Redis: {e}")
                # Redis失败时fallback到内存
                SimpleProgressTracker._memory_store[key] = data
        else:
            # 保存到内存
            SimpleProgressTracker._memory_store[key] = data
    
    def get_progress(self) -> Optional[ProgressData]:
        """获取当前进度"""
        key = f"analysis_progress:{self.analysis_id}"
        
        if self.use_redis:
            try:
                data = self.redis_client.get(key)
                if data:
                    return ProgressData(**json.loads(data))
            except Exception as e:
                logger.error(f"Failed to get progress from Redis: {e}")
        
        # 从内存获取
        data = SimpleProgressTracker._memory_store.get(key)
        if data:
            return ProgressData(**data)
        
        return None
    
    def mark_completed(self, success: bool = True):
        """标记分析完成"""
        self.status = AnalysisStatus.COMPLETED if success else AnalysisStatus.FAILED
        self.current_step = len(self.steps)  # 设置为超过最后一步，确保100%进度
        
        if success:
            self.update_progress("✅ 分析成功完成！", len(self.steps) - 1)
        else:
            self.update_progress("❌ 分析执行失败", len(self.steps) - 1)
    
    def mark_cancelled(self):
        """标记分析取消"""
        self.status = AnalysisStatus.CANCELLED
        self.update_progress("⏹️ 分析已取消")

# 全局进度获取函数
def get_analysis_progress(analysis_id: str) -> Optional[ProgressData]:
    """获取分析进度（全局函数）"""
    key = f"analysis_progress:{analysis_id}"
    
    # 先尝试Redis
    try:
        redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        data = redis_client.get(key)
        if data:
            return ProgressData(**json.loads(data))
    except:
        pass
    
    # 再尝试内存
    if hasattr(SimpleProgressTracker, '_memory_store'):
        data = SimpleProgressTracker._memory_store.get(key)
        if data:
            return ProgressData(**data)
    
    return None