"""
Database connection management
"""
import asyncio
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import redis.asyncio as redis
from redis.asyncio import Redis

from ..app.config import settings


class DatabaseManager:
    """MongoDB database connection manager"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(settings.MONGODB_URL)
            self.database = self.client[settings.MONGODB_DB_NAME]
            
            # Test connection
            await self.client.admin.command('ping')
            print(f"Connected to MongoDB: {settings.MONGODB_DB_NAME}")
            
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")
    
    async def get_database(self) -> AsyncIOMotorDatabase:
        """Get database instance"""
        if not self.database:
            await self.connect()
        return self.database
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            if not self.client:
                return False
            await self.client.admin.command('ping')
            return True
        except Exception:
            return False


class CacheManager:
    """Redis cache connection manager"""
    
    def __init__(self):
        self.redis: Optional[Redis] = None
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Test connection
            await self.redis.ping()
            print(f"Connected to Redis: {settings.REDIS_URL}")
            
        except Exception as e:
            print(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            print("Disconnected from Redis")
    
    async def get_redis(self) -> Redis:
        """Get Redis instance"""
        if not self.redis:
            await self.connect()
        return self.redis
    
    async def health_check(self) -> bool:
        """Check Redis health"""
        try:
            if not self.redis:
                return False
            await self.redis.ping()
            return True
        except Exception:
            return False


# Global instances
db_manager = DatabaseManager()
cache_manager = CacheManager()


async def get_database() -> AsyncIOMotorDatabase:
    """Dependency to get database connection"""
    return await db_manager.get_database()


async def get_redis() -> Redis:
    """Dependency to get Redis connection"""
    return await cache_manager.get_redis()


async def init_db():
    """Initialize database connections"""
    await db_manager.connect()
    await cache_manager.connect()


async def close_db():
    """Close database connections"""
    await db_manager.disconnect()
    await cache_manager.disconnect()