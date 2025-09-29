"""
Async analysis service that integrates with the task queue system
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from ..models.user import UserInDB
from ..models.analysis import (
    AnalysisRequest,
    AnalysisStatus,
    AnalysisInDB,
    AnalysisResult
)
from ..core.database import get_database, get_redis
from ..core.task_queue import TaskQueue, TaskPriority, get_task_queue
from ..services.analysis_service import AnalysisService, get_analysis_service
from ..core.websocket_manager import get_websocket_manager, WebSocketManager
from ..core.exceptions import AnalysisException

from tradingagents.utils.logging_manager import get_logger
logger = get_logger('async_analysis_service')


class AsyncAnalysisService:
    """Service for managing async analysis tasks"""
    
    def __init__(self, db: AsyncIOMotorDatabase, redis_client, task_queue: TaskQueue, websocket_manager: WebSocketManager = None):
        self.db = db
        self.redis = redis_client
        self.task_queue = task_queue
        self.websocket_manager = websocket_manager
        
        # Register analysis task handler
        self.task_queue.register_handler("stock_analysis", self._handle_analysis_task)
    
    async def start_analysis(
        self,
        analysis_request: AnalysisRequest,
        user: UserInDB,
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> str:
        """
        Start a new analysis task asynchronously
        """
        try:
            # Create analysis record in database
            analysis_doc = AnalysisInDB(
                user_id=user.id,
                stock_code=analysis_request.stock_code,
                market_type=analysis_request.market_type,
                status=AnalysisStatus.PENDING,
                config={
                    "analysts": analysis_request.analysts,
                    "llm_config": analysis_request.llm_config,
                    "custom_params": analysis_request.custom_params,
                    "analysis_date": analysis_request.analysis_date
                }
            )
            
            # Insert into database
            result = await self.db.analyses.insert_one(analysis_doc.dict(by_alias=True))
            analysis_id = str(result.inserted_id)
            
            logger.info(f"Created analysis record {analysis_id} for user {user.username}")
            
            # Prepare task payload
            task_payload = {
                "analysis_id": analysis_id,
                "analysis_request": analysis_request.dict(),
                "user_id": str(user.id),
                "user_data": {
                    "username": user.username,
                    "email": user.email
                }
            }
            
            # Enqueue analysis task
            task_id = await self.task_queue.enqueue_task(
                task_type="stock_analysis",
                payload=task_payload,
                priority=priority,
                max_retries=2,  # Analysis tasks get 2 retries
                timeout=3600    # 1 hour timeout
            )
            
            # Update analysis record with task ID
            await self.db.analyses.update_one(
                {"_id": ObjectId(analysis_id)},
                {"$set": {"task_id": task_id}}
            )
            
            logger.info(f"Enqueued analysis task {task_id} for analysis {analysis_id}")
            
            return analysis_id
            
        except Exception as e:
            logger.error(f"Failed to start analysis: {e}")
            raise AnalysisException(f"Failed to start analysis: {str(e)}")
    
    async def get_analysis_status(self, analysis_id: str, user: UserInDB) -> Dict[str, Any]:
        """
        Get analysis status and progress
        """
        try:
            # Get analysis record
            analysis_doc = await self.db.analyses.find_one({
                "_id": ObjectId(analysis_id),
                "user_id": user.id
            })
            
            if not analysis_doc:
                raise AnalysisException("Analysis not found")
            
            # Get task progress if available
            progress_data = {}
            if "task_id" in analysis_doc:
                task_id = analysis_doc["task_id"]
                
                # Get task info
                task_info = await self.task_queue.get_task_info(task_id)
                if task_info:
                    progress_data = {
                        "task_status": task_info.status.value,
                        "progress": task_info.progress,
                        "retry_count": task_info.retry_count,
                        "error_message": task_info.error_message
                    }
                
                # Get detailed progress from Redis
                progress_key = f"task_progress:{task_id}"
                detailed_progress = await self.redis.get(progress_key)
                if detailed_progress:
                    progress_info = json.loads(detailed_progress)
                    progress_data.update({
                        "current_step": progress_info.get("current_step"),
                        "message": progress_info.get("message"),
                        "updated_at": progress_info.get("updated_at")
                    })
            
            return {
                "analysis_id": analysis_id,
                "stock_code": analysis_doc["stock_code"],
                "market_type": analysis_doc["market_type"],
                "status": analysis_doc["status"],
                "progress": analysis_doc.get("progress", 0.0),
                "created_at": analysis_doc["created_at"],
                "started_at": analysis_doc.get("started_at"),
                "completed_at": analysis_doc.get("completed_at"),
                "error_message": analysis_doc.get("error_message"),
                **progress_data
            }
            
        except Exception as e:
            logger.error(f"Failed to get analysis status: {e}")
            raise AnalysisException(f"Failed to get analysis status: {str(e)}")
    
    async def get_analysis_result(self, analysis_id: str, user: UserInDB) -> Optional[AnalysisResult]:
        """
        Get analysis result if completed
        """
        try:
            # Get analysis record
            analysis_doc = await self.db.analyses.find_one({
                "_id": ObjectId(analysis_id),
                "user_id": user.id
            })
            
            if not analysis_doc:
                raise AnalysisException("Analysis not found")
            
            if analysis_doc["status"] != AnalysisStatus.COMPLETED.value:
                return None
            
            # Try to get result from Redis cache first
            if "task_id" in analysis_doc:
                task_id = analysis_doc["task_id"]
                cached_result = await self.redis.get(f"analysis_result:{task_id}")
                if cached_result:
                    result_data = json.loads(cached_result)
                    return AnalysisResult(**result_data)
            
            # Get result from database
            result_data = analysis_doc.get("result_data")
            if result_data:
                return AnalysisResult(**result_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get analysis result: {e}")
            raise AnalysisException(f"Failed to get analysis result: {str(e)}")
    
    async def cancel_analysis(self, analysis_id: str, user: UserInDB) -> bool:
        """
        Cancel a running analysis
        """
        try:
            # Get analysis record
            analysis_doc = await self.db.analyses.find_one({
                "_id": ObjectId(analysis_id),
                "user_id": user.id
            })
            
            if not analysis_doc:
                raise AnalysisException("Analysis not found")
            
            # Check if analysis can be cancelled
            if analysis_doc["status"] in [AnalysisStatus.COMPLETED.value, AnalysisStatus.FAILED.value, AnalysisStatus.CANCELLED.value]:
                return False
            
            # Cancel the task if it exists
            if "task_id" in analysis_doc:
                task_id = analysis_doc["task_id"]
                await self.task_queue.cancel_task(task_id)
            
            # Update analysis status
            await self.db.analyses.update_one(
                {"_id": ObjectId(analysis_id)},
                {
                    "$set": {
                        "status": AnalysisStatus.CANCELLED.value,
                        "completed_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"Cancelled analysis {analysis_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel analysis: {e}")
            raise AnalysisException(f"Failed to cancel analysis: {str(e)}")
    
    async def get_analysis_history(
        self,
        user: UserInDB,
        stock_code: Optional[str] = None,
        status: Optional[AnalysisStatus] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get analysis history for user
        """
        try:
            # Build query
            query = {"user_id": user.id}
            if stock_code:
                query["stock_code"] = stock_code
            if status:
                query["status"] = status.value
            
            # Get total count
            total = await self.db.analyses.count_documents(query)
            
            # Get analyses with pagination
            cursor = self.db.analyses.find(query).sort("created_at", -1).skip(offset).limit(limit)
            analyses = []
            
            async for doc in cursor:
                analysis_data = {
                    "id": str(doc["_id"]),
                    "stock_code": doc["stock_code"],
                    "market_type": doc["market_type"],
                    "status": doc["status"],
                    "progress": doc.get("progress", 0.0),
                    "created_at": doc["created_at"],
                    "started_at": doc.get("started_at"),
                    "completed_at": doc.get("completed_at"),
                    "error_message": doc.get("error_message")
                }
                analyses.append(analysis_data)
            
            return {
                "analyses": analyses,
                "total": total,
                "limit": limit,
                "offset": offset
            }
            
        except Exception as e:
            logger.error(f"Failed to get analysis history: {e}")
            raise AnalysisException(f"Failed to get analysis history: {str(e)}")
    
    async def _handle_analysis_task(self, task_id: str, payload: Dict[str, Any]):
        """
        Handle analysis task execution
        """
        analysis_id = payload["analysis_id"]
        analysis_request_data = payload["analysis_request"]
        user_id = payload["user_id"]
        
        logger.info(f"Handling analysis task {task_id} for analysis {analysis_id}")
        
        try:
            # Create analysis request object
            analysis_request = AnalysisRequest(**analysis_request_data)
            
            # Create user object (minimal for analysis)
            user = UserInDB(
                id=ObjectId(user_id),
                username=payload["user_data"]["username"],
                email=payload["user_data"]["email"],
                hashed_password="",  # Not needed for analysis
                role="user",
                permissions=[]
            )
            
            # Get analysis service
            analysis_service = AnalysisService(self.db, self.redis)
            
            # Create progress callback
            async def progress_callback(progress: float, message: str = None, current_step: str = None):
                await self.task_queue.update_task_progress(
                    task_id, progress, message, current_step
                )
                
                # 同时更新analysis_progress键，供前端API使用
                progress_data = {
                    "status": "running",
                    "progress": progress,
                    "message": message,
                    "current_step": current_step,
                    "updated_at": datetime.utcnow().isoformat()
                }
                await self.redis.setex(
                    f"analysis_progress:{analysis_id}",
                    3600,  # 1 hour TTL
                    json.dumps(progress_data)
                )
                
                # Send WebSocket notification
                if self.websocket_manager:
                    await self.websocket_manager.broadcast_analysis_progress(
                        analysis_id, progress, message, current_step
                    )
            
            # Monkey patch the analysis service to use our progress callback
            original_update_progress = analysis_service._update_progress
            original_complete_analysis = analysis_service._complete_analysis
            
            async def patched_update_progress(aid, progress, message=None, current_step=None):
                await original_update_progress(aid, progress, message, current_step)
                await progress_callback(progress, message, current_step)
            
            async def patched_complete_analysis(aid, result_data):
                await original_complete_analysis(aid, result_data)
                
                # 更新analysis_progress键为完成状态
                completion_data = {
                    "status": "completed",
                    "progress": 100.0,
                    "message": "分析已完成",
                    "current_step": "完成",
                    "updated_at": datetime.utcnow().isoformat()
                }
                await self.redis.setex(
                    f"analysis_progress:{aid}",
                    3600,  # 1 hour TTL
                    json.dumps(completion_data)
                )
                
                # Send WebSocket notification for completion
                if self.websocket_manager:
                    result_summary = {
                        "recommendation": result_data.summary.get("recommendation", "HOLD") if result_data.summary else "HOLD",
                        "confidence_score": result_data.summary.get("confidence_score", 0.5) if result_data.summary else 0.5
                    }
                    await self.websocket_manager.broadcast_analysis_completed(aid, result_summary)
            
            analysis_service._update_progress = patched_update_progress
            analysis_service._complete_analysis = patched_complete_analysis
            
            # Execute the analysis
            await analysis_service.execute_analysis(analysis_id, analysis_request, user)
            
            logger.info(f"Analysis task {task_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Analysis task {task_id} failed: {e}")
            
            # Update analysis status in database
            await self.db.analyses.update_one(
                {"_id": ObjectId(analysis_id)},
                {
                    "$set": {
                        "status": AnalysisStatus.FAILED.value,
                        "error_message": str(e),
                        "completed_at": datetime.utcnow()
                    }
                }
            )
            
            # Notify WebSocket subscribers of failure
            if self.websocket_manager:
                await self.websocket_manager.broadcast_analysis_failed(analysis_id, str(e))
            
            raise  # Re-raise to let task queue handle retry logic
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get task queue statistics
        """
        return await self.task_queue.get_queue_stats()


# Dependency function
async def get_async_analysis_service(
    db: AsyncIOMotorDatabase = None,
    redis_client = None,
    task_queue: TaskQueue = None,
    websocket_manager: WebSocketManager = None
) -> AsyncAnalysisService:
    """
    Dependency to get async analysis service instance
    """
    if db is None:
        db = await get_database()
    if redis_client is None:
        redis_client = await get_redis()
    if task_queue is None:
        task_queue = await get_task_queue()
    if websocket_manager is None:
        websocket_manager = await get_websocket_manager()
    
    return AsyncAnalysisService(db, redis_client, task_queue, websocket_manager)