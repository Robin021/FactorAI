#!/usr/bin/env python3
"""
Authing Token 交换调试脚本
模拟完整的 SSO 登录流程来找出问题
"""

import os
import requests
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def simulate_token_exchange():
    """模拟 token 交换过程"""
    print("🔍 模拟 Token 交换过程...")
    
    app_id = os.getenv("AUTHING_APP_ID")
    app_secret = os.getenv("AUTHING_APP_SECRET")
    app_host = os.getenv("AUTHING_APP_HOST")
    redirect_uri = os.getenv("AUTHING_REDIRECT_URI")
    
    # 模拟的 code（实际使用时从 Authing 回调获得）
    test_code = "test_code_12345"
    
    print(f"App ID: {app_id}")
    print(f"App Secret: {app_secret[:8]}...")
    print(f"App Host: {app_host}")
    print(f"Redirect URI: {redirect_uri}")
    print(f"Test Code: {test_code}")
    
    # 构建 token 请求
    token_url = f"{app_host}/oidc/token"
    token_data = {
        "client_id": app_id,
        "client_secret": app_secret,
        "code": test_code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }
    
    print(f"\nToken URL: {token_url}")
    print(f"Token Data: {json.dumps(token_data, indent=2)}")
    
    # 发送 token 请求
    try:
        response = requests.post(token_url, data=token_data, timeout=10)
        print(f"\n响应状态: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.ok:
            token_info = response.json()
            print(f"✅ Token 获取成功: {json.dumps(token_info, indent=2)}")
        else:
            error_info = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            print(f"❌ Token 获取失败: {error_info}")
            
            # 分析错误
            if isinstance(error_info, dict):
                error_code = error_info.get('error')
                error_desc = error_info.get('error_description', '')
                
                if error_code == 'redirect_uri_mismatch':
                    print("\n🔧 redirect_uri_mismatch 错误分析:")
                    print("1. 检查 Authing 控制台中的回调地址配置")
                    print("2. 确保回调地址与代码中的完全一致")
                    print("3. 注意协议（http/https）和端口号")
                    print(f"4. 当前配置的回调地址: {redirect_uri}")
                    
                    # 提供可能的解决方案
                    print("\n💡 可能的解决方案:")
                    print("1. 在 Authing 控制台中添加回调地址:")
                    print(f"   {redirect_uri}")
                    print("2. 检查是否有多个回调地址配置")
                    print("3. 确保回调地址格式正确（不要有多余的斜杠）")
                    
    except Exception as e:
        print(f"❌ 请求失败: {e}")

def check_possible_redirect_uris():
    """检查可能的回调地址变体"""
    print("\n🔍 检查可能的回调地址变体...")
    
    base_uri = "http://localhost:3000/api/v1/auth/authing/callback"
    
    # 可能的变体
    variants = [
        base_uri,
        base_uri + "/",
        "http://localhost:3000/api/v1/auth/authing/callback/",
        "http://127.0.0.1:3000/api/v1/auth/authing/callback",
        "https://localhost:3000/api/v1/auth/authing/callback",
        "http://localhost:8000/api/v1/auth/authing/callback",  # 可能端口不同
    ]
    
    print("可能的回调地址变体:")
    for i, variant in enumerate(variants, 1):
        print(f"{i}. {variant}")
    
    print(f"\n当前配置: {base_uri}")
    print("请确保 Authing 控制台中的回调地址配置与上述之一完全匹配")

def main():
    """主函数"""
    print("🚀 Authing Token 交换调试工具")
    print("=" * 60)
    
    # 模拟 token 交换
    simulate_token_exchange()
    
    # 检查可能的回调地址变体
    check_possible_redirect_uris()
    
    print("\n" + "=" * 60)
    print("📋 下一步操作:")
    print("1. 登录 Authing 控制台")
    print("2. 进入应用管理，找到应用 ID: 68d3879e03d9b1907f220731")
    print("3. 检查回调地址配置")
    print("4. 确保回调地址与代码中的完全一致")
    print("5. 保存配置并重新测试")

if __name__ == "__main__":
    main()
