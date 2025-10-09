#!/usr/bin/env python3
"""
测试MongoDB连接
"""

import os
import asyncio
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

async def test_mongodb_connection():
    """测试MongoDB连接"""
    try:
        # 先尝试导入motor
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            print("✅ Motor导入成功")
        except ImportError:
            print("❌ Motor未安装，尝试使用pymongo同步版本测试")
            import pymongo
            from pymongo import MongoClient
            
            MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
            DATABASE_NAME = os.getenv("MONGODB_DB_NAME", os.getenv("DATABASE_NAME", "tradingagents"))
            
            print(f"🔗 尝试连接MongoDB (同步): {MONGODB_URL}")
            print(f"📊 数据库名称: {DATABASE_NAME}")
            
            # 使用同步客户端测试
            client = MongoClient(MONGODB_URL)
            db = client[DATABASE_NAME]
            
            # 测试连接
            client.admin.command('ping')
            print("✅ MongoDB连接成功!")
            
            # 测试数据库操作
            collection = db.test_collection
            
            # 插入测试文档
            test_doc = {"test": "connection", "timestamp": "2025-10-09"}
            result = collection.insert_one(test_doc)
            print(f"✅ 插入测试文档成功: {result.inserted_id}")
            
            # 查询测试文档
            found_doc = collection.find_one({"_id": result.inserted_id})
            print(f"✅ 查询测试文档成功: {found_doc}")
            
            # 删除测试文档
            collection.delete_one({"_id": result.inserted_id})
            print("✅ 删除测试文档成功")
            
            # 关闭连接
            client.close()
            print("✅ MongoDB连接测试完成")
            
            return True
        
        MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        DATABASE_NAME = os.getenv("MONGODB_DB_NAME", os.getenv("DATABASE_NAME", "tradingagents"))
        
        print(f"🔗 尝试连接MongoDB: {MONGODB_URL}")
        print(f"📊 数据库名称: {DATABASE_NAME}")
        
        # 创建客户端
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        
        # 测试连接
        await client.admin.command('ping')
        print("✅ MongoDB连接成功!")
        
        # 测试数据库操作
        collection = db.test_collection
        
        # 插入测试文档
        test_doc = {"test": "connection", "timestamp": "2025-10-09"}
        result = await collection.insert_one(test_doc)
        print(f"✅ 插入测试文档成功: {result.inserted_id}")
        
        # 查询测试文档
        found_doc = await collection.find_one({"_id": result.inserted_id})
        print(f"✅ 查询测试文档成功: {found_doc}")
        
        # 删除测试文档
        await collection.delete_one({"_id": result.inserted_id})
        print("✅ 删除测试文档成功")
        
        # 关闭连接
        client.close()
        print("✅ MongoDB连接测试完成")
        
        return True
        
    except ImportError:
        print("❌ MongoDB驱动未安装，请运行: pip install motor")
        return False
    except Exception as e:
        print(f"❌ MongoDB连接失败: {e}")
        print(f"   URL: {MONGODB_URL}")
        print(f"   数据库: {DATABASE_NAME}")
        
        # 提供一些常见问题的解决建议
        if "authentication failed" in str(e).lower():
            print("💡 建议检查:")
            print("   1. 用户名和密码是否正确")
            print("   2. 用户是否有访问该数据库的权限")
            print("   3. authSource参数是否正确")
        elif "connection refused" in str(e).lower():
            print("💡 建议检查:")
            print("   1. MongoDB服务是否已启动")
            print("   2. 端口是否正确")
            print("   3. 防火墙是否阻止连接")
        elif "timeout" in str(e).lower():
            print("💡 建议检查:")
            print("   1. 网络连接是否正常")
            print("   2. MongoDB服务器是否响应")
            
        return False

if __name__ == "__main__":
    print("🧪 MongoDB连接测试")
    print("=" * 50)
    
    success = asyncio.run(test_mongodb_connection())
    
    if success:
        print("\n🎉 所有测试通过！MongoDB连接正常")
    else:
        print("\n❌ 测试失败，请检查MongoDB配置")