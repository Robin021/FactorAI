"""
Tests for analysis API endpoints
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock

from ..models.analysis import AnalysisStatus, MarketType


class TestAnalysisStart:
    """Test analysis start endpoint"""
    
    def test_start_analysis_success(self, test_client, auth_headers):
        """Test successful analysis start"""
        analysis_data = {
            "stock_code": "AAPL",
            "market_type": "us",
            "analysts": ["market", "news"],
            "analysis_date": "2024-01-15"
        }
        
        response = test_client.post("/api/v1/analysis/start", json=analysis_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["stock_code"] == "AAPL"
        assert data["market_type"] == "us"
        assert data["status"] == "pending"
        assert "id" in data
    
    def test_start_analysis_invalid_stock_code(self, test_client, auth_headers):
        """Test analysis start with invalid stock code"""
        analysis_data = {
            "stock_code": "INVALID123",
            "market_type": "us"
        }
        
        response = test_client.post("/api/v1/analysis/start", json=analysis_data, headers=auth_headers)
        
        assert response.status_code == 400
        assert "Invalid stock code format" in response.json()["detail"]
    
    def test_start_analysis_without_permission(self, test_client):
        """Test analysis start without permission"""
        analysis_data = {
            "stock_code": "AAPL",
            "market_type": "us"
        }
        
        response = test_client.post("/api/v1/analysis/start", json=analysis_data)
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_start_analysis_rate_limit(self, test_client, auth_headers, test_db):
        """Test analysis rate limiting"""
        # Create 5 pending analyses to hit the limit
        from ..models.analysis import AnalysisInDB, AnalysisStatus, MarketType
        from ..models.user import UserInDB
        
        # Get test user
        user_doc = await test_db.users.find_one({"username": "testuser"})
        user = UserInDB(**user_doc)
        
        for i in range(5):
            analysis = AnalysisInDB(
                user_id=user.id,
                stock_code=f"TEST{i}",
                market_type=MarketType.US,
                status=AnalysisStatus.PENDING
            )
            await test_db.analyses.insert_one(analysis.dict(by_alias=True))
        
        analysis_data = {
            "stock_code": "AAPL",
            "market_type": "us"
        }
        
        response = test_client.post("/api/v1/analysis/start", json=analysis_data, headers=auth_headers)
        
        assert response.status_code == 429
        assert "Too many active analyses" in response.json()["detail"]


class TestAnalysisStatus:
    """Test analysis status endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_analysis_status_success(self, test_client, auth_headers, test_db):
        """Test successful status retrieval"""
        # Create test analysis
        from ..models.analysis import AnalysisInDB, AnalysisStatus, MarketType
        from ..models.user import UserInDB
        
        user_doc = await test_db.users.find_one({"username": "testuser"})
        user = UserInDB(**user_doc)
        
        analysis = AnalysisInDB(
            user_id=user.id,
            stock_code="AAPL",
            market_type=MarketType.US,
            status=AnalysisStatus.RUNNING,
            progress=50.0
        )
        
        result = await test_db.analyses.insert_one(analysis.dict(by_alias=True))
        analysis_id = str(result.inserted_id)
        
        response = test_client.get(f"/api/v1/analysis/{analysis_id}/status", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["progress"] == 50.0
    
    def test_get_analysis_status_not_found(self, test_client, auth_headers):
        """Test status retrieval for non-existent analysis"""
        from bson import ObjectId
        fake_id = str(ObjectId())
        
        response = test_client.get(f"/api/v1/analysis/{fake_id}/status", headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_get_analysis_status_invalid_id(self, test_client, auth_headers):
        """Test status retrieval with invalid ID format"""
        response = test_client.get("/api/v1/analysis/invalid_id/status", headers=auth_headers)
        
        assert response.status_code == 400
        assert "Invalid analysis ID format" in response.json()["detail"]


class TestAnalysisResult:
    """Test analysis result endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_analysis_result_success(self, test_client, auth_headers, test_db):
        """Test successful result retrieval"""
        from ..models.analysis import AnalysisInDB, AnalysisStatus, AnalysisResult, MarketType
        from ..models.user import UserInDB
        
        user_doc = await test_db.users.find_one({"username": "testuser"})
        user = UserInDB(**user_doc)
        
        result_data = AnalysisResult(
            summary={"recommendation": "BUY", "confidence_score": 0.8},
            technical_analysis={"trend": "bullish"},
            fundamental_analysis={"pe_ratio": 25.5}
        )
        
        analysis = AnalysisInDB(
            user_id=user.id,
            stock_code="AAPL",
            market_type=MarketType.US,
            status=AnalysisStatus.COMPLETED,
            progress=100.0,
            result_data=result_data
        )
        
        result = await test_db.analyses.insert_one(analysis.dict(by_alias=True))
        analysis_id = str(result.inserted_id)
        
        response = test_client.get(f"/api/v1/analysis/{analysis_id}/result", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["result_data"]["summary"]["recommendation"] == "BUY"
    
    @pytest.mark.asyncio
    async def test_get_analysis_result_not_completed(self, test_client, auth_headers, test_db):
        """Test result retrieval for incomplete analysis"""
        from ..models.analysis import AnalysisInDB, AnalysisStatus, MarketType
        from ..models.user import UserInDB
        
        user_doc = await test_db.users.find_one({"username": "testuser"})
        user = UserInDB(**user_doc)
        
        analysis = AnalysisInDB(
            user_id=user.id,
            stock_code="AAPL",
            market_type=MarketType.US,
            status=AnalysisStatus.RUNNING,
            progress=50.0
        )
        
        result = await test_db.analyses.insert_one(analysis.dict(by_alias=True))
        analysis_id = str(result.inserted_id)
        
        response = test_client.get(f"/api/v1/analysis/{analysis_id}/result", headers=auth_headers)
        
        assert response.status_code == 400
        assert "Analysis is not completed" in response.json()["detail"]


class TestAnalysisHistory:
    """Test analysis history endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_analysis_history_success(self, test_client, auth_headers, test_db):
        """Test successful history retrieval"""
        from ..models.analysis import AnalysisInDB, AnalysisStatus, MarketType
        from ..models.user import UserInDB
        
        user_doc = await test_db.users.find_one({"username": "testuser"})
        user = UserInDB(**user_doc)
        
        # Create multiple analyses
        for i in range(3):
            analysis = AnalysisInDB(
                user_id=user.id,
                stock_code=f"TEST{i}",
                market_type=MarketType.US,
                status=AnalysisStatus.COMPLETED,
                progress=100.0
            )
            await test_db.analyses.insert_one(analysis.dict(by_alias=True))
        
        response = test_client.get("/api/v1/analysis/history", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["analyses"]) == 3
        assert data["total"] == 3
        assert data["page"] == 1
    
    def test_get_analysis_history_with_filters(self, test_client, auth_headers):
        """Test history retrieval with filters"""
        params = {
            "stock_code": "AAPL",
            "market_type": "us",
            "status": "completed",
            "page": 1,
            "page_size": 10
        }
        
        response = test_client.get("/api/v1/analysis/history", params=params, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["analyses"], list)


class TestAnalysisDelete:
    """Test analysis delete endpoint"""
    
    @pytest.mark.asyncio
    async def test_delete_analysis_success(self, test_client, auth_headers, test_db):
        """Test successful analysis deletion"""
        from ..models.analysis import AnalysisInDB, AnalysisStatus, MarketType
        from ..models.user import UserInDB
        
        user_doc = await test_db.users.find_one({"username": "testuser"})
        user = UserInDB(**user_doc)
        
        analysis = AnalysisInDB(
            user_id=user.id,
            stock_code="AAPL",
            market_type=MarketType.US,
            status=AnalysisStatus.COMPLETED,
            progress=100.0
        )
        
        result = await test_db.analyses.insert_one(analysis.dict(by_alias=True))
        analysis_id = str(result.inserted_id)
        
        response = test_client.delete(f"/api/v1/analysis/{analysis_id}", headers=auth_headers)
        
        assert response.status_code == 200
        assert "Analysis deleted successfully" in response.json()["message"]
        
        # Verify deletion
        deleted_analysis = await test_db.analyses.find_one({"_id": result.inserted_id})
        assert deleted_analysis is None
    
    @pytest.mark.asyncio
    async def test_delete_running_analysis_forbidden(self, test_client, auth_headers, test_db):
        """Test deletion of running analysis is forbidden"""
        from ..models.analysis import AnalysisInDB, AnalysisStatus, MarketType
        from ..models.user import UserInDB
        
        user_doc = await test_db.users.find_one({"username": "testuser"})
        user = UserInDB(**user_doc)
        
        analysis = AnalysisInDB(
            user_id=user.id,
            stock_code="AAPL",
            market_type=MarketType.US,
            status=AnalysisStatus.RUNNING,
            progress=50.0
        )
        
        result = await test_db.analyses.insert_one(analysis.dict(by_alias=True))
        analysis_id = str(result.inserted_id)
        
        response = test_client.delete(f"/api/v1/analysis/{analysis_id}", headers=auth_headers)
        
        assert response.status_code == 400
        assert "Cannot delete running analysis" in response.json()["detail"]


class TestAnalysisCancel:
    """Test analysis cancel endpoint"""
    
    @pytest.mark.asyncio
    async def test_cancel_analysis_success(self, test_client, auth_headers, test_db):
        """Test successful analysis cancellation"""
        from ..models.analysis import AnalysisInDB, AnalysisStatus, MarketType
        from ..models.user import UserInDB
        
        user_doc = await test_db.users.find_one({"username": "testuser"})
        user = UserInDB(**user_doc)
        
        analysis = AnalysisInDB(
            user_id=user.id,
            stock_code="AAPL",
            market_type=MarketType.US,
            status=AnalysisStatus.RUNNING,
            progress=50.0
        )
        
        result = await test_db.analyses.insert_one(analysis.dict(by_alias=True))
        analysis_id = str(result.inserted_id)
        
        response = test_client.post(f"/api/v1/analysis/{analysis_id}/cancel", headers=auth_headers)
        
        assert response.status_code == 200
        assert "Analysis cancellation requested" in response.json()["message"]
    
    @pytest.mark.asyncio
    async def test_cancel_completed_analysis_forbidden(self, test_client, auth_headers, test_db):
        """Test cancellation of completed analysis is forbidden"""
        from ..models.analysis import AnalysisInDB, AnalysisStatus, MarketType
        from ..models.user import UserInDB
        
        user_doc = await test_db.users.find_one({"username": "testuser"})
        user = UserInDB(**user_doc)
        
        analysis = AnalysisInDB(
            user_id=user.id,
            stock_code="AAPL",
            market_type=MarketType.US,
            status=AnalysisStatus.COMPLETED,
            progress=100.0
        )
        
        result = await test_db.analyses.insert_one(analysis.dict(by_alias=True))
        analysis_id = str(result.inserted_id)
        
        response = test_client.post(f"/api/v1/analysis/{analysis_id}/cancel", headers=auth_headers)
        
        assert response.status_code == 400
        assert "Cannot cancel analysis with status" in response.json()["detail"]


class TestAnalysisStats:
    """Test analysis statistics endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_analysis_stats_success(self, test_client, auth_headers, test_db):
        """Test successful stats retrieval"""
        from ..models.analysis import AnalysisInDB, AnalysisStatus, MarketType
        from ..models.user import UserInDB
        
        user_doc = await test_db.users.find_one({"username": "testuser"})
        user = UserInDB(**user_doc)
        
        # Create analyses with different statuses
        statuses = [AnalysisStatus.COMPLETED, AnalysisStatus.COMPLETED, AnalysisStatus.FAILED]
        for i, status in enumerate(statuses):
            analysis = AnalysisInDB(
                user_id=user.id,
                stock_code=f"TEST{i}",
                market_type=MarketType.US,
                status=status,
                progress=100.0 if status == AnalysisStatus.COMPLETED else 0.0
            )
            await test_db.analyses.insert_one(analysis.dict(by_alias=True))
        
        response = test_client.get("/api/v1/analysis/stats", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "status_counts" in data
        assert "recent_activity" in data
        assert "top_stocks" in data
        assert "total_analyses" in data
        assert data["total_analyses"] == 3


class TestStockCodeValidation:
    """Test stock code validation"""
    
    def test_validate_cn_stock_code(self, test_client, auth_headers):
        """Test Chinese stock code validation"""
        # Valid CN stock code
        analysis_data = {
            "stock_code": "000001",
            "market_type": "cn"
        }
        
        response = test_client.post("/api/v1/analysis/start", json=analysis_data, headers=auth_headers)
        assert response.status_code == 200
        
        # Invalid CN stock code
        analysis_data = {
            "stock_code": "AAPL",
            "market_type": "cn"
        }
        
        response = test_client.post("/api/v1/analysis/start", json=analysis_data, headers=auth_headers)
        assert response.status_code == 400
    
    def test_validate_us_stock_code(self, test_client, auth_headers):
        """Test US stock code validation"""
        # Valid US stock code
        analysis_data = {
            "stock_code": "AAPL",
            "market_type": "us"
        }
        
        response = test_client.post("/api/v1/analysis/start", json=analysis_data, headers=auth_headers)
        assert response.status_code == 200
        
        # Invalid US stock code
        analysis_data = {
            "stock_code": "000001",
            "market_type": "us"
        }
        
        response = test_client.post("/api/v1/analysis/start", json=analysis_data, headers=auth_headers)
        assert response.status_code == 400
    
    def test_validate_hk_stock_code(self, test_client, auth_headers):
        """Test HK stock code validation"""
        # Valid HK stock code
        analysis_data = {
            "stock_code": "0700",
            "market_type": "hk"
        }
        
        response = test_client.post("/api/v1/analysis/start", json=analysis_data, headers=auth_headers)
        assert response.status_code == 200
        
        # Invalid HK stock code
        analysis_data = {
            "stock_code": "AAPL",
            "market_type": "hk"
        }
        
        response = test_client.post("/api/v1/analysis/start", json=analysis_data, headers=auth_headers)
        assert response.status_code == 400