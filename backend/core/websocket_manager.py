"""
WebSocket connection manager for real-time communication
"""
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from fastapi import WebSocket, WebSocketDisconnect
from enum import Enum

from ..models.user import UserInDB
from .database import get_redis
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('websocket_manager')


class MessageType(str, Enum):
    """WebSocket message types"""
    ANALYSIS_PROGRESS = "analysis_progress"
    ANALYSIS_COMPLETED = "analysis_completed"
    ANALYSIS_FAILED = "analysis_failed"
    ANALYSIS_CANCELLED = "analysis_cancelled"
    SYSTEM_NOTIFICATION = "system_notification"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    AUTHENTICATION = "authentication"


class ConnectionStatus(str, Enum):
    """Connection status"""
    CONNECTING = "connecting"
    AUTHENTICATED = "authenticated"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class WebSocketConnection:
    """Represents a WebSocket connection"""
    
    def __init__(self, websocket: WebSocket, connection_id: str):
        self.websocket = websocket
        self.connection_id = connection_id
        self.user_id: Optional[str] = None
        self.user: Optional[UserInDB] = None
        self.status = ConnectionStatus.CONNECTING
        self.subscriptions: Set[str] = set()  # Analysis IDs or channels
        self.created_at = datetime.utcnow()
        self.last_heartbeat = datetime.utcnow()
        self.metadata: Dict[str, Any] = {}
    
    async def send_message(self, message_type: MessageType, data: Dict[str, Any]):
        """Send a message to the client"""
        try:
            message = {
                "type": message_type.value,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
                "connection_id": self.connection_id
            }
            await self.websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message to {self.connection_id}: {e}")
            raise
    
    async def send_error(self, error_message: str, error_code: str = "GENERAL_ERROR"):
        """Send an error message to the client"""
        await self.send_message(MessageType.ERROR, {
            "error_code": error_code,
            "error_message": error_message
        })
    
    def is_authenticated(self) -> bool:
        """Check if connection is authenticated"""
        return self.status == ConnectionStatus.AUTHENTICATED and self.user is not None
    
    def subscribe_to_analysis(self, analysis_id: str):
        """Subscribe to analysis updates"""
        self.subscriptions.add(f"analysis:{analysis_id}")
    
    def unsubscribe_from_analysis(self, analysis_id: str):
        """Unsubscribe from analysis updates"""
        self.subscriptions.discard(f"analysis:{analysis_id}")
    
    def subscribe_to_notifications(self):
        """Subscribe to system notifications"""
        self.subscriptions.add("notifications")
    
    def is_subscribed_to(self, channel: str) -> bool:
        """Check if connection is subscribed to a channel"""
        return channel in self.subscriptions


