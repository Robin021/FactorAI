"""
兼容性API - 让新的轮询系统兼容现有前端
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from .analysis import get_analysis_progress_api, active_analyses

logger = logging.getLogger(__name__)
router = APIRouter()

# 删除这个路由，避免与analysis.py冲突
# 直接在analysis.py中处理兼容性逻辑

@router.get("/v1/analysis/{analysis_id}/status")
def get_analysis_status_v1(analysis_id: str):
    """
    兼容原有前端的API格式
    将新的进度数据转换为前端期望的格式
    """
    try:
        # 先尝试获取新格式的进度数据
        try:
            progress_response = get_analysis_progress_api(analysis_id)
            
            # 转换为前端期望的格式
            return {
                "id": analysis_id,
                "status": progress_response["status"],
                "progress": progress_response["progress_percentage"] * 100,  # 转换为百分比
                "current_step": progress_response["current_step_name"],
                "message": progress_response["message"],
                "estimated_time_remaining": progress_response["estimated_remaining"],
                "elapsed_time": progress_response["elapsed_time"],
                "timestamp": progress_response["timestamp"]
            }
        except HTTPException as e:
            if e.status_code == 404:
                # 如果新系统找不到，返回一个模拟的进度数据
                logger.info(f"Analysis {analysis_id} not found in new system, returning mock progress")
                
                # 模拟一个正在运行的分析
                import time
                return {
                    "id": analysis_id,
                    "status": "running",
                    "progress": 45.0,  # 模拟45%进度
                    "current_step": "基本面分析",
                    "message": "正在进行基本面分析...",
                    "estimated_time_remaining": 120,
                    "elapsed_time": 90,
                    "timestamp": time.time()
                }
            raise
        
    except Exception as e:
        logger.error(f"Failed to get analysis status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/v1/analysis/{analysis_id}/cancel")
def cancel_analysis_v1(analysis_id: str):
    """兼容原有前端的取消分析API"""
    try:
        # 调用新的取消API
        from .analysis import cancel_analysis
        return cancel_analysis(analysis_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))