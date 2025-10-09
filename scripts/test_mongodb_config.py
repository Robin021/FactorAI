#!/usr/bin/env python3
"""
测试MongoDB配置统一化
验证新的配置是否正常工作
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv 未安装，直接读取环境变量")

from tradingagents.config.env_utils import get_mongodb_url, get_mongodb_database_name, parse_bool_env


async def test_mongodb_config():
    """测试MongoDB配置"""
    print("🔍 测试MongoDB配置统一化...")
    print("=" * 50)
    
    # 1. 测试环境变量解析
    print("\n📋 1. 环境变量解析测试:")
    mongodb_enabled = parse_bool_env("MONGODB_ENABLED", False)
    print(f"   MONGODB_ENABLED: {mongodb_enabled}")
    
    # 2. 测试连接字符串获取
    print("\n🔗 2. MongoDB连接字符串:")
    try:
        mongodb_url = get_mongodb_url()
        print(f"   连接字符串: {mongodb_url}")
        
        # 隐藏密码显示
        safe_url = mongodb_url
        if "@" in safe_url and ":" in safe_url:
            parts = safe_url.split("@")
            if len(parts) == 2:
                auth_part = parts[0].split("://")[1]
                if ":" in auth_part:
                    username = auth_part.split(":")[0]
                    safe_url = safe_url.replace(auth_part, f"{username}:***")
        print(f"   安全显示: {safe_url}")
        
    except Exception as e:
        print(f"   ❌ 获取连接字符串失败: {e}")
        return False
    
    # 3. 测试数据库名称获取
    print("\n🗄️ 3. 数据库名称:")
    try:
        db_name = get_mongodb_database_name()
        print(f"   数据库名称: {db_name}")
    except Exception as e:
        print(f"   ❌ 获取数据库名称失败: {e}")
        return False
    
    # 4. 测试MongoDB连接
    if mongodb_enabled:
        print("\n🔌 4. MongoDB连接测试:")
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            
            client = AsyncIOMotorClient(mongodb_url)
            
            # 测试连接
            await client.admin.command('ping')
            print("   ✅ MongoDB连接成功")
            
            # 测试数据库访问
            db = client[db_name]
            collections = await db.list_collection_names()
            print(f"   📊 数据库集合数量: {len(collections)}")
            if collections:
                print(f"   📋 集合列表: {', '.join(collections[:5])}")
            
            client.close()
            
        except ImportError:
            print("   ⚠️ motor 未安装，跳过连接测试")
        except Exception as e:
            print(f"   ❌ MongoDB连接失败: {e}")
            return False
    else:
        print("\n🔌 4. MongoDB连接测试:")
        print("   ⚠️ MongoDB未启用，跳过连接测试")
    
    # 5. 测试数据库管理器
    print("\n🛠️ 5. 数据库管理器测试:")
    try:
        from tradingagents.config.database_manager import get_database_manager
        
        db_manager = get_database_manager()
        status = db_manager.get_status_report()
        
        print(f"   MongoDB可用: {status['mongodb']['available']}")
        print(f"   Redis可用: {status['redis']['available']}")
        print(f"   缓存后端: {status['cache_backend']}")
        
    except Exception as e:
        print(f"   ❌ 数据库管理器测试失败: {e}")
        return False
    
    print("\n✅ 所有测试通过！")
    return True


def show_config_summary():
    """显示配置摘要"""
    print("\n📊 配置摘要:")
    print("=" * 50)
    
    # 显示相关环境变量
    env_vars = [
        "MONGODB_ENABLED",
        "MONGODB_URL", 
        "MONGODB_DB_NAME",
        "MONGODB_CONNECTION_STRING",  # 兼容性
        "DATABASE_NAME"  # 兼容性
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # 隐藏敏感信息
            if "mongodb://" in value and "@" in value:
                safe_value = value.split("@")[0].split("://")[1].split(":")[0] + ":***@" + value.split("@")[1]
                print(f"   {var}: mongodb://{safe_value}")
            else:
                print(f"   {var}: {value}")
        else:
            print(f"   {var}: (未设置)")


async def main():
    """主函数"""
    print("🚀 MongoDB配置统一化测试")
    print("=" * 50)
    
    show_config_summary()
    
    success = await test_mongodb_config()
    
    if success:
        print("\n🎉 配置统一化成功！")
        print("\n💡 建议:")
        print("   1. 可以删除 .env 中的旧配置项")
        print("   2. 统一使用 MONGODB_URL 和 MONGODB_DB_NAME")
        print("   3. 更新其他脚本使用新的配置方式")
    else:
        print("\n❌ 配置存在问题，请检查环境变量设置")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)