#!/usr/bin/env python3
"""
模拟真实的 Authing SSO 登录流程
测试从认证到获取用户信息的完整过程
"""

import os
import requests
import json
import time
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def simulate_complete_sso_flow():
    """模拟完整的 SSO 登录流程"""
    print("🚀 模拟完整的 Authing SSO 登录流程")
    print("=" * 60)
    
    app_id = os.getenv("AUTHING_APP_ID")
    app_secret = os.getenv("AUTHING_APP_SECRET")
    app_host = os.getenv("AUTHING_APP_HOST")
    redirect_uri = os.getenv("AUTHING_REDIRECT_URI")
    
    print(f"配置信息:")
    print(f"  App ID: {app_id}")
    print(f"  App Secret: {app_secret[:8]}...")
    print(f"  App Host: {app_host}")
    print(f"  Redirect URI: {redirect_uri}")
    
    # 步骤 1: 构建认证 URL
    print(f"\n1️⃣ 构建认证 URL...")
    scope = "openid profile email phone username roles unionid external_id extended_fields"
    state = f"test_state_{int(time.time())}"
    
    auth_url = f"{app_host}/oidc/auth?" + "&".join([
        f"client_id={app_id}",
        "response_type=code",
        f"scope={scope}",
        f"redirect_uri={redirect_uri}",
        f"state={state}"
    ])
    
    print(f"认证 URL: {auth_url}")
    
    # 步骤 2: 测试认证 URL
    print(f"\n2️⃣ 测试认证 URL...")
    try:
        response = requests.get(auth_url, timeout=10, allow_redirects=False)
        print(f"响应状态: {response.status_code}")
        
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            print(f"✅ 认证 URL 正常，重定向到: {location[:100]}...")
            
            if 'login' in location:
                print("✅ 会重定向到 Authing 登录页面")
            else:
                print("⚠️ 重定向目标异常")
        else:
            print(f"❌ 认证 URL 异常: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 认证 URL 测试失败: {e}")
        return False
    
    # 步骤 3: 模拟 token 交换（使用模拟的 code）
    print(f"\n3️⃣ 模拟 Token 交换...")
    
    # 模拟一个真实的 code 格式
    mock_code = f"mock_code_{int(time.time())}"
    
    token_url = f"{app_host}/oidc/token"
    token_data = {
        "client_id": app_id,
        "client_secret": app_secret,
        "code": mock_code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }
    
    print(f"Token URL: {token_url}")
    print(f"Token Data: {json.dumps(token_data, indent=2)}")
    
    try:
        response = requests.post(token_url, data=token_data, timeout=10)
        print(f"Token 交换响应: {response.status_code}")
        
        if response.ok:
            token_info = response.json()
            print(f"✅ Token 交换成功: {json.dumps(token_info, indent=2)}")
            
            # 步骤 4: 使用 access_token 获取用户信息
            access_token = token_info.get("access_token")
            if access_token:
                print(f"\n4️⃣ 获取用户信息...")
                userinfo_url = f"{app_host}/oidc/me"
                headers = {"Authorization": f"Bearer {access_token}"}
                
                userinfo_response = requests.get(userinfo_url, headers=headers, timeout=10)
                print(f"用户信息响应: {userinfo_response.status_code}")
                
                if userinfo_response.ok:
                    user_info = userinfo_response.json()
                    print(f"✅ 用户信息获取成功: {json.dumps(user_info, indent=2)}")
                    return True
                else:
                    error_info = userinfo_response.json() if userinfo_response.headers.get('content-type', '').startswith('application/json') else userinfo_response.text
                    print(f"❌ 用户信息获取失败: {error_info}")
                    return False
            else:
                print("❌ Token 响应中没有 access_token")
                return False
        else:
            error_info = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            print(f"❌ Token 交换失败: {error_info}")
            
            # 分析错误
            if isinstance(error_info, dict):
                error_code = error_info.get('error')
                error_desc = error_info.get('error_description', '')
                
                print(f"\n错误分析:")
                print(f"  错误代码: {error_code}")
                print(f"  错误描述: {error_desc}")
                
                if error_code == 'invalid_grant':
                    print("  原因: 授权码无效或已过期（这是预期的，因为我们使用的是模拟 code）")
                    print("  解决: 需要使用真实的 code")
                elif error_code == 'redirect_uri_mismatch':
                    print("  原因: 回调地址不匹配")
                    print("  解决: 检查 Authing 控制台中的回调地址配置")
                elif error_code == 'invalid_client':
                    print("  原因: 客户端认证失败")
                    print("  解决: 检查 App ID 和 App Secret")
                else:
                    print(f"  原因: 未知错误 - {error_code}")
                    
            return False
            
    except Exception as e:
        print(f"❌ Token 交换请求失败: {e}")
        return False

def check_authing_user_pool():
    """检查 Authing 用户池"""
    print(f"\n5️⃣ 检查 Authing 用户池...")
    print("⚠️ 无法直接检查用户池，需要手动验证:")
    print("1. 登录 Authing 控制台: https://console.authing.cn")
    print("2. 进入用户管理")
    print("3. 检查是否有用户")
    print("4. 如果没有用户，创建一个测试用户")
    print("5. 确保用户已激活")

def provide_next_steps():
    """提供下一步操作"""
    print(f"\n📋 下一步操作:")
    print("1. 使用真实的 SSO 登录流程:")
    print("   - 访问认证 URL")
    print("   - 在 Authing 登录页面输入用户名密码")
    print("   - 完成登录后获得真实的 code")
    print("   - 使用真实的 code 进行 token 交换")
    
    print("\n2. 检查 Authing 用户池:")
    print("   - 确保有测试用户")
    print("   - 确保用户已激活")
    print("   - 检查用户权限")
    
    print("\n3. 查看服务器日志:")
    print("   - 进行真实的 SSO 登录")
    print("   - 查看服务器日志中的错误信息")
    print("   - 分析具体的失败原因")

def main():
    """主函数"""
    success = simulate_complete_sso_flow()
    
    check_authing_user_pool()
    
    provide_next_steps()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 模拟流程成功")
        print("   说明 Authing 配置正确，问题可能在于用户池或权限")
    else:
        print("❌ 模拟流程失败")
        print("   需要检查 Authing 配置和网络连接")

if __name__ == "__main__":
    main()
