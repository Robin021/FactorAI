#!/usr/bin/env python3
"""
调试进度显示问题
"""

import asyncio
import json
import redis.asyncio as redis
from datetime import datetime

async def check_redis_keys():
    """检查Redis中的进度数据"""
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        # 获取所有分析相关的键
        keys = await r.keys("*analysis*")
        print(f"🔍 找到 {len(keys)} 个分析相关的Redis键:")
        
        for key in keys:
            data = await r.get(key)
            if data:
                try:
                    parsed_data = json.loads(data)
                    print(f"  📊 {key}: {parsed_data}")
                except:
                    print(f"  📊 {key}: {data}")
            else:
                print(f"  📊 {key}: (空)")
        
        # 获取所有task相关的键
        task_keys = await r.keys("task_progress:*")
        print(f"\n🔍 找到 {len(task_keys)} 个任务进度键:")
        
        for key in task_keys:
            data = await r.get(key)
            if data:
                try:
                    parsed_data = json.loads(data)
                    print(f"  📊 {key}: {parsed_data}")
                except:
                    print(f"  📊 {key}: {data}")
        
        await r.close()
        
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")

async def simulate_progress_update():
    """模拟进度更新"""
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        analysis_id = "test-analysis-123"
        
        # 模拟几个进度步骤
        steps = [
            (10, "🔍 验证股票代码和市场信息..."),
            (25, "📊 开始市场数据收集..."),
            (50, "💼 进行基本面分析..."),
            (75, "📝 编写分析报告..."),
            (100, "✅ 分析完成")
        ]
        
        for progress, message in steps:
            progress_data = {
                "status": "running" if progress < 100 else "completed",
                "progress": progress,
                "message": message,
                "current_step": f"步骤{progress//25 + 1}",
                "updated_at": datetime.utcnow().isoformat()
            }
            
            await r.setex(
                f"analysis_progress:{analysis_id}",
                3600,
                json.dumps(progress_data)
            )
            
            print(f"📊 更新进度: {progress}% - {message}")
            await asyncio.sleep(2)
        
        await r.close()
        
    except Exception as e:
        print(f"❌ 模拟进度更新失败: {e}")

if __name__ == "__main__":
    print("🔍 检查Redis中的进度数据...")
    asyncio.run(check_redis_keys())
    
    print("\n" + "="*50)
    print("🧪 模拟进度更新...")
    asyncio.run(simulate_progress_update())