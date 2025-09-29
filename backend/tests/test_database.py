"""
Tests for database operations and models
"""
import pytest
from datetime import datetime, timedelta
from bson import ObjectId

from ..models.user import UserInDB, UserRole, UserCreate, UserUpdate
from ..models.analysis import AnalysisInDB, AnalysisStatus, MarketType, AnalysisRequest
from ..models.config import ConfigInDB, ConfigType
from ..core.database import get_database
from ..core.auth import get_password_hash, verify_password


class TestUserModel:
    """Test user model operations"""
    
    @pytest.mark.asyncio
    async def test_create_user(self, test_db):
        """Test user creation"""
        user_data = UserInDB(
            username="testuser",
            email="test@example.com",
            role=UserRole.USER,
            permissions=["analysis.read"],
            password_hash=get_password_hash("password123"),
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        result = await test_db.users.insert_one(user_data.dict(by_alias=True))
        assert result.inserted_id is not None
        
        # Verify user was created
        created_user = await test_db.users.find_one({"_id": result.inserted_id})
        assert created_user is not None
        assert created_user["username"] == "testuser"
        assert created_user["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_find_user_by_username(self, test_db, test_user):
        """Test finding user by username"""
        user_doc = await test_db.users.find_one({"username": "testuser"})
        
        assert user_doc is not None
        user = UserInDB(**user_doc)
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.USER
    
    @pytest.mark.asyncio
    async def test_update_user(self, test_db, test_user):
        """Test user update"""
        update_data = {
            "email": "updated@example.com",
            "updated_at": datetime.utcnow()
        }
        
        result = await test_db.users.update_one(
            {"_id": test_user.id},
            {"$set": update_data}
        )
        
        assert result.modified_count == 1
        
        # Verify update
        updated_user = await test_db.users.find_one({"_id": test_user.id})
        assert updated_user["email"] == "updated@example.com"
    
    @pytest.mark.asyncio
    async def test_delete_user(self, test_db, test_user):
        """Test user deletion"""
        result = await test_db.users.delete_one({"_id": test_user.id})
        assert result.deleted_count == 1
        
        # Verify deletion
        deleted_user = await test_db.users.find_one({"_id": test_user.id})
        assert deleted_user is None
    
    @pytest.mark.asyncio
    async def test_user_password_operations(self, test_db):
        """Test password hashing and verification"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        # Verify password hashing
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrongpassword", hashed)
        
        # Test user creation with hashed password
        user_data = UserInDB(
            username="passwordtest",
            email="password@example.com",
            role=UserRole.USER,
            permissions=[],
            password_hash=hashed,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        result = await test_db.users.insert_one(user_data.dict(by_alias=True))
        assert result.inserted_id is not None


class TestAnalysisModel:
    """Test analysis model operations"""
    
    @pytest.mark.asyncio
    async def test_create_analysis(self, test_db, test_user):
        """Test analysis creation"""
        analysis_data = AnalysisInDB(
            user_id=test_user.id,
            stock_code="AAPL",
            market_type=MarketType.US,
            status=AnalysisStatus.PENDING,
            progress=0.0,
            created_at=datetime.utcnow()
        )
        
        result = await test_db.analyses.insert_one(analysis_data.dict(by_alias=True))
        assert result.inserted_id is not None
        
        # Verify analysis was created
        created_analysis = await test_db.analyses.find_one({"_id": result.inserted_id})
        assert created_analysis is not None
        assert created_analysis["stock_code"] == "AAPL"
        assert created_analysis["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_update_analysis_progress(self, test_db, test_user):
        """Test analysis progress update"""
        # Create analysis
        analysis_data = AnalysisInDB(
            user_id=test_user.id,
            stock_code="AAPL",
            market_type=MarketType.US,
            status=AnalysisStatus.PENDING,
            progress=0.0
        )
        
        result = await test_db.analyses.insert_one(analysis_data.dict(by_alias=True))
        analysis_id = result.inserted_id
        
        # Update progress
        update_data = {
            "status": AnalysisStatus.RUNNING.value,
            "progress": 50.0,
            "started_at": datetime.utcnow()
        }
        
        update_result = await test_db.analyses.update_one(
            {"_id": analysis_id},
            {"$set": update_data}
        )
        
        assert update_result.modified_count == 1
        
        # Verify update
        updated_analysis = await test_db.analyses.find_one({"_id": analysis_id})
        assert updated_analysis["status"] == "running"
        assert updated_analysis["progress"] == 50.0
    
    @pytest.mark.asyncio
    async def test_find_user_analyses(self, test_db, test_user):
        """Test finding analyses by user"""
        # Create multiple analyses
        for i in range(3):
            analysis_data = AnalysisInDB(
                user_id=test_user.id,
                stock_code=f"TEST{i}",
                market_type=MarketType.US,
                status=AnalysisStatus.COMPLETED,
                progress=100.0
            )
            await test_db.analyses.insert_one(analysis_data.dict(by_alias=True))
        
        # Find user analyses
        cursor = test_db.analyses.find({"user_id": test_user.id})
        analyses = await cursor.to_list(length=None)
        
        assert len(analyses) == 3
        for analysis in analyses:
            assert analysis["user_id"] == test_user.id
    
    @pytest.mark.asyncio
    async def test_analysis_aggregation(self, test_db, test_user):
        """Test analysis aggregation queries"""
        # Create analyses with different statuses
        statuses = [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED, AnalysisStatus.COMPLETED]
        for i, status in enumerate(statuses):
            analysis_data = AnalysisInDB(
                user_id=test_user.id,
                stock_code=f"TEST{i}",
                market_type=MarketType.US,
                status=status,
                progress=100.0 if status == AnalysisStatus.COMPLETED else 0.0
            )
            await test_db.analyses.insert_one(analysis_data.dict(by_alias=True))
        
        # Aggregate by status
        pipeline = [
            {"$match": {"user_id": test_user.id}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        
        cursor = test_db.analyses.aggregate(pipeline)
        results = await cursor.to_list(length=None)
        
        status_counts = {result["_id"]: result["count"] for result in results}
        assert status_counts.get("completed", 0) == 2
        assert status_counts.get("failed", 0) == 1


class TestConfigModel:
    """Test configuration model operations"""
    
    @pytest.mark.asyncio
    async def test_create_config(self, test_db, test_user):
        """Test configuration creation"""
        config_data = ConfigInDB(
            user_id=test_user.id,
            config_type=ConfigType.LLM,
            config_data={
                "provider": "openai",
                "model": "gpt-4",
                "api_key": "test_key"
            },
            created_at=datetime.utcnow()
        )
        
        result = await test_db.configs.insert_one(config_data.dict(by_alias=True))
        assert result.inserted_id is not None
        
        # Verify config was created
        created_config = await test_db.configs.find_one({"_id": result.inserted_id})
        assert created_config is not None
        assert created_config["config_type"] == "llm"
        assert created_config["config_data"]["provider"] == "openai"
    
    @pytest.mark.asyncio
    async def test_update_config(self, test_db, test_user):
        """Test configuration update"""
        # Create config
        config_data = ConfigInDB(
            user_id=test_user.id,
            config_type=ConfigType.LLM,
            config_data={"provider": "openai", "model": "gpt-3.5-turbo"}
        )
        
        result = await test_db.configs.insert_one(config_data.dict(by_alias=True))
        config_id = result.inserted_id
        
        # Update config
        update_data = {
            "config_data.model": "gpt-4",
            "updated_at": datetime.utcnow()
        }
        
        update_result = await test_db.configs.update_one(
            {"_id": config_id},
            {"$set": update_data}
        )
        
        assert update_result.modified_count == 1
        
        # Verify update
        updated_config = await test_db.configs.find_one({"_id": config_id})
        assert updated_config["config_data"]["model"] == "gpt-4"
    
    @pytest.mark.asyncio
    async def test_find_user_configs(self, test_db, test_user):
        """Test finding configurations by user and type"""
        # Create configs of different types
        config_types = [ConfigType.LLM, ConfigType.DATA_SOURCE, ConfigType.SYSTEM]
        for config_type in config_types:
            config_data = ConfigInDB(
                user_id=test_user.id,
                config_type=config_type,
                config_data={"test": "data"}
            )
            await test_db.configs.insert_one(config_data.dict(by_alias=True))
        
        # Find LLM configs
        llm_configs = await test_db.configs.find({
            "user_id": test_user.id,
            "config_type": ConfigType.LLM.value
        }).to_list(length=None)
        
        assert len(llm_configs) == 1
        assert llm_configs[0]["config_type"] == "llm"


class TestDatabaseIndexes:
    """Test database indexes and performance"""
    
    @pytest.mark.asyncio
    async def test_user_indexes(self, test_db):
        """Test user collection indexes"""
        indexes = await test_db.users.list_indexes().to_list(length=None)
        index_names = [idx["name"] for idx in indexes]
        
        # Should have default _id index
        assert "_id_" in index_names
        
        # Create username index if not exists
        await test_db.users.create_index("username", unique=True)
        await test_db.users.create_index("email", unique=True)
        
        # Verify indexes were created
        indexes = await test_db.users.list_indexes().to_list(length=None)
        index_names = [idx["name"] for idx in indexes]
        assert "username_1" in index_names
        assert "email_1" in index_names
    
    @pytest.mark.asyncio
    async def test_analysis_indexes(self, test_db):
        """Test analysis collection indexes"""
        # Create compound indexes for common queries
        await test_db.analyses.create_index([("user_id", 1), ("created_at", -1)])
        await test_db.analyses.create_index([("user_id", 1), ("status", 1)])
        await test_db.analyses.create_index("stock_code")
        
        # Verify indexes
        indexes = await test_db.analyses.list_indexes().to_list(length=None)
        index_names = [idx["name"] for idx in indexes]
        
        assert "user_id_1_created_at_-1" in index_names
        assert "user_id_1_status_1" in index_names
        assert "stock_code_1" in index_names


class TestDatabaseTransactions:
    """Test database transaction handling"""
    
    @pytest.mark.asyncio
    async def test_transaction_success(self, test_db, test_user):
        """Test successful transaction"""
        async with await test_db.client.start_session() as session:
            async with session.start_transaction():
                # Create analysis
                analysis_data = AnalysisInDB(
                    user_id=test_user.id,
                    stock_code="AAPL",
                    market_type=MarketType.US,
                    status=AnalysisStatus.PENDING
                )
                
                result = await test_db.analyses.insert_one(
                    analysis_data.dict(by_alias=True),
                    session=session
                )
                
                # Update user last activity
                await test_db.users.update_one(
                    {"_id": test_user.id},
                    {"$set": {"last_activity": datetime.utcnow()}},
                    session=session
                )
        
        # Verify both operations succeeded
        analysis = await test_db.analyses.find_one({"_id": result.inserted_id})
        assert analysis is not None
        
        user = await test_db.users.find_one({"_id": test_user.id})
        assert "last_activity" in user
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, test_db, test_user):
        """Test transaction rollback on error"""
        try:
            async with await test_db.client.start_session() as session:
                async with session.start_transaction():
                    # Create analysis
                    analysis_data = AnalysisInDB(
                        user_id=test_user.id,
                        stock_code="AAPL",
                        market_type=MarketType.US,
                        status=AnalysisStatus.PENDING
                    )
                    
                    result = await test_db.analyses.insert_one(
                        analysis_data.dict(by_alias=True),
                        session=session
                    )
                    
                    # Simulate error
                    raise Exception("Simulated error")
        except Exception:
            pass
        
        # Verify rollback - analysis should not exist
        analysis = await test_db.analyses.find_one({"stock_code": "AAPL"})
        assert analysis is None


class TestDatabaseValidation:
    """Test database validation and constraints"""
    
    @pytest.mark.asyncio
    async def test_unique_username_constraint(self, test_db, test_user):
        """Test username uniqueness constraint"""
        # Try to create user with same username
        duplicate_user = UserInDB(
            username="testuser",  # Same as test_user
            email="different@example.com",
            role=UserRole.USER,
            permissions=[],
            password_hash=get_password_hash("password123"),
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        # This should fail due to unique constraint
        with pytest.raises(Exception):
            await test_db.users.insert_one(duplicate_user.dict(by_alias=True))
    
    @pytest.mark.asyncio
    async def test_required_fields_validation(self, test_db):
        """Test required fields validation"""
        # Try to create user without required fields
        incomplete_user = {
            "username": "incomplete"
            # Missing required fields
        }
        
        # This should work at database level but fail at model validation
        with pytest.raises(Exception):
            UserInDB(**incomplete_user)