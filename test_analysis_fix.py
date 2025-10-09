#!/usr/bin/env python3
"""
测试分析修复是否有效
"""
import requests
import json

def test_analysis_api():
    """测试分析API"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 测试分析API修复...")
    
    # 1. 登录获取token
    print("\n1. 登录admin用户...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{base_url}/api/v1/auth/login", data=login_data)
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            print(f"✅ 登录成功，获得token: {token[:20]}...")
        else:
            print(f"❌ 登录失败: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return
    
    # 2. 测试分析历史API
    print("\n2. 测试分析历史API...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{base_url}/api/v1/analysis/history", headers=headers)
        if response.status_code == 200:
            history_data = response.json()
            print(f"✅ 分析历史获取成功")
            print(f"   总记录数: {history_data.get('total', 0)}")
            
            analyses = history_data.get('analyses', [])
            if analyses:
                print(f"   分析记录数: {len(analyses)}")
                for i, analysis in enumerate(analyses[:3]):
                    print(f"   [{i+1}] ID: {analysis.get('id')}")
                    print(f"       股票: {analysis.get('stock_code')}")
                    print(f"       状态: {analysis.get('status')}")
                    print(f"       有结果: {'是' if analysis.get('result_data') else '否'}")
                
                # 3. 测试获取具体分析结果
                if analyses:
                    test_id = analyses[0].get('id')
                    print(f"\n3. 测试获取分析结果 (ID: {test_id})...")
                    
                    try:
                        response = requests.get(f"{base_url}/api/v1/analysis/{test_id}/results", headers=headers)
                        if response.status_code == 200:
                            result_data = response.json()
                            print("✅ 分析结果获取成功")
                            print(f"   股票代码: {result_data.get('stock_code')}")
                            print(f"   状态: {result_data.get('status')}")
                            print(f"   有结果数据: {'是' if result_data.get('result_data') else '否'}")
                            
                            if result_data.get('result_data'):
                                rd = result_data['result_data']
                                print(f"   分析师: {rd.get('analysts', [])}")
                                print(f"   决策: {rd.get('decision', {}).get('action', 'N/A')}")
                        else:
                            print(f"❌ 获取分析结果失败: {response.status_code} - {response.text}")
                    except Exception as e:
                        print(f"❌ 获取分析结果请求失败: {e}")
            else:
                print("   ⚠️ 没有分析记录")
        else:
            print(f"❌ 分析历史获取失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 分析历史请求失败: {e}")
    
    print("\n🎯 测试完成！")
    print("\n💡 如果看到分析记录，说明修复成功")
    print("   如果仍然没有数据，可能需要:")
    print("   1. 重启后端服务")
    print("   2. 清理前端浏览器缓存")
    print("   3. 检查MongoDB连接")

if __name__ == "__main__":
    test_analysis_api()