class WebSocketManager:
    """Manages WebSocket connections and message broadcasting"""
    
    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.analysis_subscribers: Dict[str, Set[str]] = {}  # analysis_id -> connection_ids
        self.notification_subscribers: Set[str] = set()  # connection_ids subscribed to notifications
        self.redis_client = None
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.redis_listener_task: Optional[asyncio.Task] = None
    
    async def initialize(self):
        """Initialize the WebSocket manager"""
        self.redis_client = await get_redis()
        
        # Start background tasks
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self.redis_listener_task = asyncio.create_task(self._redis_listener_loop())
        
        logger.info("WebSocket manager initialized")
    
    async def shutdown(self):
        """Shutdown the WebSocket manager"""
        # Cancel background tasks
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        if self.redis_listener_task:
            self.redis_listener_task.cancel()
        
        # Close all connections
        for connection in list(self.connections.values()):
            await self.disconnect(connection.connection_id)
        
        logger.info("WebSocket manager shutdown")
    
    async def connect(self, websocket: WebSocket) -> str:
        """Accept a new WebSocket connection"""
        connection_id = str(uuid.uuid4())
        
        await websocket.accept()
        
        connection = WebSocketConnection(websocket, connection_id)
        self.connections[connection_id] = connection
        
        logger.info(f"WebSocket connection {connection_id} established")
        
        # Send connection confirmation
        await connection.send_message(MessageType.AUTHENTICATION, {
            "connection_id": connection_id,
            "status": "connected",
            "message": "Please authenticate to continue"
        })
        
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """Disconnect a WebSocket connection"""
        connection = self.connections.get(connection_id)
        if not connection:
            return
        
        # Remove from user connections
        if connection.user_id:
            user_connections = self.user_connections.get(connection.user_id, set())
            user_connections.discard(connection_id)
            if not user_connections:
                del self.user_connections[connection.user_id]
        
        # Remove from subscriptions
        for subscription in connection.subscriptions:
            if subscription.startswith("analysis:"):
                analysis_id = subscription.replace("analysis:", "")
                subscribers = self.analysis_subscribers.get(analysis_id, set())
                subscribers.discard(connection_id)
                if not subscribers:
                    del self.analysis_subscribers[analysis_id]
            elif subscription == "notifications":
                self.notification_subscribers.discard(connection_id)
        
        # Close WebSocket
        try:
            await connection.websocket.close()
        except Exception:
            pass  # Connection might already be closed
        
        # Remove from connections
        del self.connections[connection_id]
        
        logger.info(f"WebSocket connection {connection_id} disconnected")
    
    async def authenticate_connection(self, connection_id: str, user: UserInDB) -> bool:
        """Authenticate a WebSocket connection"""
        connection = self.connections.get(connection_id)
        if not connection:
            return False
        
        connection.user = user
        connection.user_id = str(user.id)
        connection.status = ConnectionStatus.AUTHENTICATED
        
        # Add to user connections
        if connection.user_id not in self.user_connections:
            self.user_connections[connection.user_id] = set()
        self.user_connections[connection.user_id].add(connection_id)
        
        # Send authentication success
        await connection.send_message(MessageType.AUTHENTICATION, {
            "status": "authenticated",
            "user_id": connection.user_id,
            "username": user.username
        })
        
        logger.info(f"WebSocket connection {connection_id} authenticated for user {user.username}")
        return True
    
    async def handle_message(self, connection_id: str, message: str):
        """Handle incoming WebSocket message"""
        connection = self.connections.get(connection_id)
        if not connection:
            return
        
        try:
            data = json.loads(message)
            message_type = data.get("type")
            payload = data.get("data", {})
            
            if message_type == "heartbeat":
                await self._handle_heartbeat(connection)
            elif message_type == "subscribe_analysis":
                await self._handle_subscribe_analysis(connection, payload)
            elif message_type == "unsubscribe_analysis":
                await self._handle_unsubscribe_analysis(connection, payload)
            elif message_type == "subscribe_notifications":
                await self._handle_subscribe_notifications(connection)
            else:
                await connection.send_error(f"Unknown message type: {message_type}", "UNKNOWN_MESSAGE_TYPE")
                
        except json.JSONDecodeError:
            await connection.send_error("Invalid JSON message", "INVALID_JSON")
        except Exception as e:
            logger.error(f"Error handling message from {connection_id}: {e}")
            await connection.send_error("Internal server error", "INTERNAL_ERROR")
    
    async def _handle_heartbeat(self, connection: WebSocketConnection):
        """Handle heartbeat message"""
        connection.last_heartbeat = datetime.utcnow()
        await connection.send_message(MessageType.HEARTBEAT, {
            "status": "alive",
            "server_time": datetime.utcnow().isoformat()
        })
    
    async def _handle_subscribe_analysis(self, connection: WebSocketConnection, payload: Dict[str, Any]):
        """Handle analysis subscription"""
        if not connection.is_authenticated():
            await connection.send_error("Authentication required", "AUTHENTICATION_REQUIRED")
            return
        
        analysis_id = payload.get("analysis_id")
        if not analysis_id:
            await connection.send_error("Analysis ID required", "MISSING_ANALYSIS_ID")
            return
        
        # TODO: Verify user has access to this analysis
        
        connection.subscribe_to_analysis(analysis_id)
        
        # Add to analysis subscribers
        if analysis_id not in self.analysis_subscribers:
            self.analysis_subscribers[analysis_id] = set()
        self.analysis_subscribers[analysis_id].add(connection.connection_id)
        
        await connection.send_message(MessageType.ANALYSIS_PROGRESS, {
            "analysis_id": analysis_id,
            "status": "subscribed",
            "message": f"Subscribed to analysis {analysis_id}"
        })
    
    async def _handle_unsubscribe_analysis(self, connection: WebSocketConnection, payload: Dict[str, Any]):
        """Handle analysis unsubscription"""
        analysis_id = payload.get("analysis_id")
        if not analysis_id:
            await connection.send_error("Analysis ID required", "MISSING_ANALYSIS_ID")
            return
        
        connection.unsubscribe_from_analysis(analysis_id)
        
        # Remove from analysis subscribers
        subscribers = self.analysis_subscribers.get(analysis_id, set())
        subscribers.discard(connection.connection_id)
        if not subscribers:
            del self.analysis_subscribers[analysis_id]
        
        await connection.send_message(MessageType.ANALYSIS_PROGRESS, {
            "analysis_id": analysis_id,
            "status": "unsubscribed",
            "message": f"Unsubscribed from analysis {analysis_id}"
        })
    
    async def _handle_subscribe_notifications(self, connection: WebSocketConnection):
        """Handle notification subscription"""
        if not connection.is_authenticated():
            await connection.send_error("Authentication required", "AUTHENTICATION_REQUIRED")
            return
        
        connection.subscribe_to_notifications()
        self.notification_subscribers.add(connection.connection_id)
        
        await connection.send_message(MessageType.SYSTEM_NOTIFICATION, {
            "status": "subscribed",
            "message": "Subscribed to system notifications"
        })
    
    async def broadcast_analysis_progress(
        self,
        analysis_id: str,
        progress: float,
        message: Optional[str] = None,
        current_step: Optional[str] = None
    ):
        """Broadcast analysis progress to subscribers"""
        subscribers = self.analysis_subscribers.get(analysis_id, set())
        if not subscribers:
            return
        
        data = {
            "analysis_id": analysis_id,
            "progress": progress,
            "message": message,
            "current_step": current_step,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to all subscribers
        for connection_id in list(subscribers):  # Use list() to avoid modification during iteration
            connection = self.connections.get(connection_id)
            if connection:
                try:
                    await connection.send_message(MessageType.ANALYSIS_PROGRESS, data)
                except Exception as e:
                    logger.error(f"Failed to send progress to {connection_id}: {e}")
                    # Remove failed connection
                    await self.disconnect(connection_id)
    
    async def broadcast_analysis_completed(self, analysis_id: str, result_summary: Dict[str, Any]):
        """Broadcast analysis completion to subscribers"""
        subscribers = self.analysis_subscribers.get(analysis_id, set())
        if not subscribers:
            return
        
        data = {
            "analysis_id": analysis_id,
            "status": "completed",
            "result_summary": result_summary,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for connection_id in list(subscribers):
            connection = self.connections.get(connection_id)
            if connection:
                try:
                    await connection.send_message(MessageType.ANALYSIS_COMPLETED, data)
                except Exception as e:
                    logger.error(f"Failed to send completion to {connection_id}: {e}")
                    await self.disconnect(connection_id)
    
    async def broadcast_analysis_failed(self, analysis_id: str, error_message: str):
        """Broadcast analysis failure to subscribers"""
        subscribers = self.analysis_subscribers.get(analysis_id, set())
        if not subscribers:
            return
        
        data = {
            "analysis_id": analysis_id,
            "status": "failed",
            "error_message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for connection_id in list(subscribers):
            connection = self.connections.get(connection_id)
            if connection:
                try:
                    await connection.send_message(MessageType.ANALYSIS_FAILED, data)
                except Exception as e:
                    logger.error(f"Failed to send failure to {connection_id}: {e}")
                    await self.disconnect(connection_id)
    
    async def broadcast_system_notification(self, message: str, notification_type: str = "info"):
        """Broadcast system notification to all subscribers"""
        if not self.notification_subscribers:
            return
        
        data = {
            "type": notification_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for connection_id in list(self.notification_subscribers):
            connection = self.connections.get(connection_id)
            if connection:
                try:
                    await connection.send_message(MessageType.SYSTEM_NOTIFICATION, data)
                except Exception as e:
                    logger.error(f"Failed to send notification to {connection_id}: {e}")
                    await self.disconnect(connection_id)
    
    async def send_to_user(self, user_id: str, message_type: MessageType, data: Dict[str, Any]):
        """Send message to all connections of a specific user"""
        user_connections = self.user_connections.get(user_id, set())
        
        for connection_id in list(user_connections):
            connection = self.connections.get(connection_id)
            if connection:
                try:
                    await connection.send_message(message_type, data)
                except Exception as e:
                    logger.error(f"Failed to send message to user {user_id} connection {connection_id}: {e}")
                    await self.disconnect(connection_id)
    
    async def _heartbeat_loop(self):
        """Background task to check connection health"""
        while True:
            try:
                current_time = datetime.utcnow()
                timeout_threshold = 300  # 5 minutes
                
                # Check for stale connections
                stale_connections = []
                for connection_id, connection in self.connections.items():
                    time_since_heartbeat = (current_time - connection.last_heartbeat).total_seconds()
                    if time_since_heartbeat > timeout_threshold:
                        stale_connections.append(connection_id)
                
                # Disconnect stale connections
                for connection_id in stale_connections:
                    logger.warning(f"Disconnecting stale connection {connection_id}")
                    await self.disconnect(connection_id)
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
                await asyncio.sleep(60)
    
    async def _redis_listener_loop(self):
        """Background task to listen for Redis pub/sub messages"""
        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe("websocket_broadcast")
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await self._handle_redis_message(data)
                    except Exception as e:
                        logger.error(f"Error handling Redis message: {e}")
                        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Redis listener error: {e}")
    
    async def _handle_redis_message(self, data: Dict[str, Any]):
        """Handle messages from Redis pub/sub"""
        message_type = data.get("type")
        
        if message_type == "analysis_progress":
            await self.broadcast_analysis_progress(
                data["analysis_id"],
                data["progress"],
                data.get("message"),
                data.get("current_step")
            )
        elif message_type == "analysis_completed":
            await self.broadcast_analysis_completed(
                data["analysis_id"],
                data["result_summary"]
            )
        elif message_type == "analysis_failed":
            await self.broadcast_analysis_failed(
                data["analysis_id"],
                data["error_message"]
            )
        elif message_type == "system_notification":
            await self.broadcast_system_notification(
                data["message"],
                data.get("notification_type", "info")
            )
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        return {
            "total_connections": len(self.connections),
            "authenticated_connections": len([c for c in self.connections.values() if c.is_authenticated()]),
            "unique_users": len(self.user_connections),
            "analysis_subscriptions": len(self.analysis_subscribers),
            "notification_subscribers": len(self.notification_subscribers)
        }


# Global WebSocket manager instance
_websocket_manager: Optional[WebSocketManager] = None


async def get_websocket_manager() -> WebSocketManager:
    """Get global WebSocket manager instance"""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
        await _websocket_manager.initialize()
    return _websocket_manager


async def shutdown_websocket_manager():
    """Shutdown the WebSocket manager"""
    global _websocket_manager
    if _websocket_manager:
        await _websocket_manager.shutdown()
        _websocket_manager = None