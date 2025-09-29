"""
Test configuration and fixtures
"""
import asyncio
import pytest
import pytest_asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from ..app.main import app
from ..core.database import get_database, get_redis
from ..models.user import UserInDB, UserRole
from ..core.auth import get_password_hash


# Test database configuration
TEST_DATABASE_URL = "mongodb://localhost:27017"
TEST_DATABASE_NAME = "test_trading_agents"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_db():
    """Create test database connection"""
    client = AsyncIOMotorClient(TEST_DATABASE_URL)
    db = client[TEST_DATABASE_NAME]
    
    # Clean up before tests
    await db.users.delete_many({})
    
    yield db
    
    # Clean up after tests
    await db.users.delete_many({})
    client.close()


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.setex = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=True)
    redis_mock.exists = AsyncMock(return_value=False)
    redis_mock.sadd = AsyncMock(return_value=True)
    redis_mock.srem = AsyncMock(return_value=True)
    redis_mock.smembers = AsyncMock(return_value=set())
    redis_mock.expire = AsyncMock(return_value=True)
    redis_mock.ttl = AsyncMock(return_value=3600)
    redis_mock.incr = AsyncMock(return_value=1)
    return redis_mock


@pytest.fixture
def test_client(test_db, mock_redis):
    """Create test client with dependency overrides"""
    
    def override_get_database():
        return test_db
    
    def override_get_redis():
        return mock_redis
    
    app.dependency_overrides[get_database] = override_get_database
    app.dependency_overrides[get_redis] = override_get_redis
    
    with TestClient(app) as client:
        yield client
    
    # Clean up overrides
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(test_db):
    """Create a test user"""
    user_data = UserInDB(
        username="testuser",
        email="test@example.com",
        role=UserRole.USER,
        permissions=["analysis.create", "analysis.read"],
        password_hash=get_password_hash("testpassword123"),
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    result = await test_db.users.insert_one(user_data.dict(by_alias=True))
    user_data.id = result.inserted_id
    
    return user_data


@pytest_asyncio.fixture
async def test_admin(test_db):
    """Create a test admin user"""
    admin_data = UserInDB(
        username="admin",
        email="admin@example.com",
        role=UserRole.ADMIN,
        permissions=["*"],
        password_hash=get_password_hash("adminpassword123"),
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    result = await test_db.users.insert_one(admin_data.dict(by_alias=True))
    admin_data.id = result.inserted_id
    
    return admin_data


@pytest.fixture
def auth_headers(test_client, test_user):
    """Get authentication headers for test user"""
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    
    response = test_client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(test_client, test_admin):
    """Get authentication headers for admin user"""
    login_data = {
        "username": "admin",
        "password": "adminpassword123"
    }
    
    response = test_client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}