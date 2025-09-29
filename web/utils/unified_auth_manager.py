"""
统一认证管理器
处理本地登录和 SSO 登录的统一认证
"""

import streamlit as st
import time
from typing import Dict, Optional, Tuple
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入日志模块
try:
    from tradingagents.utils.logging_manager import get_logger
    logger = get_logger('unified_auth')
except ImportError:
    import logging
    logger = logging.getLogger('unified_auth')

class UnifiedAuthManager:
    """统一认证管理器"""
    
    def __init__(self):
        """初始化统一认证管理器"""
        self.session_timeout = 600  # 10分钟超时
        logger.info("✅ 统一认证管理器初始化完成")
    
    def is_authenticated(self) -> bool:
        """检查是否已认证"""
        return st.session_state.get('authenticated', False)
    
    def get_current_user(self) -> Optional[Dict]:
        """获取当前用户信息"""
        if not self.is_authenticated():
            return None
        
        user_info = st.session_state.get('user_info', {})
        return user_info
    
    def login_local(self, username: str, password: str) -> Tuple[bool, Optional[Dict]]:
        """
        本地登录
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            (登录成功, 用户信息)
        """
        try:
            # 简单的本地用户验证（实际项目中应该使用数据库）
            valid_users = {
                "admin": {"password": "admin123", "role": "admin", "display_name": "管理员"},
                "user": {"password": "user123", "role": "user", "display_name": "普通用户"}
            }
            
            if username not in valid_users:
                logger.warning(f"⚠️ 用户不存在: {username}")
                return False, None
            
            user_data = valid_users[username]
            if password != user_data["password"]:
                logger.warning(f"⚠️ 密码错误: {username}")
                return False, None
            
            # 创建用户信息
            user_info = {
                "username": username,
                "display_name": user_data["display_name"],
                "role": user_data["role"],
                "auth_type": "local",
                "auth_provider": "local",
                "permissions": ["read"] if user_data["role"] == "user" else ["read", "write", "admin"]
            }
            
            # 保存到 session
            st.session_state.authenticated = True
            st.session_state.user_info = user_info
            st.session_state.login_time = time.time()
            
            logger.info(f"✅ 本地登录成功: {username}")
            return True, user_info
            
        except Exception as e:
            logger.error(f"❌ 本地登录失败: {e}")
            return False, None
    
    def login_sso(self, user_info: Dict) -> bool:
        """
        SSO 登录
        
        Args:
            user_info: SSO 用户信息
            
        Returns:
            登录是否成功
        """
        try:
            if not user_info:
                logger.error("❌ SSO 用户信息为空")
                return False
            
            # 确保用户信息包含必要字段
            required_fields = ["username", "display_name", "sub"]
            for field in required_fields:
                if field not in user_info:
                    logger.error(f"❌ SSO 用户信息缺少必要字段: {field}")
                    return False
            
            # 标准化用户信息
            standardized_user_info = {
                "username": user_info["username"],
                "display_name": user_info["display_name"],
                "email": user_info.get("email", ""),
                "phone": user_info.get("phone", ""),
                "avatar": user_info.get("avatar", ""),
                "roles": user_info.get("roles", []),
                "extended_fields": user_info.get("extended_fields", {}),
                "sub": user_info["sub"],
                "role": "user",  # 默认角色
                "permissions": ["read"],
                "auth_type": "sso",
                "auth_provider": user_info.get("auth_provider", "authing")
            }
            
            # 保存到 session
            st.session_state.authenticated = True
            st.session_state.user_info = standardized_user_info
            st.session_state.login_time = time.time()
            
            logger.info(f"✅ SSO 登录成功: {standardized_user_info['username']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ SSO 登录失败: {e}")
            return False
    
    def logout(self):
        """用户登出"""
        try:
            user_info = self.get_current_user()
            username = user_info.get("username", "unknown") if user_info else "unknown"
            
            # 清除 session
            st.session_state.authenticated = False
            st.session_state.user_info = None
            st.session_state.login_time = None
            
            logger.info(f"✅ 用户登出成功: {username}")
            
        except Exception as e:
            logger.error(f"❌ 登出失败: {e}")
    
    def check_permission(self, permission: str) -> bool:
        """
        检查用户权限
        
        Args:
            permission: 权限名称
            
        Returns:
            是否有权限
        """
        if not self.is_authenticated():
            return False
        
        user_info = self.get_current_user()
        if not user_info:
            return False
        
        permissions = user_info.get("permissions", [])
        return permission in permissions
    
    def get_user_role(self) -> str:
        """获取用户角色"""
        user_info = self.get_current_user()
        return user_info.get("role", "guest") if user_info else "guest"
    
    def is_admin(self) -> bool:
        """检查是否为管理员"""
        return self.get_user_role() == "admin"
    
    def get_auth_type(self) -> str:
        """获取认证类型"""
        user_info = self.get_current_user()
        return user_info.get("auth_type", "unknown") if user_info else "unknown"
    
    def get_auth_provider(self) -> str:
        """获取认证提供商"""
        user_info = self.get_current_user()
        return user_info.get("auth_provider", "unknown") if user_info else "unknown"

# 全局统一认证管理器实例
unified_auth_manager = UnifiedAuthManager()

# 导出管理器实例
__all__ = ['unified_auth_manager', 'UnifiedAuthManager']
