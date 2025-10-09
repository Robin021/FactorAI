#!/usr/bin/env python3
"""
修复分析数据问题
检查MongoDB和文件系统数据，确保数据一致性
"""
import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

async def check_and_fix_analysis_data():
    """检查和修复分析数据"""
    
    print("🔍 开始检查分析数据...")
    
    # 连接MongoDB
    try:
        # 从环境变量读取MongoDB连接
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from tradingagents.config.env_utils import get_mongodb_url
        
        mongodb_url = get_mongodb_url()
        client = AsyncIOMotorClient(mongodb_url)
        db = client.tradingagents
        print("✅ MongoDB连接成功")
    except Exception as e:
        print(f"❌ MongoDB连接失败: {e}")
        return
    
    # 1. 检查MongoDB中的分析记录
    print("\n📊 检查MongoDB分析记录...")
    try:
        total_analyses = await db.analyses.count_documents({})
        completed_analyses = await db.analyses.count_documents({"status": "completed"})
        analyses_with_results = await db.analyses.count_documents({
            "result_data": {"$exists": True, "$ne": None}
        })
        
        print(f"  总分析记录: {total_analyses}")
        print(f"  已完成分析: {completed_analyses}")
        print(f"  有结果数据: {analyses_with_results}")
        
        # 显示最近的几条记录
        print("\n  最近的分析记录:")
        async for doc in db.analyses.find().sort("created_at", -1).limit(5):
            print(f"    ID: {doc.get('_id')}")
            print(f"    股票: {doc.get('stock_code')}")
            print(f"    状态: {doc.get('status')}")
            print(f"    创建时间: {doc.get('created_at')}")
            print(f"    有结果: {'是' if doc.get('result_data') else '否'}")
            print("    ---")
            
    except Exception as e:
        print(f"❌ 检查MongoDB失败: {e}")
    
    # 2. 检查文件系统数据
    print("\n📁 检查文件系统数据...")
    data_dir = Path("data")
    
    if data_dir.exists():
        # 检查分析结果目录
        results_dir = data_dir / "analysis_results"
        if results_dir.exists():
            print(f"  分析结果目录存在: {results_dir}")
            
            # 统计文件数量
            json_files = list(results_dir.rglob("*.json"))
            md_files = list(results_dir.rglob("*.md"))
            
            print(f"  JSON文件数量: {len(json_files)}")
            print(f"  Markdown文件数量: {len(md_files)}")
            
            # 显示一些示例文件
            if json_files:
                print("  示例JSON文件:")
                for f in json_files[:3]:
                    print(f"    {f}")
            
            if md_files:
                print("  示例报告文件:")
                for f in md_files[:3]:
                    print(f"    {f}")
        else:
            print("  ❌ 分析结果目录不存在")
    else:
        print("  ❌ data目录不存在")
    
    # 3. 检查特定的UUID分析
    target_uuid = "16fce083-1a14-4bf7-b2d7-bd77597a2725"
    print(f"\n🎯 查找特定分析ID: {target_uuid}")
    
    # 在MongoDB中查找
    found_in_mongo = False
    try:
        # 尝试作为字符串ID查找
        analysis = await db.analyses.find_one({"_id": target_uuid})
        if analysis:
            print("  ✅ 在MongoDB中找到 (字符串ID)")
            found_in_mongo = True
        else:
            # 尝试在其他字段中查找
            analysis = await db.analyses.find_one({"analysis_id": target_uuid})
            if analysis:
                print("  ✅ 在MongoDB中找到 (analysis_id字段)")
                found_in_mongo = True
    except Exception as e:
        print(f"  ❌ MongoDB查找失败: {e}")
    
    if not found_in_mongo:
        print("  ❌ 在MongoDB中未找到")
    
    # 在文件系统中查找
    found_in_files = False
    if data_dir.exists():
        # 搜索包含该UUID的文件
        for file_path in data_dir.rglob("*"):
            if file_path.is_file():
                try:
                    if target_uuid in file_path.name:
                        print(f"  ✅ 在文件名中找到: {file_path}")
                        found_in_files = True
                    elif file_path.suffix in ['.json', '.txt', '.md']:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if target_uuid in content:
                                print(f"  ✅ 在文件内容中找到: {file_path}")
                                found_in_files = True
                                break
                except Exception:
                    continue
    
    if not found_in_files:
        print("  ❌ 在文件系统中未找到")
    
    # 4. 建议修复方案
    print("\n🔧 修复建议:")
    
    if not found_in_mongo and not found_in_files:
        print("  1. 该分析ID可能是无效的或已被删除")
        print("  2. 检查前端是否有缓存的无效数据")
        print("  3. 清理前端localStorage和sessionStorage")
    
    if total_analyses == 0:
        print("  1. MongoDB中没有分析数据，可能需要运行数据迁移")
        print("  2. 检查MongoDB服务是否正常运行")
        print("  3. 检查数据库连接配置")
    
    if completed_analyses > analyses_with_results:
        print("  1. 有已完成的分析缺少结果数据")
        print("  2. 可能需要重新运行这些分析")
        print("  3. 或者从文件系统迁移结果数据")
    
    # 5. 提供修复命令
    print("\n🛠️  修复命令:")
    print("  # 清理前端缓存")
    print("  localStorage.clear(); sessionStorage.clear(); location.reload();")
    print()
    print("  # 运行数据迁移 (如果需要)")
    print("  cd backend && python scripts/migration/run_migration.py")
    print()
    print("  # 重启服务")
    print("  # 重启后端服务和前端服务")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_and_fix_analysis_data())