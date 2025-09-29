#!/usr/bin/env python3
"""
Authing 用户信息获取诊断脚本
检查为什么获取不到真实的用户信息
"""

import os
import requests
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_authing_api_calls():
    """测试 Authing API 调用"""
    print("🔍 测试 Authing API 调用...")
    
    app_id = os.getenv("AUTHING_APP_ID")
    app_secret = os.getenv("AUTHING_APP_SECRET")
    app_host = os.getenv("AUTHING_APP_HOST")
    redirect_uri = os.getenv("AUTHING_REDIRECT_URI")
    
    print(f"App ID: {app_id}")
    print(f"App Secret: {app_secret[:8]}...")
    print(f"App Host: {app_host}")
    print(f"Redirect URI: {redirect_uri}")
    
    # 测试 1: 检查 OpenID 配置
    print("\n1️⃣ 检查 OpenID 配置...")
    try:
        config_url = f"{app_host}/oidc/.well-known/openid-configuration"
        response = requests.get(config_url, timeout=10)
        if response.ok:
            config = response.json()
            print("✅ OpenID 配置可访问")
            print(f"   Userinfo Endpoint: {config.get('userinfo_endpoint')}")
        else:
            print(f"❌ OpenID 配置不可访问: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ OpenID 配置检查失败: {e}")
        return False
    
    # 测试 2: 模拟 token 交换（使用无效 code）
    print("\n2️⃣ 测试 Token 交换...")
    try:
        token_url = f"{app_host}/oidc/token"
        token_data = {
            "client_id": app_id,
            "client_secret": app_secret,
            "code": "invalid_test_code",
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }
        
        response = requests.post(token_url, data=token_data, timeout=10)
        print(f"   Token 交换响应: {response.status_code}")
        
        if response.ok:
            print("✅ Token 交换成功（意外）")
            return True
        else:
            error_info = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            print(f"   Token 交换错误: {error_info}")
            
            # 分析错误类型
            if isinstance(error_info, dict):
                error_code = error_info.get('error')
                if error_code == 'invalid_grant':
                    print("✅ 这是预期的错误（无效的 code）")
                    print("   说明 token 交换机制正常")
                    return True
                elif error_code == 'redirect_uri_mismatch':
                    print("❌ 回调地址不匹配")
                    return False
                elif error_code == 'invalid_client':
                    print("❌ 客户端认证失败（App ID 或 Secret 错误）")
                    return False
                else:
                    print(f"❌ 未知错误: {error_code}")
                    return False
            else:
                print(f"❌ 非 JSON 响应: {error_info}")
                return False
                
    except Exception as e:
        print(f"❌ Token 交换测试失败: {e}")
        return False
    
    # 测试 3: 检查用户信息端点
    print("\n3️⃣ 测试用户信息端点...")
    try:
        userinfo_url = f"{app_host}/oidc/me"
        # 使用无效的 token 测试端点是否可访问
        headers = {"Authorization": "Bearer invalid_token"}
        response = requests.get(userinfo_url, headers=headers, timeout=10)
        print(f"   用户信息端点响应: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ 用户信息端点可访问（返回 401 是预期的）")
            return True
        elif response.status_code == 404:
            print("❌ 用户信息端点不存在")
            return False
        else:
            print(f"⚠️ 用户信息端点响应异常: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 用户信息端点测试失败: {e}")
        return False

def check_server_logs():
    """检查服务器日志"""
    print("\n🔍 检查服务器日志...")
    
    try:
        # 检查是否有日志文件
        if os.path.exists("server.log"):
            with open("server.log", "r") as f:
                lines = f.readlines()
                # 查找最近的 Authing 相关错误
                authing_errors = [line for line in lines if "Authing" in line and "ERROR" in line]
                if authing_errors:
                    print("❌ 发现 Authing 错误:")
                    for error in authing_errors[-5:]:  # 显示最近5个错误
                        print(f"   {error.strip()}")
                else:
                    print("✅ 未发现 Authing 错误")
        else:
            print("⚠️ 未找到服务器日志文件")
    except Exception as e:
        print(f"❌ 检查日志失败: {e}")

def analyze_possible_causes():
    """分析可能的原因"""
    print("\n🔍 分析可能的原因...")
    
    print("可能的原因:")
    print("1. 🔑 Authing 应用密钥错误")
    print("2. 🌐 网络连接问题")
    print("3. ⏰ Token 过期或无效")
    print("4. 👤 Authing 用户池中没有用户")
    print("5. 🔒 权限配置问题")
    print("6. 📝 Scope 权限不足")
    print("7. 🐛 代码中的异常处理被触发")

def provide_solutions():
    """提供解决方案"""
    print("\n💡 解决方案:")
    print("1. 检查 Authing 控制台中的应用配置")
    print("2. 确保应用密钥正确")
    print("3. 在 Authing 用户池中创建测试用户")
    print("4. 检查网络连接和防火墙")
    print("5. 查看服务器详细日志")
    print("6. 使用真实的 code 进行测试")

def main():
    """主函数"""
    print("🚀 Authing 用户信息获取诊断工具")
    print("=" * 60)
    
    # 测试 API 调用
    api_ok = test_authing_api_calls()
    
    # 检查服务器日志
    check_server_logs()
    
    # 分析可能的原因
    analyze_possible_causes()
    
    # 提供解决方案
    provide_solutions()
    
    print("\n" + "=" * 60)
    if api_ok:
        print("✅ Authing API 调用正常")
        print("   问题可能在于:")
        print("   - Authing 用户池中没有用户")
        print("   - 权限配置问题")
        print("   - 代码异常处理被触发")
    else:
        print("❌ Authing API 调用异常")
        print("   需要检查:")
        print("   - 应用配置")
        print("   - 网络连接")
        print("   - 认证信息")

if __name__ == "__main__":
    main()
