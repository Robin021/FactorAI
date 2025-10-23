#!/usr/bin/env python3
"""
修改 admin 用户密码的脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def change_admin_password(new_password: str):
    """修改 admin 用户密码"""
    try:
        # 连接数据库
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        db = client[settings.MONGODB_DB_NAME]
        
        # 查找 admin 用户
        admin_user = await db.users.find_one({"username": "admin"})
        
        if not admin_user:
            print("❌ 未找到 admin 用户")
            return False
        
        # 生成新密码哈希
        new_password_hash = pwd_context.hash(new_password)
        
        # 更新密码
        result = await db.users.update_one(
            {"username": "admin"},
            {"$set": {"password_hash": new_password_hash}}
        )
        
        if result.modified_count > 0:
            print(f"✅ admin 密码已成功修改")
            print(f"新密码: {new_password}")
            return True
        else:
            print("❌ 密码修改失败")
            return False
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False
    finally:
        client.close()


async def main():
    if len(sys.argv) < 2:
        print("使用方法: python change_admin_password.py <新密码>")
        print("示例: python change_admin_password.py MyNewPassword123")
        sys.exit(1)
    
    new_password = sys.argv[1]
    
    if len(new_password) < 8:
        print("❌ 密码长度至少为 8 个字符")
        sys.exit(1)
    
    print(f"准备修改 admin 密码...")
    success = await change_admin_password(new_password)
    
    if success:
        print("\n✅ 完成！请使用新密码登录")
    else:
        print("\n❌ 修改失败")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
