#!/usr/bin/env python3
"""
修复分析记录的时间戳
- 如果 started_at 为空，设置为 created_at
- 如果 completed_at 为空且状态为 completed，设置为 created_at + 1分钟（估算）
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

async def fix_timestamps():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    
    print("🔧 开始修复分析记录的时间戳...")
    
    # 查找所有分析记录
    cursor = db.analyses.find({})
    fixed_count = 0
    total_count = 0
    
    async for doc in cursor:
        total_count += 1
        analysis_id = doc.get("_id")
        created_at = doc.get("created_at")
        started_at = doc.get("started_at")
        completed_at = doc.get("completed_at")
        status = doc.get("status")
        
        updates = {}
        
        # 修复 started_at
        if not started_at and created_at:
            updates["started_at"] = created_at
            print(f"  📝 {analysis_id}: 设置 started_at = created_at")
        
        # 修复 completed_at
        if status == "completed" and not completed_at:
            if created_at:
                # 估算完成时间为创建时间 + 2分钟
                estimated_completed = created_at + timedelta(minutes=2)
                updates["completed_at"] = estimated_completed
                print(f"  📝 {analysis_id}: 设置 completed_at = created_at + 2分钟")
            else:
                updates["completed_at"] = datetime.utcnow()
                print(f"  📝 {analysis_id}: 设置 completed_at = 当前时间")
        
        # 应用更新
        if updates:
            await db.analyses.update_one(
                {"_id": analysis_id},
                {"$set": updates}
            )
            fixed_count += 1
    
    print(f"\n✅ 完成！")
    print(f"   总记录数: {total_count}")
    print(f"   修复记录数: {fixed_count}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_timestamps())
