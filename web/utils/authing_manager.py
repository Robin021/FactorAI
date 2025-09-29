"""
Authing SSO 管理器
处理 Authing 单点登录的用户认证和信息获取
解决用户信息不一致的问题
"""

import os
import requests
import hashlib
import streamlit as st
from typing import Dict, Optional, Tuple
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入日志模块
try:
    from tradingagents.utils.logging_manager import get_logger
    logger = get_logger('authing')
except ImportError:
    import logging
    logger = logging.getLogger('authing')

class AuthingManager:
    """Authing SSO 管理器"""
    
    def __init__(self):
        """初始化 Authing 管理器"""
        # 从环境变量读取 Authing 配置
        self.app_id = os.getenv("AUTHING_APP_ID")
        self.app_secret = os.getenv("AUTHING_APP_SECRET") 
        self.app_host = os.getenv("AUTHING_APP_HOST")
        self.redirect_uri = os.getenv("AUTHING_REDIRECT_URI")
        
        # 检查配置是否完整
        self.is_configured = bool(self.app_id and self.app_host)
        
        if not self.is_configured:
            logger.warning("⚠️ Authing 配置不完整，SSO 功能将不可用")
            logger.info("需要设置环境变量: AUTHING_APP_ID, AUTHING_APP_HOST")
        else:
            logger.info(f"✅ Authing SSO 管理器初始化完成")
            logger.info(f"📱 App ID: {self.app_id}")
            logger.info(f"🌐 App Host: {self.app_host}")
    
    def get_sso_login_url(self) -> Optional[str]:
        """获取 SSO 登录 URL"""
        if not self.is_configured:
            return None
        
        # 构建 Authing 登录 URL
        # 使用完整的 scope 来确保获取稳定的用户信息
        scope = "openid profile email phone username roles unionid external_id extended_fields"
        
        auth_url = f"{self.app_host}/oidc/auth?" + "&".join([
            f"client_id={self.app_id}",
            "response_type=code",
            f"scope={scope}",
            f"redirect_uri={self.redirect_uri}",
            f"state={self._generate_state()}"
        ])
        
        logger.info(f"🔗 生成 SSO 登录 URL: {auth_url}")
        return auth_url
    
    def login_with_authing(self, code: str) -> Tuple[bool, Optional[Dict]]:
        """
        使用 Authing code 进行登录
        
        Args:
            code: Authing 返回的授权码
            
        Returns:
            (登录成功, 用户信息)
        """
        if not self.is_configured:
            logger.error("❌ Authing 配置不完整，无法进行 SSO 登录")
            return False, None
        
        try:
            logger.info(f"🔄 开始处理 Authing SSO 登录，code: {code[:8]}...")
            
            # 第一步：用 code 换取 access_token
            token_info = self._exchange_code_for_token(code)
            if not token_info:
                return False, None
            
            access_token = token_info.get("access_token")
            if not access_token:
                logger.error("❌ 未获取到 access_token")
                return False, None
            
            # 第二步：用 access_token 获取用户信息
            user_info = self._get_user_info(access_token)
            if not user_info:
                return False, None
            
            # 第三步：标准化用户信息，确保一致性
            standardized_user_info = self._standardize_user_info(user_info)
            
            logger.info(f"✅ SSO 登录成功，用户: {standardized_user_info.get('username')}")
            return True, standardized_user_info
            
        except Exception as e:
            logger.error(f"❌ Authing SSO 登录失败: {e}")
            return False, None
    
    def _exchange_code_for_token(self, code: str) -> Optional[Dict]:
        """用 code 换取 access_token"""
        try:
            token_url = f"{self.app_host}/oidc/token"
            token_data = {
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": self.redirect_uri
            }
            
            logger.info(f"🔄 正在交换 token，URL: {token_url}")
            token_response = requests.post(token_url, data=token_data, timeout=30)
            
            if not token_response.ok:
                logger.error(f"❌ 获取 token 失败: {token_response.status_code} - {token_response.text}")
                return None
            
            token_info = token_response.json()
            logger.info(f"✅ Token 获取成功，类型: {token_info.get('token_type')}")
            return token_info
            
        except Exception as e:
            logger.error(f"❌ Token 交换失败: {e}")
            return None
    
    def _get_user_info(self, access_token: str) -> Optional[Dict]:
        """用 access_token 获取用户信息"""
        try:
            userinfo_url = f"{self.app_host}/oidc/me"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            logger.info(f"🔄 正在获取用户信息，URL: {userinfo_url}")
            userinfo_response = requests.get(userinfo_url, headers=headers, timeout=30)
            
            if not userinfo_response.ok:
                logger.error(f"❌ 获取用户信息失败: {userinfo_response.status_code} - {userinfo_response.text}")
                return None
            
            user_info = userinfo_response.json()
            logger.info(f"✅ 用户信息获取成功，sub: {user_info.get('sub')}")
            logger.debug(f"📋 原始用户信息: {user_info}")
            return user_info
            
        except Exception as e:
            logger.error(f"❌ 用户信息获取失败: {e}")
            return None
    
    def _standardize_user_info(self, user_info: Dict) -> Dict:
        """
        标准化用户信息，确保一致性
        
        这是解决用户信息不一致问题的关键方法
        """
        # 使用 sub 作为唯一标识符，确保一致性
        sub = user_info.get("sub")
        if not sub:
            logger.error("❌ 用户信息中缺少 sub 字段")
            return {}
        
        # 用户名优先级：preferred_username > username > 手机号 > sub
        # 改进：如果用户名相关字段都为空，使用手机号作为用户名
        username = (
            user_info.get("preferred_username") or 
            user_info.get("username") or 
            user_info.get("phone_number") or 
            sub
        )
        
        # 显示名称优先级：name > nickname > 手机号 > username
        display_name = (
            user_info.get("name") or 
            user_info.get("nickname") or 
            user_info.get("phone_number") or 
            username
        )
        
        # 邮箱处理 - 改进：如果邮箱为空，使用手机号生成邮箱
        email = user_info.get("email")
        if not email:
            phone = user_info.get("phone_number")
            if phone:
                # 使用手机号生成邮箱
                email = f"{phone}@authing.demo"
            else:
                # 最后回退到用户名生成邮箱
                email = f"{username}@authing.demo"
        
        # 手机号处理
        phone = user_info.get("phone_number")
        
        # 头像处理
        avatar = user_info.get("picture")
        
        # 角色信息
        roles = user_info.get("roles", [])
        
        # 扩展字段
        extended_fields = user_info.get("extended_fields", {})
        
        standardized_info = {
            "sub": sub,  # 唯一标识符
            "username": username,  # 用户名
            "display_name": display_name,  # 显示名称
            "email": email,  # 邮箱
            "phone": phone,  # 手机号
            "avatar": avatar,  # 头像
            "roles": roles,  # 角色列表
            "extended_fields": extended_fields,  # 扩展字段
            "auth_type": "sso",  # 认证类型
            "auth_provider": "authing",  # 认证提供商
            "raw_user_info": user_info  # 保留原始信息用于调试
        }
        
        logger.info(f"📋 标准化用户信息: {standardized_info}")
        return standardized_info
    
    def _generate_state(self) -> str:
        """生成 state 参数"""
        import time
        import random
        timestamp = str(int(time.time()))
        random_str = str(random.randint(1000, 9999))
        return f"{timestamp}_{random_str}"
    
    def validate_config(self) -> bool:
        """验证 Authing 配置"""
        if not self.is_configured:
            return False
        
        try:
            # 尝试访问 Authing 配置端点
            config_url = f"{self.app_host}/.well-known/openid_configuration"
            response = requests.get(config_url, timeout=10)
            return response.ok
        except Exception as e:
            logger.error(f"❌ Authing 配置验证失败: {e}")
            return False

# 全局 Authing 管理器实例
authing_manager = AuthingManager()

# 导出管理器实例
__all__ = ['authing_manager', 'AuthingManager']
