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
        """根据分析师数量动态生成分析步骤"""
        steps = [
            ProgressStep("数据验证", "验证股票代码并预获取数据", 0.05),
            ProgressStep("环境准备", "检查API密钥和环境配置", 0.02),
            ProgressStep("成本预估", "预估分析成本", 0.01),
            ProgressStep("参数配置", "配置分析参数和模型", 0.02),
            ProgressStep("引擎初始化", "初始化AI分析引擎", 0.05),
        ]
        
        # 为每个分析师添加专门的步骤
        analyst_weight = 0.8 / len(self.analysts)
        analyst_names = {
            'market': '市场分析师',
            'fundamentals': '基本面分析师', 
            'technical': '技术分析师',
            'sentiment': '情绪分析师',
            'news': '新闻分析师'
        }
        
        for analyst in self.analysts:
            analyst_name = analyst_names.get(analyst, analyst)
            steps.append(ProgressStep(
                f"{analyst_name}分析",
                f"{analyst_name}正在进行专业分析",
                analyst_weight
            ))
        
        steps.append(ProgressStep("结果整理", "整理分析结果和生成报告", 0.05))
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
    
    def _detect_step_from_message(self, message: str) -> Optional[int]:
        """智能检测当前步骤"""
        message_lower = message.lower()
        
        if "开始股票分析" in message:
            return 0
        elif "验证" in message or "预获取" in message:
            return 0
        elif "环境" in message or "api" in message_lower:
            return 1
        elif "成本" in message or "预估" in message:
            return 2
        elif "配置" in message or "参数" in message:
            return 3
        elif "初始化" in message or "引擎" in message:
            return 4
        elif any(analyst in message for analyst in ["市场分析师", "基本面分析师", "技术分析师"]):
            # 找到对应的分析师步骤
            for i, step in enumerate(self.steps):
                if "分析师" in step.name and any(keyword in message for keyword in step.name.split()):
                    return i
        elif "整理" in message or "结果" in message:
            return len(self.steps) - 1
        elif "完成" in message or "成功" in message:
            return len(self.steps) - 1
            
        return None
    
    def _calculate_weighted_progress(self) -> float:
        """根据步骤权重计算进度"""
        if self.current_step >= len(self.steps):
            return 1.0
            
        completed_weight = sum(step.weight for step in self.steps[:self.current_step])
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
        self.current_step = len(self.steps) - 1
        
        if success:
            self.update_progress("✅ 分析成功完成！")
        else:
            self.update_progress("❌ 分析执行失败")
    
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