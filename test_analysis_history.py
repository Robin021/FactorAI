#!/usr/bin/env python3
"""
测试分析历史API功能
"""

import requests
import json
import sys

def test_analysis_history_api():
    """测试分析历史API"""
    
    print("🧪 测试分析历史API...")
    
    base_url = "http://localhost:8000"
    
    # 1. 先尝试登录获取token
    print("\n1️⃣ 尝试登录获取token...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        login_response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data, timeout=10)
        if login_response.status_code != 200:
            print(f"❌ 登录失败: {login_response.status_code}")
            print(f"响应: {login_response.text}")
            return False
            
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ 登录成功")
        
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return False
    
    # 2. 测试获取分析历史
    print("\n2️⃣ 测试获取分析历史...")
    try:
        history_response = requests.get(
            f"{base_url}/api/v1/analysis/history",
            headers=headers,
            timeout=10
        )
        
        print(f"状态码: {history_response.status_code}")
        
        if history_response.status_code == 200:
            history_data = history_response.json()
            print("✅ 分析历史API调用成功")
            print(f"📊 数据结构: {json.dumps(history_data, indent=2, ensure_ascii=False)}")
            
            # 检查数据结构
            if "analyses" in history_data:
                analyses_count = len(history_data["analyses"])
                total_count = history_data.get("total", 0)
                print(f"📈 找到 {analyses_count} 条分析记录，总计 {total_count} 条")
                
                if analyses_count > 0:
                    print("📋 第一条记录示例:")
                    first_record = history_data["analyses"][0]
                    for key, value in first_record.items():
                        print(f"  {key}: {value}")
                else:
                    print("⚠️ 没有找到分析记录")
                    
            return True
        else:
            print(f"❌ 分析历史API调用失败: {history_response.status_code}")
            print(f"错误信息: {history_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 分析历史API请求失败: {e}")
        return False

def test_analysis_history_with_params():
    """测试带参数的分析历史API"""
    
    print("\n🧪 测试带参数的分析历史API...")
    
    base_url = "http://localhost:8000"
    
    # 使用之前的token（简化处理）
    login_data = {
        "username": "admin", 
        "password": "admin123"
    }
    
    try:
        login_response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data, timeout=10)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 测试不同的参数组合
        test_params = [
            {"page": 1, "page_size": 5},
            {"page": 1, "page_size": 10, "stock_code": "000001"},
            {"page": 1, "page_size": 10, "status": "completed"},
        ]
        
        for i, params in enumerate(test_params, 1):
            print(f"\n{i}️⃣ 测试参数: {params}")
            
            response = requests.get(
                f"{base_url}/api/v1/analysis/history",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                analyses_count = len(data.get("analyses", []))
                total_count = data.get("total", 0)
                print(f"✅ 成功获取 {analyses_count} 条记录，总计 {total_count} 条")
            else:
                print(f"❌ 失败: {response.status_code} - {response.text}")
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def check_database_data():
    """检查数据库中是否有分析数据"""
    
    print("\n🧪 检查数据库中的分析数据...")
    
    try:
        # 这里可以添加直接查询数据库的逻辑
        # 暂时跳过，因为需要数据库连接配置
        print("⚠️ 数据库直接查询功能暂未实现")
        print("💡 建议通过MongoDB客户端或管理界面检查 analyses 集合")
        
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")

if __name__ == "__main__":
    print("🚀 开始测试分析历史功能...")
    print("=" * 60)
    
    # 测试基本API
    test1_result = test_analysis_history_api()
    
    # 测试带参数的API
    if test1_result:
        test_analysis_history_with_params()
    
    # 检查数据库
    check_database_data()
    
    print(f"\n📊 测试结果:")
    print(f"  基本API测试: {'✅ 通过' if test1_result else '❌ 失败'}")
    
    if test1_result:
        print("🎉 分析历史API基本功能正常！")
        print("\n💡 如果前端仍然看不到数据，请检查:")
        print("  1. 前端API调用的URL是否正确")
        print("  2. 前端数据转换逻辑是否正确")
        print("  3. 前端认证token是否有效")
        print("  4. 浏览器开发者工具中的网络请求")
    else:
        print("⚠️ 分析历史API存在问题，需要进一步调试。")