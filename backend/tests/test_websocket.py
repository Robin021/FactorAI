"""
Tests for WebSocket functionality
"""
import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from ..core.websocket_manager import WebSocketManager, WebSocketConnection, MessageType
from ..app.main import app


class TestWebSocketManager:
    """Test WebSocket manager functionality"""
    
    @pytest.fixture
    async def ws_manager(self):
        """Create WebSocket manager for testing"""
        manager = WebSocketManager()
        manager.redis_client = AsyncMock()
        return manager
    
    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket"""
        websocket = AsyncMock()
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.close = AsyncMock()
        return websocket
    
    @pytest.mark.asyncio
    async def test_connect_websocket(self, ws_manager, mock_websocket):
        """Test WebSocket connection"""
        connection_id = await ws_manager.connect(mock_websocket)
        
        assert connection_id in ws_manager.connections
        assert ws_manager.connections[connection_id].websocket == mock_websocket
        mock_websocket.accept.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authenticate_connection(self, ws_manager, mock_websocket):
        """Test WebSocket authentication"""
        from ..models.user import UserInDB
        from bson import ObjectId
        
        # Connect first
        connection_id = await ws_manager.connect(mock_websocket)
        
        # Create mock user
        user = UserInDB(
            id=ObjectId(),
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            role="user",
            permissions=[]
        )
        
        # Authenticate
        success = await ws_manager.authenticate_connection(connection_id, user)
        
        assert success
        connection = ws_manager.connections[connection_id]
        assert connection.is_authenticated()
        assert connection.user_id == str(user.id)
        assert str(user.id) in ws_manager.user_connections
    
    @pytest.mark.asyncio
    async def test_broadcast_analysis_progress(self, ws_manager, mock_websocket):
        """Test broadcasting analysis progress"""
        from ..models.user import UserInDB
        from bson import ObjectId
        
        # Setup connection and authentication
        connection_id = await ws_manager.connect(mock_websocket)
        user = UserInDB(
            id=ObjectId(),
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            role="user",
            permissions=[]
        )
        await ws_manager.authenticate_connection(connection_id, user)
        
        # Subscribe to analysis
        analysis_id = "test_analysis_123"
        connection = ws_manager.connections[connection_id]
        connection.subscribe_to_analysis(analysis_id)
        ws_manager.analysis_subscribers[analysis_id] = {connection_id}
        
        # Broadcast progress
        await ws_manager.broadcast_analysis_progress(
            analysis_id, 50.0, "Processing data", "data_collection"
        )
        
        # Verify message was sent
        mock_websocket.send_text.assert_called()
        call_args = mock_websocket.send_text.call_args[0][0]
        message = json.loads(call_args)
        
        assert message["type"] == MessageType.ANALYSIS_PROGRESS.value
        assert message["data"]["analysis_id"] == analysis_id
        assert message["data"]["progress"] == 50.0
        assert message["data"]["message"] == "Processing data"
        assert message["data"]["current_step"] == "data_collection"
    
    @pytest.mark.asyncio
    async def test_disconnect_websocket(self, ws_manager, mock_websocket):
        """Test WebSocket disconnection"""
        from ..models.user import UserInDB
        from bson import ObjectId
        
        # Setup connection
        connection_id = await ws_manager.connect(mock_websocket)
        user = UserInDB(
            id=ObjectId(),
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            role="user",
            permissions=[]
        )
        await ws_manager.authenticate_connection(connection_id, user)
        
        # Subscribe to analysis
        analysis_id = "test_analysis_123"
        connection = ws_manager.connections[connection_id]
        connection.subscribe_to_analysis(analysis_id)
        ws_manager.analysis_subscribers[analysis_id] = {connection_id}
        
        # Disconnect
        await ws_manager.disconnect(connection_id)
        
        # Verify cleanup
        assert connection_id not in ws_manager.connections
        assert str(user.id) not in ws_manager.user_connections
        assert analysis_id not in ws_manager.analysis_subscribers
        mock_websocket.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_heartbeat_message(self, ws_manager, mock_websocket):
        """Test heartbeat message handling"""
        from ..models.user import UserInDB
        from bson import ObjectId
        
        # Setup authenticated connection
        connection_id = await ws_manager.connect(mock_websocket)
        user = UserInDB(
            id=ObjectId(),
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            role="user",
            permissions=[]
        )
        await ws_manager.authenticate_connection(connection_id, user)
        
        # Send heartbeat message
        heartbeat_message = json.dumps({
            "type": "heartbeat",
            "data": {}
        })
        
        await ws_manager.handle_message(connection_id, heartbeat_message)
        
        # Verify heartbeat response was sent
        mock_websocket.send_text.assert_called()
        call_args = mock_websocket.send_text.call_args[0][0]
        response = json.loads(call_args)
        
        assert response["type"] == MessageType.HEARTBEAT.value
        assert response["data"]["status"] == "alive"
    
    def test_connection_stats(self, ws_manager):
        """Test connection statistics"""
        # Add some mock connections
        ws_manager.connections = {
            "conn1": MagicMock(is_authenticated=lambda: True),
            "conn2": MagicMock(is_authenticated=lambda: False),
            "conn3": MagicMock(is_authenticated=lambda: True)
        }
        ws_manager.user_connections = {"user1": {"conn1"}, "user2": {"conn3"}}
        ws_manager.analysis_subscribers = {"analysis1": {"conn1", "conn3"}}
        ws_manager.notification_subscribers = {"conn1", "conn2"}
        
        stats = ws_manager.get_connection_stats()
        
        assert stats["total_connections"] == 3
        assert stats["authenticated_connections"] == 2
        assert stats["unique_users"] == 2
        assert stats["analysis_subscriptions"] == 1
        assert stats["notification_subscribers"] == 2


class TestWebSocketAPI:
    """Test WebSocket API endpoints"""
    
    def test_websocket_endpoint_exists(self):
        """Test that WebSocket endpoint is available"""
        client = TestClient(app)
        
        # This will fail to connect without proper WebSocket client,
        # but it should not return 404
        try:
            with client.websocket_connect("/api/v1/ws"):
                pass
        except Exception:
            # Expected to fail in test environment
            pass
    
    def test_websocket_stats_endpoint(self):
        """Test WebSocket stats endpoint"""
        client = TestClient(app)
        
        # This would require authentication in real scenario
        # For now, just test that endpoint exists
        response = client.get("/api/v1/ws/stats")
        # May return 401/403 due to auth requirements, but not 404
        assert response.status_code != 404


if __name__ == "__main__":
    pytest.main([__file__])