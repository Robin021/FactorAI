#!/usr/bin/env python3
"""
检查分析记录是否存在
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

async def check_analysis():
    try:
        # 从环境变量读取MongoDB连接
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from tradingagents.config.env_utils import get_mongodb_url
        
        mongodb_url = get_mongodb_url()
        client = AsyncIOMotorClient(mongodb_url)
        db = client.tradingagents
        
        analysis_id = '16fce083-1a14-4bf7-b2d7-bd77597a2725'
        
        print(f"正在查找分析ID: {analysis_id}")
        
        # 尝试按字符串ID查找
        analysis = await db.analyses.find_one({'_id': analysis_id})
        if analysis:
            print('✅ 找到分析记录 (字符串ID):')
            print(f"  股票代码: {analysis.get('stock_code')}")
            print(f"  状态: {analysis.get('status')}")
            print(f"  创建时间: {analysis.get('created_at')}")
            print(f"  结果数据: {'有' if analysis.get('result_data') else '无'}")
            return analysis
        
        # 尝试按ObjectId查找
        try:
            analysis = await db.analyses.find_one({'_id': ObjectId(analysis_id)})
            if analysis:
                print('✅ 找到分析记录 (ObjectId):')
                print(f"  股票代码: {analysis.get('stock_code')}")
                print(f"  状态: {analysis.get('status')}")
                print(f"  创建时间: {analysis.get('created_at')}")
                print(f"  结果数据: {'有' if analysis.get('result_data') else '无'}")
                return analysis
        except Exception as e:
            print(f'ObjectId转换失败: {e}')
        
        # 如果没找到，列出最近的分析记录
        print('❌ 未找到指定的分析记录')
        print('\n最近的分析记录:')
        async for doc in db.analyses.find().sort('created_at', -1).limit(5):
            print(f"  ID: {doc.get('_id')}")
            print(f"  股票: {doc.get('stock_code')}")
            print(f"  状态: {doc.get('status')}")
            print(f"  创建时间: {doc.get('created_at')}")
            print("  ---")
        
        return None
        
    except Exception as e:
        print(f'数据库连接错误: {e}')
        return None
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(check_analysis())