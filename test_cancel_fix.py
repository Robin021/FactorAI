#!/usr/bin/env python3
"""
测试取消分析功能的修复
"""

import requests
import time
import json

def test_cancel_analysis():
    """测试取消分析功能"""
    
    # 1. 启动一个分析任务
    print("🚀 启动分析任务...")
    
    start_payload = {
        "symbol": "AAPL",
        "market_type": "US",
        "analysis_date": "2024-01-15",
        "analysts": ["market", "fundamentals", "technical"],
        "research_depth": 2,
        "llm_provider": "deepseek",
        "llm_model": "deepseek-chat"
    }
    
    try:
        # 启动分析
        response = requests.post(
            "http://localhost:8000/api/v1/analysis/start",
            json=start_payload,
            headers={"Authorization": "Bearer test_token"}
        )
        
        if response.status_code != 200:
            print(f"❌ 启动分析失败: {response.status_code}")
            print(f"响应: {response.text}")
            return
            
        result = response.json()
        analysis_id = result.get("analysis_id")
        
        if not analysis_id:
            print(f"❌ 未获取到分析ID: {result}")
            return
            
        print(f"✅ 分析任务已启动，ID: {analysis_id}")
        
        # 2. 等待几秒让分析开始
        print("⏳ 等待分析开始...")
        time.sleep(3)
        
        # 3. 检查分析状态
        progress_response = requests.get(
            f"http://localhost:8000/api/v1/analysis/{analysis_id}/progress",
            headers={"Authorization": "Bearer test_token"}
        )
        
        if progress_response.status_code == 200:
            progress = progress_response.json()
            print(f"📊 当前进度: {progress.get('status')} - {progress.get('message', 'N/A')}")
        
        # 4. 取消分析
        print("⏹️ 尝试取消分析...")
        
        cancel_response = requests.post(
            f"http://localhost:8000/api/v1/analysis/{analysis_id}/cancel",
            headers={"Authorization": "Bearer test_token"}
        )
        
        if cancel_response.status_code == 200:
            cancel_result = cancel_response.json()
            print(f"✅ 取消请求成功: {cancel_result.get('message')}")
        else:
            print(f"❌ 取消请求失败: {cancel_response.status_code}")
            print(f"响应: {cancel_response.text}")
            return
        
        # 5. 验证分析是否真的被取消了
        print("🔍 验证取消效果...")
        
        for i in range(10):  # 检查10次，每次间隔1秒
            time.sleep(1)
            
            progress_response = requests.get(
                f"http://localhost:8000/api/v1/analysis/{analysis_id}/progress",
                headers={"Authorization": "Bearer test_token"}
            )
            
            if progress_response.status_code == 200:
                progress = progress_response.json()
                status = progress.get('status')
                message = progress.get('message', 'N/A')
                
                print(f"  检查 {i+1}/10: 状态={status}, 消息={message}")
                
                if status == 'cancelled':
                    print("✅ 分析已成功取消！")
                    return
                elif status in ['completed', 'failed']:
                    print(f"❌ 分析未被取消，最终状态: {status}")
                    return
            else:
                print(f"❌ 无法获取进度: {progress_response.status_code}")
        
        print("⚠️ 取消状态验证超时")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    print("🧪 开始测试取消分析功能...")
    test_cancel_analysis()
    print("🏁 测试完成")