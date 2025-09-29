#!/usr/bin/env python3
"""
测试进度跟踪修复
"""

import requests
import time
import json

def test_progress_tracking():
    """测试进度跟踪是否正常工作"""
    
    # 1. 登录获取token
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    login_response = requests.post("http://localhost:8000/api/v1/auth/login", json=login_data)
    if login_response.status_code != 200:
        print(f"❌ 登录失败: {login_response.status_code}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ 登录成功")
    
    # 2. 启动分析
    analysis_data = {
        "symbol": "AAPL",
        "market_type": "US",
        "analysis_type": "comprehensive"
    }
    
    analysis_response = requests.post(
        "http://localhost:8000/api/v1/analysis/start", 
        json=analysis_data, 
        headers=headers
    )
    
    if analysis_response.status_code != 200:
        print(f"❌ 启动分析失败: {analysis_response.status_code}")
        print(analysis_response.text)
        return
    
    analysis_id = analysis_response.json()["analysis_id"]
    print(f"✅ 分析启动成功，ID: {analysis_id}")
    
    # 3. 轮询进度
    print("\n📊 开始监控进度...")
    last_progress = -1
    last_message = ""
    
    for i in range(60):  # 最多监控60次（10分钟）
        try:
            progress_response = requests.get(
                f"http://localhost:8000/api/v1/analysis/{analysis_id}/progress",
                headers=headers
            )
            
            if progress_response.status_code == 200:
                progress_data = progress_response.json()
                current_progress = progress_data.get("progress_percentage", 0)
                status = progress_data.get("status", "unknown")
                message = progress_data.get("message", "")
                
                # 在进度或消息有变化时打印
                if current_progress != last_progress or message != last_message:
                    progress_percent = int(current_progress * 100)
                    print(f"[{i+1:2d}] {progress_percent:3d}% | {status:10s} | {message}")
                    last_progress = current_progress
                    last_message = message
                
                # 检查是否完成
                if status in ["completed", "failed", "cancelled"]:
                    print(f"\n🎯 分析{status}!")
                    break
                    
            elif progress_response.status_code == 404:
                print(f"[{i+1:2d}] ❌ 进度未找到 (404)")
            else:
                print(f"[{i+1:2d}] ❌ 获取进度失败: {progress_response.status_code}")
                
        except Exception as e:
            print(f"[{i+1:2d}] ❌ 请求异常: {e}")
        
        time.sleep(10)  # 每10秒检查一次
    
    print("\n✅ 进度监控完成")

if __name__ == "__main__":
    test_progress_tracking()