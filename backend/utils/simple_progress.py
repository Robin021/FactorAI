#!/usr/bin/env python3
"""
简单进度跟踪器
模仿老的Streamlit框架的简单进度显示方式
"""

import time
from typing import Optional, Callable
import asyncio
import json
from datetime import datetime

class SimpleProgressTracker:
    """简单的进度跟踪器"""
    
    def __init__(self, analysis_id: str, redis_client=None):
        self.analysis_id = analysis_id
        self.redis_client = redis_client
        self.current_step = 0
        self.total_steps = 10  # 固定10步，简单明了
        self.start_time = time.time()
        self.status = "running"
        self.message = "准备开始分析..."
        
        # 预定义的步骤名称
        self.step_names = [
            "📋 准备分析",
            "🔍 验证股票代码", 
            "🔧 检查环境配置",
            "📊 获取市场数据",
            "💼 获取基本面数据",
            "📈 技术分析",
            "💭 情绪分析",
            "🤝 综合分析",
            "💡 生成建议",
            "📄 完成报告"
        ]
    
    async def update_progress(self, message: str, step: Optional[int] = None):
        """更新进度"""
        if step is not None:
            self.current_step = min(step, self.total_steps - 1)
        
        self.message = message
        elapsed_time = time.time() - self.start_time
        progress_percentage = (self.current_step / (self.total_steps - 1)) * 100
        
        # 估算剩余时间（简单线性估算）
        if progress_percentage > 0:
            estimated_total_time = elapsed_time / (progress_percentage / 100)
            remaining_time = max(estimated_total_time - elapsed_time, 0)
        else:
            remaining_time = 300  # 默认5分钟
        
        # 构建进度数据
        progress_data = {
            "analysis_id": self.analysis_id,
            "status": self.status,
            "progress": progress_percentage,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "current_step_name": self.step_names[self.current_step],
            "message": message,
            "elapsed_time": elapsed_time,
            "estimated_time_remaining": remaining_time,
            "last_update": time.time()
        }
        
        # 保存到Redis
        if self.redis_client:
            try:
                await self.redis_client.setex(
                    f"analysis_progress:{self.analysis_id}",
                    3600,  # 1小时过期
                    json.dumps(progress_data)
                )
            except Exception as e:
                print(f"Failed to save progress to Redis: {e}")
        
        print(f"📊 [进度] 步骤 {self.current_step + 1}/{self.total_steps}: {message}")
    
    async def complete(self, message: str = "分析完成"):
        """标记完成"""
        self.status = "completed"
        self.current_step = self.total_steps - 1
        await self.update_progress(message)
    
    async def fail(self, error_message: str):
        """标记失败"""
        self.status = "failed"
        await self.update_progress(f"分析失败: {error_message}")

def create_simple_progress_callback(tracker: SimpleProgressTracker):
    """创建简单的进度回调函数"""
    async def callback(message: str, step: Optional[int] = None):
        await tracker.update_progress(message, step)
    return callback

# 同步版本（兼容旧代码）
class SyncSimpleProgressTracker:
    """同步版本的简单进度跟踪器"""
    
    def __init__(self, analysis_id: str):
        self.analysis_id = analysis_id
        self.current_step = 0
        self.total_steps = 10
        self.start_time = time.time()
        
    def update_progress(self, message: str, step: Optional[int] = None):
        """更新进度（同步版本）"""
        if step is not None:
            self.current_step = min(step, self.total_steps - 1)
        
        progress_percentage = (self.current_step / (self.total_steps - 1)) * 100
        print(f"📊 [进度] 步骤 {self.current_step + 1}/{self.total_steps} ({progress_percentage:.1f}%): {message}")

def create_sync_progress_callback(tracker: SyncSimpleProgressTracker):
    """创建同步版本的进度回调函数"""
    def callback(message: str, step: Optional[int] = None, total_steps: Optional[int] = None):
        if total_steps and total_steps != tracker.total_steps:
            tracker.total_steps = total_steps
        tracker.update_progress(message, step)
    return callback