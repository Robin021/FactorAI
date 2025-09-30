"""
Analysis API endpoints
"""
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from ...models.user import UserInDB
from ...models.analysis import (
    Analysis,
    AnalysisInDB,
    AnalysisRequest,
    AnalysisProgress,
    AnalysisResult,
    AnalysisStatus,
    AnalysisListResponse,
    AnalysisHistoryQuery,
    MarketType
)
from ...core.security import (
    get_current_active_user,
    require_permissions,
    Permissions
)
from ...core.database import get_database, get_redis
from ...core.exceptions import AuthenticationException, ValidationException
from ...services.analysis_service import AnalysisService, get_analysis_service

# Import logging
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('api.analysis')

router = APIRouter()


@router.post("/start", response_model=dict)
async def start_analysis(
    analysis_request: AnalysisRequest,
    priority: Optional[str] = "normal",
    current_user: UserInDB = Depends(require_permissions([Permissions.ANALYSIS_CREATE])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Start a new analysis task using async task queue
    """
    # Import here to avoid circular imports
    from ...services.async_analysis_service import get_async_analysis_service
    from ...core.task_queue import TaskPriority
    
    # Validate stock code format based on market type
    if not _validate_stock_code(analysis_request.stock_code, analysis_request.market_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid stock code format for {analysis_request.market_type.value} market"
        )
    
    # Check if user has reached analysis limit (optional rate limiting)
    active_analyses = await db.analyses.count_documents({
        "user_id": current_user.id,
        "status": {"$in": [AnalysisStatus.PENDING.value, AnalysisStatus.RUNNING.value]}
    })
    
    if active_analyses >= 5:  # Limit to 5 concurrent analyses per user
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many active analyses. Please wait for some to complete."
        )
    
    # Parse priority
    priority_map = {
        "low": TaskPriority.LOW,
        "normal": TaskPriority.NORMAL,
        "high": TaskPriority.HIGH,
        "urgent": TaskPriority.URGENT
    }
    task_priority = priority_map.get(priority.lower(), TaskPriority.NORMAL)
    
    # Get async analysis service
    async_analysis_service = await get_async_analysis_service()
    
    # Start analysis using async task queue
    analysis_id = await async_analysis_service.start_analysis(
        analysis_request, current_user, task_priority
    )
    
    return {
        "analysis_id": analysis_id,
        "status": "queued",
        "message": "Analysis queued successfully",
        "priority": priority
    }


@router.get("/{analysis_id}/progress")
async def get_analysis_progress(
    analysis_id: str,
    current_user: UserInDB = Depends(require_permissions([Permissions.ANALYSIS_READ])),
    db: AsyncIOMotorDatabase = Depends(get_database),
    redis_client = Depends(get_redis)
):
    """
    Get analysis progress (polling endpoint)
    Returns detailed progress information for frontend polling
    """
    try:
        analysis_object_id = ObjectId(analysis_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid analysis ID format"
        )
    
    # Get analysis from database
    analysis_doc = await db.analyses.find_one({"_id": analysis_object_id})
    if not analysis_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    analysis = AnalysisInDB(**analysis_doc)
    
    # Check if user owns this analysis or is admin
    if str(analysis.user_id) != str(current_user.id) and "admin" not in current_user.role.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get real-time progress from Redis
    progress_data = None
    redis_keys_to_try = [
        f"analysis_progress:{analysis_id}",  # React版本格式
        f"progress:{analysis_id}",           # Streamlit版本格式
        f"task_progress:analysis_{analysis_id}"  # TaskQueue格式
    ]
    
    for key in redis_keys_to_try:
        progress_data = await redis_client.get(key)
        if progress_data:
            break
    
    # 解析进度数据
    if progress_data:
        try:
            import json
            progress_info = json.loads(progress_data)
            
            # 返回兼容前端 SimpleAnalysisProgress 组件的格式
            # 优先使用 progress_percentage (0-1格式)，如果没有则从 progress (0-100) 转换
            progress_percentage = progress_info.get("progress_percentage")
            if progress_percentage is None:
                # fallback: 从progress字段转换
                progress_percentage = progress_info.get("progress", 0) / 100.0
            
            return {
                "analysis_id": analysis_id,
                "status": progress_info.get("status", analysis.status.value),
                "current_step": progress_info.get("current_step", 0),
                "total_steps": progress_info.get("total_steps", 6),
                "progress_percentage": progress_percentage,  # 0-1 的小数格式
                "message": progress_info.get("message", "正在分析..."),
                "elapsed_time": progress_info.get("elapsed_time", 0),
                "estimated_remaining": progress_info.get("estimated_time_remaining", progress_info.get("estimated_remaining", 0)),
                "current_step_name": progress_info.get("current_step_name") or progress_info.get("current_step") or "分析中",
                "timestamp": datetime.utcnow().timestamp()
            }
        except Exception as e:
            logger.warning(f"Failed to parse progress data from Redis: {e}")
    
    # Fallback to database data
    # 从数据库构造进度数据
    progress_percentage = analysis.progress / 100.0 if analysis.progress else 0.0
    
    # 根据进度估算当前步骤
    total_steps = 6
    current_step = int(progress_percentage * total_steps)
    
    # 根据状态返回消息
    status_messages = {
        "pending": "等待开始...",
        "running": "正在分析...",
        "completed": "分析完成",
        "failed": analysis.error_message or "分析失败",
        "cancelled": "已取消"
    }
    
    return {
        "analysis_id": analysis_id,
        "status": analysis.status.value,
        "current_step": current_step,
        "total_steps": total_steps,
        "progress_percentage": progress_percentage,
        "message": status_messages.get(analysis.status.value, "未知状态"),
        "elapsed_time": 0,
        "estimated_remaining": 0,
        "current_step_name": f"步骤 {current_step + 1}/{total_steps}",
        "timestamp": datetime.utcnow().timestamp()
    }


@router.get("/{analysis_id}/status", response_model=AnalysisProgress)
async def get_analysis_status(
    analysis_id: str,
    current_user: UserInDB = Depends(require_permissions([Permissions.ANALYSIS_READ])),
    db: AsyncIOMotorDatabase = Depends(get_database),
    redis_client = Depends(get_redis)
):
    """
    Get analysis status and progress
    """
    try:
        analysis_object_id = ObjectId(analysis_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid analysis ID format"
        )
    
    # Get analysis from database
    analysis_doc = await db.analyses.find_one({"_id": analysis_object_id})
    if not analysis_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    analysis = AnalysisInDB(**analysis_doc)
    
    # Check if user owns this analysis or is admin
    if str(analysis.user_id) != str(current_user.id) and "admin" not in current_user.role.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get real-time progress from Redis if available
    # 尝试多种Redis键格式，兼容Streamlit版本和React版本
    progress_data = None
    redis_keys_to_try = [
        f"analysis_progress:{analysis_id}",  # React版本格式
        f"progress:{analysis_id}",           # Streamlit版本格式
        f"task_progress:analysis_{analysis_id}"  # TaskQueue格式
    ]
    
    for key in redis_keys_to_try:
        progress_data = await redis_client.get(key)
        if progress_data:
            break
    
    if progress_data:
        try:
            import json
            progress_info = json.loads(progress_data)
            
            # 兼容不同的数据格式
            status_value = progress_info.get("status", analysis.status.value)
            if isinstance(status_value, str):
                # 确保状态值正确映射
                status_mapping = {
                    'running': 'running',
                    'completed': 'completed', 
                    'failed': 'failed',
                    'pending': 'pending',
                    'cancelled': 'cancelled'
                }
                status_value = status_mapping.get(status_value, analysis.status.value)
            
            # 兼容不同的进度字段名 - 注意不能用or，因为0会被判断为False
            if "progress" in progress_info:
                progress_value = progress_info["progress"]
            elif "progress_percentage" in progress_info:
                # progress_percentage是0-1格式，需要转换为0-100
                progress_value = progress_info["progress_percentage"] * 100
            else:
                progress_value = analysis.progress
            
            # 兼容不同的步骤字段名
            current_step = progress_info.get("current_step") or progress_info.get("current_step_name")
            
            # 兼容不同的消息字段名
            message = progress_info.get("message") or progress_info.get("last_message")
            
            # 兼容不同的时间字段名
            estimated_time_remaining = progress_info.get("estimated_time_remaining") or progress_info.get("remaining_time")
            
            return AnalysisProgress(
                status=AnalysisStatus(status_value),
                progress=progress_value,
                current_step=current_step,
                message=message,
                estimated_time_remaining=estimated_time_remaining
            )
        except Exception as e:
            logger.warning(f"Failed to parse progress data: {e}")
            pass
    
    # Fallback to database data
    return AnalysisProgress(
        status=analysis.status,
        progress=analysis.progress,
        current_step=None,
        message=analysis.error_message if analysis.status == AnalysisStatus.FAILED else None
    )


@router.get("/{analysis_id}/result", response_model=Analysis)
async def get_analysis_result(
    analysis_id: str,
    current_user: UserInDB = Depends(require_permissions([Permissions.ANALYSIS_READ])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get analysis result
    """
    try:
        analysis_object_id = ObjectId(analysis_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid analysis ID format"
        )
    
    # Get analysis from database
    analysis_doc = await db.analyses.find_one({"_id": analysis_object_id})
    if not analysis_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    analysis = AnalysisInDB(**analysis_doc)
    
    # Check if user owns this analysis or is admin
    if str(analysis.user_id) != str(current_user.id) and "admin" not in current_user.role.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if analysis is completed
    if analysis.status != AnalysisStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis is not completed. Current status: {analysis.status.value}"
        )
    
    return _convert_to_analysis_response(analysis)


@router.get("/history", response_model=AnalysisListResponse)
async def get_analysis_history(
    stock_code: Optional[str] = None,
    market_type: Optional[MarketType] = None,
    status: Optional[AnalysisStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: UserInDB = Depends(require_permissions([Permissions.ANALYSIS_READ])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get analysis history with filtering and pagination
    """
    # Validate pagination parameters
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20
    
    # Build query filter
    query_filter = {"user_id": current_user.id}
    
    if stock_code:
        query_filter["stock_code"] = stock_code.upper()
    
    if market_type:
        query_filter["market_type"] = market_type.value
    
    if status:
        query_filter["status"] = status.value
    
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        query_filter["created_at"] = date_filter
    
    # Get total count
    total = await db.analyses.count_documents(query_filter)
    
    # Get paginated results
    skip = (page - 1) * page_size
    cursor = db.analyses.find(query_filter).sort("created_at", -1).skip(skip).limit(page_size)
    
    analyses = []
    async for analysis_doc in cursor:
        analysis = AnalysisInDB(**analysis_doc)
        analyses.append(_convert_to_analysis_response(analysis))
    
    return AnalysisListResponse(
        analyses=analyses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.delete("/{analysis_id}")
async def delete_analysis(
    analysis_id: str,
    current_user: UserInDB = Depends(require_permissions([Permissions.ANALYSIS_DELETE])),
    db: AsyncIOMotorDatabase = Depends(get_database),
    redis_client = Depends(get_redis)
):
    """
    Delete an analysis record
    """
    try:
        analysis_object_id = ObjectId(analysis_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid analysis ID format"
        )
    
    # Get analysis from database
    analysis_doc = await db.analyses.find_one({"_id": analysis_object_id})
    if not analysis_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    analysis = AnalysisInDB(**analysis_doc)
    
    # Check if user owns this analysis or is admin
    if str(analysis.user_id) != str(current_user.id) and "admin" not in current_user.role.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Cannot delete running analysis
    if analysis.status == AnalysisStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete running analysis. Please cancel it first."
        )
    
    # Delete from database
    await db.analyses.delete_one({"_id": analysis_object_id})
    
    # Clean up Redis cache
    await redis_client.delete(f"analysis_progress:{analysis_id}")
    await redis_client.delete(f"analysis_result:{analysis_id}")
    
    return {"message": "Analysis deleted successfully"}


@router.post("/{analysis_id}/cancel")
async def cancel_analysis(
    analysis_id: str,
    current_user: UserInDB = Depends(require_permissions([Permissions.ANALYSIS_UPDATE])),
    db: AsyncIOMotorDatabase = Depends(get_database),
    redis_client = Depends(get_redis)
):
    """
    Cancel a running analysis
    """
    try:
        analysis_object_id = ObjectId(analysis_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid analysis ID format"
        )
    
    # Get analysis from database
    analysis_doc = await db.analyses.find_one({"_id": analysis_object_id})
    if not analysis_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    analysis = AnalysisInDB(**analysis_doc)
    
    # Check if user owns this analysis or is admin
    if str(analysis.user_id) != str(current_user.id) and "admin" not in current_user.role.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Can only cancel pending or running analyses
    if analysis.status not in [AnalysisStatus.PENDING, AnalysisStatus.RUNNING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel analysis with status: {analysis.status.value}"
        )
    
    # Update status to cancelled
    await db.analyses.update_one(
        {"_id": analysis_object_id},
        {
            "$set": {
                "status": AnalysisStatus.CANCELLED.value,
                "completed_at": datetime.utcnow()
            }
        }
    )
    
    # Set cancellation flag in Redis
    await redis_client.setex(f"analysis_cancel:{analysis_id}", 3600, "true")
    
    return {"message": "Analysis cancellation requested"}


@router.get("/stats")
async def get_analysis_stats(
    current_user: UserInDB = Depends(require_permissions([Permissions.ANALYSIS_READ])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get analysis statistics for the current user
    """
    # Get status counts
    pipeline = [
        {"$match": {"user_id": current_user.id}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    
    status_counts = {}
    async for result in db.analyses.aggregate(pipeline):
        status_counts[result["_id"]] = result["count"]
    
    # Get recent activity (last 30 days)
    from datetime import timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    recent_count = await db.analyses.count_documents({
        "user_id": current_user.id,
        "created_at": {"$gte": thirty_days_ago}
    })
    
    # Get most analyzed stocks
    pipeline = [
        {"$match": {"user_id": current_user.id}},
        {"$group": {"_id": "$stock_code", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    
    top_stocks = []
    async for result in db.analyses.aggregate(pipeline):
        top_stocks.append({
            "stock_code": result["_id"],
            "count": result["count"]
        })
    
    return {
        "status_counts": status_counts,
        "recent_activity": recent_count,
        "top_stocks": top_stocks,
        "total_analyses": sum(status_counts.values())
    }


@router.get("/queue/stats")
async def get_queue_stats(
    current_user: UserInDB = Depends(require_permissions([Permissions.ADMIN]))
):
    """
    Get task queue statistics (admin only)
    """
    from ...services.async_analysis_service import get_async_analysis_service
    
    async_analysis_service = await get_async_analysis_service()
    stats = await async_analysis_service.get_queue_stats()
    return stats


def _validate_stock_code(stock_code: str, market_type: MarketType) -> bool:
    """
    Validate stock code format based on market type
    """
    if not stock_code:
        return False
    
    stock_code = stock_code.upper()
    
    if market_type == MarketType.CN:
        # Chinese stocks: 6 digits (e.g., 000001, 600000)
        return len(stock_code) == 6 and stock_code.isdigit()
    elif market_type == MarketType.US:
        # US stocks: 1-5 letters (e.g., AAPL, MSFT, GOOGL)
        return 1 <= len(stock_code) <= 5 and stock_code.isalpha()
    elif market_type == MarketType.HK:
        # HK stocks: 4-5 digits (e.g., 0700, 00700)
        return 4 <= len(stock_code) <= 5 and stock_code.isdigit()
    
    return False


def _convert_to_analysis_response(analysis_db: AnalysisInDB) -> Analysis:
    """
    Convert database analysis model to API response model
    """
    return Analysis(
        id=str(analysis_db.id),
        user_id=str(analysis_db.user_id),
        stock_code=analysis_db.stock_code,
        market_type=analysis_db.market_type,
        status=analysis_db.status,
        progress=analysis_db.progress,
        config=analysis_db.config,
        result_data=analysis_db.result_data,
        error_message=analysis_db.error_message,
        created_at=analysis_db.created_at,
        started_at=analysis_db.started_at,
        completed_at=analysis_db.completed_at
    )