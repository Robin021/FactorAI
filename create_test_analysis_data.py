#!/usr/bin/env python3
"""
创建测试分析数据
"""

import asyncio
import sys
from datetime import datetime, timedelta
from bson import ObjectId

async def create_test_data():
    """创建测试分析数据"""
    
    print("🧪 创建测试分析数据...")
    
    try:
        # 导入数据库相关模块
        from motor.motor_asyncio import AsyncIOMotorClient
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # 连接数据库
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        db_name = os.getenv("MONGODB_DB_NAME", "tradingagents")
        
        client = AsyncIOMotorClient(mongodb_url)
        db = client[db_name]
        
        print(f"📊 连接数据库: {mongodb_url}/{db_name}")
        
        # 检查是否已有用户
        users_count = await db.users.count_documents({})
        print(f"👥 数据库中有 {users_count} 个用户")
        
        if users_count == 0:
            print("⚠️ 数据库中没有用户，先创建一个测试用户...")
            
            # 创建测试用户
            test_user = {
                "_id": ObjectId(),
                "username": "admin",
                "email": "admin@example.com",
                "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3L3jzZvUxO",  # admin123
                "is_active": True,
                "role": "admin",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await db.users.insert_one(test_user)
            user_id = test_user["_id"]
            print(f"✅ 创建测试用户: {user_id}")
        else:
            # 使用第一个用户
            user = await db.users.find_one({})
            user_id = user["_id"]
            print(f"👤 使用现有用户: {user_id} ({user.get('username', 'unknown')})")
        
        # 检查现有分析记录
        existing_analyses = await db.analyses.count_documents({"user_id": user_id})
        print(f"📈 用户已有 {existing_analyses} 条分析记录")
        
        # 创建测试分析数据
        test_analyses = []
        
        for i in range(5):
            analysis = {
                "_id": ObjectId(),
                "user_id": user_id,
                "stock_code": f"00000{i+1}",
                "market_type": "CN",
                "status": "completed" if i < 3 else "failed" if i == 3 else "running",
                "progress": 100.0 if i < 3 else 50.0 if i == 3 else 75.0,
                "config": {
                    "analysts": ["market", "fundamentals"],
                    "research_depth": 2,
                    "llm_provider": "deepseek"
                },
                "result_data": {
                    "summary": f"分析结果 {i+1}",
                    "recommendation": "买入" if i % 2 == 0 else "持有"
                } if i < 3 else None,
                "error_message": "分析失败" if i == 3 else None,
                "created_at": datetime.utcnow() - timedelta(days=i),
                "started_at": datetime.utcnow() - timedelta(days=i, hours=1),
                "completed_at": datetime.utcnow() - timedelta(days=i, minutes=30) if i < 4 else None
            }
            test_analyses.append(analysis)
        
        # 插入测试数据
        if test_analyses:
            result = await db.analyses.insert_many(test_analyses)
            print(f"✅ 创建了 {len(result.inserted_ids)} 条测试分析记录")
            
            # 显示创建的记录
            for i, analysis in enumerate(test_analyses):
                print(f"  {i+1}. {analysis['stock_code']} - {analysis['status']} - {analysis['progress']}%")
        
        # 验证数据
        total_analyses = await db.analyses.count_documents({"user_id": user_id})
        print(f"📊 用户现在总共有 {total_analyses} 条分析记录")
        
        # 关闭连接
        client.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 创建测试数据失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def verify_test_data():
    """验证测试数据"""
    
    print("\n🔍 验证测试数据...")
    
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        db_name = os.getenv("MONGODB_DB_NAME", "tradingagents")
        
        client = AsyncIOMotorClient(mongodb_url)
        db = client[db_name]
        
        # 查询所有分析记录
        analyses = []
        async for analysis in db.analyses.find({}).sort("created_at", -1):
            analyses.append(analysis)
        
        print(f"📊 数据库中总共有 {len(analyses)} 条分析记录")
        
        if analyses:
            print("📋 分析记录列表:")
            for i, analysis in enumerate(analyses[:10]):  # 只显示前10条
                print(f"  {i+1}. ID: {analysis['_id']}")
                print(f"     用户: {analysis['user_id']}")
                print(f"     股票: {analysis['stock_code']}")
                print(f"     状态: {analysis['status']}")
                print(f"     创建时间: {analysis['created_at']}")
                print()
        
        client.close()
        
    except Exception as e:
        print(f"❌ 验证数据失败: {e}")

if __name__ == "__main__":
    print("🚀 开始创建测试分析数据...")
    print("=" * 60)
    
    # 创建测试数据
    success = asyncio.run(create_test_data())
    
    if success:
        # 验证数据
        asyncio.run(verify_test_data())
        
        print("\n🎉 测试数据创建完成！")
        print("💡 现在可以重新测试分析历史API了")
    else:
        print("\n❌ 测试数据创建失败")