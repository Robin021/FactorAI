#!/usr/bin/env python3
"""
测试分析记录的MongoDB写入功能
"""

import os
import requests
import json
import time
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_analysis_mongodb():
    """测试分析记录的MongoDB写入"""
    
    # API基础URL
    base_url = "http://localhost:8000"
    
    print("🧪 测试分析记录的MongoDB写入功能")
    print("=" * 50)
    
    # 1. 登录获取token
    print("1️⃣ 登录获取访问令牌...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data["access_token"]
            print(f"✅ 登录成功，获得访问令牌")
        else:
            print(f"❌ 登录失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return False
    
    # 2. 启动分析
    print("\n2️⃣ 启动股票分析...")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    analysis_data = {
        "symbol": "600580",  # 卧龙电驱
        "market_type": "CN",
        "analysis_type": "comprehensive"
    }
    
    try:
        response = requests.post(f"{base_url}/api/v1/analysis/start", json=analysis_data, headers=headers)
        if response.status_code == 200:
            analysis_result = response.json()
            analysis_id = analysis_result["analysis_id"]
            print(f"✅ 分析启动成功，分析ID: {analysis_id}")
        else:
            print(f"❌ 启动分析失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 启动分析请求失败: {e}")
        return False
    
    # 3. 监控分析进度
    print(f"\n3️⃣ 监控分析进度 (ID: {analysis_id})...")
    max_wait_time = 300  # 最多等待5分钟
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            response = requests.get(f"{base_url}/api/v1/analysis/{analysis_id}/progress", headers=headers)
            if response.status_code == 200:
                progress_data = response.json()
                status = progress_data.get("status", "unknown")
                progress = progress_data.get("progress_percentage", 0) * 100
                message = progress_data.get("message", "")
                
                print(f"📊 进度: {progress:.1f}% - {status} - {message}")
                
                if status == "completed":
                    print("✅ 分析完成！")
                    break
                elif status == "failed":
                    print("❌ 分析失败！")
                    return False
                    
            else:
                print(f"⚠️ 获取进度失败: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️ 获取进度请求失败: {e}")
        
        time.sleep(10)  # 每10秒检查一次
    
    else:
        print("⏰ 分析超时，但这不影响MongoDB测试")
    
    # 4. 检查分析历史
    print(f"\n4️⃣ 检查分析历史记录...")
    try:
        response = requests.get(f"{base_url}/api/v1/analysis/history", headers=headers)
        if response.status_code == 200:
            history_data = response.json()
            analyses = history_data.get("analyses", [])
            total = history_data.get("total", 0)
            
            print(f"✅ 获取历史记录成功，共 {total} 条记录")
            
            # 查找我们刚才创建的分析
            our_analysis = None
            for analysis in analyses:
                if analysis.get("analysis_id") == analysis_id:
                    our_analysis = analysis
                    break
            
            if our_analysis:
                print(f"✅ 找到我们的分析记录:")
                print(f"   - ID: {our_analysis.get('analysis_id')}")
                print(f"   - 股票: {our_analysis.get('symbol')}")
                print(f"   - 状态: {our_analysis.get('status')}")
                print(f"   - 进度: {our_analysis.get('progress_percentage', 0) * 100:.1f}%")
                print(f"   - 创建时间: {our_analysis.get('created_at', 'N/A')}")
                return True
            else:
                print(f"❌ 未找到我们的分析记录 (ID: {analysis_id})")
                print("📋 现有记录:")
                for analysis in analyses[:3]:  # 显示前3条
                    print(f"   - {analysis.get('analysis_id')} - {analysis.get('symbol')} - {analysis.get('status')}")
                return False
                
        else:
            print(f"❌ 获取历史记录失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 获取历史记录请求失败: {e}")
        return False

if __name__ == "__main__":
    success = test_analysis_mongodb()
    
    if success:
        print("\n🎉 MongoDB写入测试成功！")
        print("✅ 分析记录已正确保存到数据库")
        print("✅ 用户历史记录功能正常")
    else:
        print("\n❌ MongoDB写入测试失败")
        print("⚠️ 请检查服务器日志和数据库连接")