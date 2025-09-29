"""
WebSocket API endpoints for real-time communication
"""
import asyncio
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.security import HTTPBearer
from jose import JWTError, jwt

from ...models.user import UserInDB
from ...core.websocket_manager import get_websocket_manager, WebSocketManager
from ...core.security import get_user_by_id
from ...core.auth import verify_token
from ...app.config import settings
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('websocket_api')

router = APIRouter()
security = HTTPBearer()


async def authenticate_websocket_user(token: str) -> Optional[UserInDB]:
    """Authenticate user from WebSocket token"""
    try:
        # Verify JWT token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        # Get user from database
        user = await get_user_by_id(user_id)
        return user
        
    except JWTError:
        return None
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        return None


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    ws_manager: WebSocketManager = Depends(get_websocket_manager)
):
    """
    WebSocket endpoint for real-time communication
    
    Query parameters:
    - token: JWT authentication token (optional, can be sent after connection)
    """
    connection_id = None
    
    try:
        # Accept connection
        connection_id = await ws_manager.connect(websocket)
        logger.info(f"WebSocket connection {connection_id} established")
        
        # Authenticate if token provided in query
        if token:
            user = await authenticate_websocket_user(token)
            if user:
                await ws_manager.authenticate_connection(connection_id, user)
            else:
                await websocket.send_text('{"type": "error", "data": {"error_code": "INVALID_TOKEN", "error_message": "Invalid authentication token"}}')
        
        # Message handling loop
        while True:
            try:
                # Wait for message with timeout
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Handle authentication message
                if not ws_manager.connections[connection_id].is_authenticated():
                    await handle_authentication_message(connection_id, message, ws_manager)
                else:
                    # Handle regular messages
                    await ws_manager.handle_message(connection_id, message)
                    
            except asyncio.TimeoutError:
                # Send heartbeat request
                await websocket.send_text('{"type": "heartbeat_request", "data": {}}')
                continue
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket connection {connection_id} disconnected by client")
    except Exception as e:
        logger.error(f"WebSocket connection {connection_id} error: {e}")
    finally:
        if connection_id:
            await ws_manager.disconnect(connection_id)


async def handle_authentication_message(
    connection_id: str, 
    message: str, 
    ws_manager: WebSocketManager
):
    """Handle authentication message for unauthenticated connections"""
    try:
        import json
        data = json.loads(message)
        
        if data.get("type") == "authenticate":
            token = data.get("data", {}).get("token")
            if not token:
                await ws_manager.connections[connection_id].send_error(
                    "Authentication token required", 
                    "MISSING_TOKEN"
                )
                return
            
            user = await authenticate_websocket_user(token)
            if user:
                await ws_manager.authenticate_connection(connection_id, user)
            else:
                await ws_manager.connections[connection_id].send_error(
                    "Invalid authentication token", 
                    "INVALID_TOKEN"
                )
        else:
            await ws_manager.connections[connection_id].send_error(
                "Authentication required", 
                "AUTHENTICATION_REQUIRED"
            )
            
    except json.JSONDecodeError:
        await ws_manager.connections[connection_id].send_error(
            "Invalid JSON message", 
            "INVALID_JSON"
        )
    except Exception as e:
        logger.error(f"Authentication message error: {e}")
        await ws_manager.connections[connection_id].send_error(
            "Internal server error", 
            "INTERNAL_ERROR"
        )


@router.websocket("/ws/analysis/{analysis_id}")
async def analysis_websocket_endpoint(
    websocket: WebSocket,
    analysis_id: str,
    token: Optional[str] = Query(None),
    ws_manager: WebSocketManager = Depends(get_websocket_manager)
):
    """
    WebSocket endpoint for specific analysis progress updates
    
    This endpoint automatically subscribes to the specified analysis.
    """
    connection_id = None
    
    try:
        # Accept connection
        connection_id = await ws_manager.connect(websocket)
        logger.info(f"Analysis WebSocket connection {connection_id} established for analysis {analysis_id}")
        
        # Authenticate
        user = None
        if token:
            user = await authenticate_websocket_user(token)
        
        if not user:
            await websocket.send_text('{"type": "error", "data": {"error_code": "AUTHENTICATION_REQUIRED", "error_message": "Authentication required"}}')
            return
        
        await ws_manager.authenticate_connection(connection_id, user)
        
        # TODO: Verify user has access to this analysis
        # For now, we'll assume they do if they're authenticated
        
        # Auto-subscribe to analysis
        connection = ws_manager.connections[connection_id]
        connection.subscribe_to_analysis(analysis_id)
        
        if analysis_id not in ws_manager.analysis_subscribers:
            ws_manager.analysis_subscribers[analysis_id] = set()
        ws_manager.analysis_subscribers[analysis_id].add(connection_id)
        
        # Send subscription confirmation
        await connection.send_message("analysis_progress", {
            "analysis_id": analysis_id,
            "status": "subscribed",
            "message": f"Subscribed to analysis {analysis_id}"
        })
        
        # Message handling loop
        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                await ws_manager.handle_message(connection_id, message)
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_text('{"type": "heartbeat_request", "data": {}}')
                continue
                
    except WebSocketDisconnect:
        logger.info(f"Analysis WebSocket connection {connection_id} disconnected")
    except Exception as e:
        logger.error(f"Analysis WebSocket connection {connection_id} error: {e}")
    finally:
        if connection_id:
            await ws_manager.disconnect(connection_id)


@router.get("/ws/stats")
async def get_websocket_stats(
    ws_manager: WebSocketManager = Depends(get_websocket_manager)
):
    """
    Get WebSocket connection statistics (admin only)
    """
    # TODO: Add admin permission check
    return ws_manager.get_connection_stats()


@router.post("/ws/broadcast")
async def broadcast_message(
    message: str,
    message_type: str = "info",
    ws_manager: WebSocketManager = Depends(get_websocket_manager)
):
    """
    Broadcast system notification to all connected clients (admin only)
    """
    # TODO: Add admin permission check
    await ws_manager.broadcast_system_notification(message, message_type)
    return {"message": "Broadcast sent successfully"}


@router.post("/ws/analysis/{analysis_id}/notify")
async def notify_analysis_subscribers(
    analysis_id: str,
    message: str,
    ws_manager: WebSocketManager = Depends(get_websocket_manager)
):
    """
    Send notification to analysis subscribers (internal use)
    """
    # TODO: Add internal API authentication
    await ws_manager.broadcast_analysis_progress(
        analysis_id, 
        progress=None,  # Don't update progress, just send message
        message=message
    )
    return {"message": "Notification sent successfully"}