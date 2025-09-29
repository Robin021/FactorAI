#!/usr/bin/env python3
"""
Authing SSO 调试脚本
检查回调地址和配置问题
"""

import os
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def check_authing_config():
    """检查 Authing 配置"""
    print("🔍 检查 Authing 配置...")
    
    app_id = os.getenv("AUTHING_APP_ID")
    app_secret = os.getenv("AUTHING_APP_SECRET")
    app_host = os.getenv("AUTHING_APP_HOST")
    redirect_uri = os.getenv("AUTHING_REDIRECT_URI")
    
    print(f"App ID: {app_id}")
    print(f"App Secret: {app_secret[:8]}...")
    print(f"App Host: {app_host}")
    print(f"Redirect URI: {redirect_uri}")
    
    return app_id, app_secret, app_host, redirect_uri

def check_openid_config(app_host):
    """检查 OpenID 配置"""
    print("\n🔍 检查 OpenID 配置...")
    
    try:
        config_url = f"{app_host}/oidc/.well-known/openid-configuration"
        response = requests.get(config_url, timeout=10)
        
        if response.ok:
            config = response.json()
            print("✅ OpenID 配置可访问")
            print(f"Issuer: {config.get('issuer')}")
            print(f"Authorization Endpoint: {config.get('authorization_endpoint')}")
            print(f"Token Endpoint: {config.get('token_endpoint')}")
            print(f"Userinfo Endpoint: {config.get('userinfo_endpoint')}")
            return config
        else:
            print(f"❌ OpenID 配置不可访问: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 检查 OpenID 配置失败: {e}")
        return None

def test_auth_url(app_id, app_host, redirect_uri):
    """测试认证 URL"""
    print("\n🔍 测试认证 URL...")
    
    scope = "openid profile email phone username roles unionid external_id extended_fields"
    auth_url = f"{app_host}/oidc/auth?" + "&".join([
        f"client_id={app_id}",
        "response_type=code",
        f"scope={scope}",
        f"redirect_uri={redirect_uri}",
        "state=test_state"
    ])
    
    print(f"认证 URL: {auth_url}")
    
    # 测试 URL 是否可访问
    try:
        response = requests.get(auth_url, timeout=10, allow_redirects=False)
        print(f"响应状态: {response.status_code}")
        
        if response.status_code == 302:
            print("✅ 认证 URL 正常，会重定向到登录页面")
            location = response.headers.get('Location', '')
            print(f"重定向到: {location}")
        else:
            print(f"⚠️ 认证 URL 响应异常: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试认证 URL 失败: {e}")

def test_callback_endpoint():
    """测试回调端点"""
    print("\n🔍 测试回调端点...")
    
    callback_url = "http://localhost:3000/api/v1/auth/authing/callback"
    
    try:
        response = requests.get(f"{callback_url}?code=test&state=test", timeout=10)
        print(f"回调端点状态: {response.status_code}")
        
        if response.ok:
            print("✅ 回调端点可访问")
            # 检查响应内容
            content = response.text[:200]
            if "SSO 登录成功" in content:
                print("✅ 回调端点返回成功页面")
            elif "SSO 登录失败" in content:
                print("⚠️ 回调端点返回失败页面")
            else:
                print(f"⚠️ 回调端点响应内容: {content[:100]}...")
        else:
            print(f"❌ 回调端点不可访问: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试回调端点失败: {e}")

def main():
    """主函数"""
    print("🚀 Authing SSO 调试工具")
    print("=" * 50)
    
    # 检查配置
    app_id, app_secret, app_host, redirect_uri = check_authing_config()
    
    if not all([app_id, app_secret, app_host, redirect_uri]):
        print("❌ 配置不完整，请检查 .env 文件")
        return
    
    # 检查 OpenID 配置
    config = check_openid_config(app_host)
    
    # 测试认证 URL
    test_auth_url(app_id, app_host, redirect_uri)
    
    # 测试回调端点
    test_callback_endpoint()
    
    print("\n" + "=" * 50)
    print("🔧 调试建议:")
    print("1. 确保 Authing 控制台中的回调地址配置为:")
    print(f"   {redirect_uri}")
    print("2. 检查 Authing 应用是否启用")
    print("3. 确保应用密钥正确")
    print("4. 检查网络连接和防火墙设置")

if __name__ == "__main__":
    main()
