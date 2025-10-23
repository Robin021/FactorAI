#!/usr/bin/env python3
"""检查分析数据"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

async def check_analysis():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    
    # 获取最新的一条分析记录
    analysis = await db.analyses.find_one(sort=[('created_at', -1)])
    
    if analysis:
        print('最新分析记录:')
        print(f'  ID: {analysis.get("_id")}')
        print(f'  股票代码: {analysis.get("stock_code")}')
        print(f'  状态: {analysis.get("status")}')
        print(f'  创建时间: {analysis.get("created_at")}')
        print(f'  开始时间: {analysis.get("started_at")}')
        print(f'  完成时间: {analysis.get("completed_at")}')
        
        result_data = analysis.get("result_data")
        if result_data:
            print(f'  result_data 类型: {type(result_data)}')
            if isinstance(result_data, dict):
                print(f'  result_data keys: {list(result_data.keys())[:10]}')
                print(f'  stock_name: {result_data.get("stock_name", "未找到")}')
        else:
            print('  result_data: None')
    else:
        print('没有找到分析记录')
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_analysis())
