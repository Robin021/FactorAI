"""
Async task queue system for managing analysis tasks
"""
import asyncio
import json
import traceback
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
from dataclasses import dataclass, asdict
from motor.motor_asyncio import AsyncIOMotorDatabase
import redis.asyncio as redis

from ..models.analysis import AnalysisStatus
from .database import get_database, get_redis
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('task_queue')


class TaskStatus(str, Enum):
    """Task status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(int, Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class TaskInfo:
    """Task information structure"""
    task_id: str
    task_type: str
    payload: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    max_retries: int = 3
    retry_count: int = 0
    retry_delay: int = 60  # seconds
    timeout: int = 3600  # seconds
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    error_message: Optional[str] = None
    progress: float = 0.0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class TaskQueue:
    """Async task queue manager"""
    
    def __init__(self, redis_client: redis.Redis, db: AsyncIOMotorDatabase):
        self.redis = redis_client
        self.db = db
        self.workers: Dict[str, asyncio.Task] = {}
        self.task_handlers: Dict[str, Callable] = {}
        self.running = False
        self.max_workers = 5
        self.worker_semaphore = asyncio.Semaphore(self.max_workers)
        
        # Redis keys
        self.queue_key = "task_queue"
        self.processing_key = "task_processing"
        self.task_info_prefix = "task_info:"
        self.task_progress_prefix = "task_progress:"
        self.task_cancel_prefix = "task_cancel:"
    
    def register_handler(self, task_type: str, handler: Callable):
        """Register a task handler for a specific task type"""
        self.task_handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")
    
    async def enqueue_task(
        self,
        task_type: str,
        payload: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
        timeout: int = 3600
    ) -> str:
        """Enqueue a new task"""
        task_id = str(uuid.uuid4())
        
        task_info = TaskInfo(
            task_id=task_id,
            task_type=task_type,
            payload=payload,
            priority=priority,
            max_retries=max_retries,
            timeout=timeout
        )
        
        # Store task info in Redis
        await self.redis.setex(
            f"{self.task_info_prefix}{task_id}",
            86400,  # 24 hours TTL
            json.dumps(asdict(task_info), default=str)
        )
        
        # Add to priority queue
        await self.redis.zadd(
            self.queue_key,
            {task_id: priority.value}
        )
        
        # Store in database for persistence
        await self.db.tasks.insert_one({
            "_id": task_id,
            "task_type": task_type,
            "payload": payload,
            "priority": priority.value,
            "max_retries": max_retries,
            "timeout": timeout,
            "status": TaskStatus.PENDING.value,
            "created_at": task_info.created_at,
            "retry_count": 0,
            "progress": 0.0
        })
        
        logger.info(f"Enqueued task {task_id} of type {task_type} with priority {priority.name}")
        return task_id
    
    async def get_task_info(self, task_id: str) -> Optional[TaskInfo]:
        """Get task information"""
        # Try Redis first
        task_data = await self.redis.get(f"{self.task_info_prefix}{task_id}")
        if task_data:
            data = json.loads(task_data)
            # Convert datetime strings back to datetime objects
            for field in ['created_at', 'started_at', 'completed_at']:
                if data.get(field):
                    data[field] = datetime.fromisoformat(data[field])
            return TaskInfo(**data)
        
        # Fallback to database
        task_doc = await self.db.tasks.find_one({"_id": task_id})
        if task_doc:
            return TaskInfo(
                task_id=task_doc["_id"],
                task_type=task_doc["task_type"],
                payload=task_doc["payload"],
                priority=TaskPriority(task_doc["priority"]),
                max_retries=task_doc["max_retries"],
                retry_count=task_doc.get("retry_count", 0),
                timeout=task_doc["timeout"],
                created_at=task_doc["created_at"],
                started_at=task_doc.get("started_at"),
                completed_at=task_doc.get("completed_at"),
                status=TaskStatus(task_doc["status"]),
                error_message=task_doc.get("error_message"),
                progress=task_doc.get("progress", 0.0)
            )
        
        return None
    
    async def update_task_progress(
        self,
        task_id: str,
        progress: float,
        message: Optional[str] = None,
        current_step: Optional[str] = None
    ):
        """Update task progress"""
        progress_data = {
            "progress": progress,
            "message": message,
            "current_step": current_step,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Update Redis
        await self.redis.setex(
            f"{self.task_progress_prefix}{task_id}",
            3600,  # 1 hour TTL
            json.dumps(progress_data)
        )
        
        # Publish to WebSocket subscribers via Redis pub/sub
        if task_id.startswith("analysis_"):
            analysis_id = task_id.replace("analysis_", "")
            websocket_message = {
                "type": "analysis_progress",
                "analysis_id": analysis_id,
                "progress": progress,
                "message": message,
                "current_step": current_step
            }
            await self.redis.publish("websocket_broadcast", json.dumps(websocket_message))
        
        # Update database
        await self.db.tasks.update_one(
            {"_id": task_id},
            {"$set": {"progress": progress}}
        )
        
        # Update task info in Redis
        task_info = await self.get_task_info(task_id)
        if task_info:
            task_info.progress = progress
            await self.redis.setex(
                f"{self.task_info_prefix}{task_id}",
                86400,
                json.dumps(asdict(task_info), default=str)
            )
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        # Set cancel flag
        await self.redis.setex(f"{self.task_cancel_prefix}{task_id}", 3600, "1")
        
        # Update task status
        task_info = await self.get_task_info(task_id)
        if task_info and task_info.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            task_info.status = TaskStatus.CANCELLED
            task_info.completed_at = datetime.utcnow()
            
            # Update Redis
            await self.redis.setex(
                f"{self.task_info_prefix}{task_id}",
                86400,
                json.dumps(asdict(task_info), default=str)
            )
            
            # Update database
            await self.db.tasks.update_one(
                {"_id": task_id},
                {
                    "$set": {
                        "status": TaskStatus.CANCELLED.value,
                        "completed_at": task_info.completed_at
                    }
                }
            )
            
            # Remove from queue if pending
            await self.redis.zrem(self.queue_key, task_id)
            
            logger.info(f"Cancelled task {task_id}")
            return True
        
        return False
    
    async def is_cancelled(self, task_id: str) -> bool:
        """Check if task is cancelled"""
        cancel_flag = await self.redis.get(f"{self.task_cancel_prefix}{task_id}")
        return cancel_flag is not None
    
    async def start_workers(self):
        """Start task workers"""
        if self.running:
            return
        
        self.running = True
        logger.info(f"Starting {self.max_workers} task workers")
        
        # Start worker tasks
        for i in range(self.max_workers):
            worker_id = f"worker_{i}"
            self.workers[worker_id] = asyncio.create_task(
                self._worker_loop(worker_id)
            )
        
        # Start cleanup task
        self.workers["cleanup"] = asyncio.create_task(self._cleanup_loop())
    
    async def stop_workers(self):
        """Stop task workers"""
        if not self.running:
            return
        
        self.running = False
        logger.info("Stopping task workers")
        
        # Cancel all worker tasks
        for worker_task in self.workers.values():
            worker_task.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers.values(), return_exceptions=True)
        self.workers.clear()
    
    async def _worker_loop(self, worker_id: str):
        """Main worker loop"""
        logger.info(f"Worker {worker_id} started")
        
        while self.running:
            try:
                # Get next task from queue
                task_id = await self._get_next_task()
                if not task_id:
                    await asyncio.sleep(1)  # No tasks available, wait
                    continue
                
                # Process the task
                async with self.worker_semaphore:
                    await self._process_task(task_id, worker_id)
                    
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(5)  # Wait before retrying
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def _get_next_task(self) -> Optional[str]:
        """Get next task from priority queue"""
        # Get highest priority task
        result = await self.redis.zpopmax(self.queue_key)
        if result:
            task_id, priority = result[0]
            
            # Move to processing set
            await self.redis.sadd(self.processing_key, task_id)
            
            return task_id
        
        return None
    
    async def _process_task(self, task_id: str, worker_id: str):
        """Process a single task"""
        task_info = await self.get_task_info(task_id)
        if not task_info:
            logger.error(f"Task {task_id} not found")
            return
        
        # Check if task is cancelled
        if await self.is_cancelled(task_id):
            logger.info(f"Task {task_id} was cancelled before processing")
            return
        
        logger.info(f"Worker {worker_id} processing task {task_id} of type {task_info.task_type}")
        
        # Update task status to running
        task_info.status = TaskStatus.RUNNING
        task_info.started_at = datetime.utcnow()
        await self._update_task_info(task_info)
        
        try:
            # Get task handler
            handler = self.task_handlers.get(task_info.task_type)
            if not handler:
                raise Exception(f"No handler registered for task type: {task_info.task_type}")
            
            # Execute task with timeout
            await asyncio.wait_for(
                handler(task_id, task_info.payload),
                timeout=task_info.timeout
            )
            
            # Mark as completed
            task_info.status = TaskStatus.COMPLETED
            task_info.completed_at = datetime.utcnow()
            task_info.progress = 100.0
            await self._update_task_info(task_info)
            
            logger.info(f"Task {task_id} completed successfully")
            
        except asyncio.TimeoutError:
            logger.error(f"Task {task_id} timed out")
            await self._handle_task_failure(task_info, "Task timed out")
            
        except asyncio.CancelledError:
            logger.info(f"Task {task_id} was cancelled during processing")
            task_info.status = TaskStatus.CANCELLED
            task_info.completed_at = datetime.utcnow()
            await self._update_task_info(task_info)
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            logger.error(traceback.format_exc())
            await self._handle_task_failure(task_info, str(e))
        
        finally:
            # Remove from processing set
            await self.redis.srem(self.processing_key, task_id)
    
    async def _handle_task_failure(self, task_info: TaskInfo, error_message: str):
        """Handle task failure with retry logic"""
        task_info.error_message = error_message
        task_info.retry_count += 1
        
        if task_info.retry_count <= task_info.max_retries:
            # Schedule retry
            task_info.status = TaskStatus.RETRYING
            await self._update_task_info(task_info)
            
            # Calculate retry delay with exponential backoff
            delay = task_info.retry_delay * (2 ** (task_info.retry_count - 1))
            retry_time = datetime.utcnow() + timedelta(seconds=delay)
            
            logger.info(f"Scheduling retry {task_info.retry_count}/{task_info.max_retries} for task {task_info.task_id} in {delay} seconds")
            
            # Schedule retry by adding back to queue with delay
            await asyncio.sleep(delay)
            await self.redis.zadd(
                self.queue_key,
                {task_info.task_id: task_info.priority.value}
            )
            
            # Reset status to pending for retry
            task_info.status = TaskStatus.PENDING
            task_info.started_at = None
            await self._update_task_info(task_info)
            
        else:
            # Max retries exceeded, mark as failed
            task_info.status = TaskStatus.FAILED
            task_info.completed_at = datetime.utcnow()
            await self._update_task_info(task_info)
            
            logger.error(f"Task {task_info.task_id} failed permanently after {task_info.retry_count} retries")
    
    async def _update_task_info(self, task_info: TaskInfo):
        """Update task info in Redis and database"""
        # Update Redis
        await self.redis.setex(
            f"{self.task_info_prefix}{task_info.task_id}",
            86400,
            json.dumps(asdict(task_info), default=str)
        )
        
        # Update database
        update_data = {
            "status": task_info.status.value,
            "retry_count": task_info.retry_count,
            "progress": task_info.progress
        }
        
        if task_info.started_at:
            update_data["started_at"] = task_info.started_at
        if task_info.completed_at:
            update_data["completed_at"] = task_info.completed_at
        if task_info.error_message:
            update_data["error_message"] = task_info.error_message
        
        await self.db.tasks.update_one(
            {"_id": task_info.task_id},
            {"$set": update_data}
        )
    
    async def _cleanup_loop(self):
        """Cleanup expired tasks and progress data"""
        while self.running:
            try:
                # Clean up completed tasks older than 7 days
                cutoff_date = datetime.utcnow() - timedelta(days=7)
                
                # Remove from database
                result = await self.db.tasks.delete_many({
                    "status": {"$in": [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, TaskStatus.CANCELLED.value]},
                    "completed_at": {"$lt": cutoff_date}
                })
                
                if result.deleted_count > 0:
                    logger.info(f"Cleaned up {result.deleted_count} old tasks")
                
                # Clean up orphaned processing tasks (tasks that were processing but worker died)
                processing_tasks = await self.redis.smembers(self.processing_key)
                for task_id in processing_tasks:
                    task_info = await self.get_task_info(task_id.decode() if isinstance(task_id, bytes) else task_id)
                    if task_info and task_info.started_at:
                        # If task has been running for more than 2x timeout, consider it orphaned
                        max_runtime = timedelta(seconds=task_info.timeout * 2)
                        if datetime.utcnow() - task_info.started_at > max_runtime:
                            logger.warning(f"Found orphaned task {task_info.task_id}, requeueing")
                            
                            # Remove from processing and requeue
                            await self.redis.srem(self.processing_key, task_info.task_id)
                            await self.redis.zadd(
                                self.queue_key,
                                {task_info.task_id: task_info.priority.value}
                            )
                            
                            # Reset task status
                            task_info.status = TaskStatus.PENDING
                            task_info.started_at = None
                            await self._update_task_info(task_info)
                
                # Sleep for 5 minutes before next cleanup
                await asyncio.sleep(300)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        pending_count = await self.redis.zcard(self.queue_key)
        processing_count = await self.redis.scard(self.processing_key)
        
        # Get task counts by status from database
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        status_counts = {}
        async for doc in self.db.tasks.aggregate(pipeline):
            status_counts[doc["_id"]] = doc["count"]
        
        return {
            "pending": pending_count,
            "processing": processing_count,
            "workers_running": len([w for w in self.workers.values() if not w.done()]),
            "status_counts": status_counts,
            "queue_running": self.running
        }


# Global task queue instance
_task_queue: Optional[TaskQueue] = None


async def get_task_queue() -> TaskQueue:
    """Get global task queue instance"""
    global _task_queue
    if _task_queue is None:
        redis_client = await get_redis()
        db = await get_database()
        _task_queue = TaskQueue(redis_client, db)
    return _task_queue


async def initialize_task_queue():
    """Initialize and start the task queue"""
    task_queue = await get_task_queue()
    await task_queue.start_workers()
    return task_queue


async def shutdown_task_queue():
    """Shutdown the task queue"""
    global _task_queue
    if _task_queue:
        await _task_queue.stop_workers()
        _task_queue = None