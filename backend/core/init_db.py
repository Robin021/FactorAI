"""
Database initialization and migration scripts
"""
import asyncio
from datetime import datetime
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
from passlib.context import CryptContext

from ..models.user import UserInDB, UserRole
from ..models.config import ConfigInDB, ConfigType, SystemConfig
from ..core.security import DEFAULT_ROLE_PERMISSIONS
from .database import get_database


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_indexes(db: AsyncIOMotorDatabase):
    """Create database indexes for optimal performance"""
    
    # User collection indexes
    await db.users.create_index("username", unique=True)
    await db.users.create_index("email", unique=True, sparse=True)
    await db.users.create_index("created_at")
    
    # Analysis collection indexes
    await db.analyses.create_index([("user_id", 1), ("created_at", -1)])
    await db.analyses.create_index("stock_code")
    await db.analyses.create_index("status")
    await db.analyses.create_index("created_at")
    
    # Config collection indexes
    await db.configs.create_index([("user_id", 1), ("config_type", 1)])
    await db.configs.create_index("config_type")
    await db.configs.create_index("updated_at")
    
    print("Database indexes created successfully")


async def create_default_admin_user(db: AsyncIOMotorDatabase):
    """Create default admin user if not exists"""
    
    # Check if admin user already exists
    existing_admin = await db.users.find_one({"role": UserRole.ADMIN})
    if existing_admin:
        print("Admin user already exists")
        return
    
    # Create default admin user
    admin_user = UserInDB(
        username="admin",
        email="admin@tradingagents.com",
        role=UserRole.ADMIN,
        permissions=DEFAULT_ROLE_PERMISSIONS["admin"],
        password_hash=pwd_context.hash("your_new_password"),  # Default password - CHANGE THIS!
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    result = await db.users.insert_one(admin_user.dict(by_alias=True))
    print(f"Default admin user created with ID: {result.inserted_id}")
    print("Default admin credentials: username=admin, password=admin123")
    print("Please change the default password after first login!")


async def create_default_system_config(db: AsyncIOMotorDatabase):
    """Create default system configuration"""
    
    # Check if system config already exists
    existing_config = await db.configs.find_one({"config_type": ConfigType.SYSTEM})
    if existing_config:
        print("System configuration already exists")
        return
    
    # Create default system configuration
    system_config = ConfigInDB(
        user_id=None,  # System-wide configuration
        config_type=ConfigType.SYSTEM,
        config_data=SystemConfig().dict(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    result = await db.configs.insert_one(system_config.dict(by_alias=True))
    print(f"Default system configuration created with ID: {result.inserted_id}")


async def init_database():
    """Initialize database with default data and indexes"""
    try:
        db = await get_database()
        
        print("Initializing database...")
        
        # Create indexes
        await create_indexes(db)
        
        # Create default admin user
        await create_default_admin_user(db)
        
        # Create default system configuration
        await create_default_system_config(db)
        
        print("Database initialization completed successfully")
        
    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise


async def migrate_database():
    """Run database migrations"""
    try:
        db = await get_database()
        
        print("Running database migrations...")
        
        # Add migration logic here as needed
        # For example, adding new fields, updating data structures, etc.
        
        # Migration 1: Ensure all users have created_at field
        users_without_created_at = await db.users.count_documents({"created_at": {"$exists": False}})
        if users_without_created_at > 0:
            await db.users.update_many(
                {"created_at": {"$exists": False}},
                {"$set": {"created_at": datetime.utcnow()}}
            )
            print(f"Updated {users_without_created_at} users with created_at field")
        
        # Migration 2: Ensure all configs have updated_at field
        configs_without_updated_at = await db.configs.count_documents({"updated_at": {"$exists": False}})
        if configs_without_updated_at > 0:
            await db.configs.update_many(
                {"updated_at": {"$exists": False}},
                {"$set": {"updated_at": datetime.utcnow()}}
            )
            print(f"Updated {configs_without_updated_at} configs with updated_at field")
        
        print("Database migrations completed successfully")
        
    except Exception as e:
        print(f"Database migration failed: {e}")
        raise


async def reset_database():
    """Reset database (WARNING: This will delete all data!)"""
    try:
        db = await get_database()
        
        print("WARNING: Resetting database - all data will be lost!")
        
        # Drop all collections
        collections = await db.list_collection_names()
        for collection_name in collections:
            await db.drop_collection(collection_name)
            print(f"Dropped collection: {collection_name}")
        
        # Reinitialize database
        await init_database()
        
        print("Database reset completed successfully")
        
    except Exception as e:
        print(f"Database reset failed: {e}")
        raise


if __name__ == "__main__":
    # Run database initialization
    asyncio.run(init_database())