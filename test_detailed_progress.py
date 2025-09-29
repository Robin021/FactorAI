#!/usr/bin/env python3
"""
测试详细进度显示功能
"""

import requests
import time
import json

def test_analysis_with_detailed_progress():
    """测试分析的详细进度显示"""
    
    # 启动分析
    analysis_request = {
        "stock_symbol": "000001",
        "market_type": "A股",
        "analysis_date": "2025-01-29",
        "analysts": ["market", "fundamentals", "technical"],
        "research_depth": 2,
        "llm_provider": "dashscope",
        "llm_model": "qwen-plus"
    }
    
    print("🚀 启动分析...")
    response = requests.post(
        "http://localhost:8001/api/analysis/start",
        json=analysis_request,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 200:
        print(f"❌ 启动分析失败: {response.status_code}")
        print(response.text)
        return
    
    result = response.json()
    analysis_id = result["analysis_id"]
    print(f"✅ 分析已启动，ID: {analysis_id}")
    
    # 轮询进度
    print("\n📊 开始监控进度...")
    last_message = ""
    
    while True:
        try:
            progress_response = requests.get(
                f"http://localhost:8001/api/analysis/{analysis_id}/progress"
            )
            
            if progress_response.status_code == 200:
                progress_data = progress_response.json()
                
                status = progress_data.get("status", "unknown")
                current_step = progress_data.get("current_step", 0)
                total_steps = progress_data.get("total_steps", 0)
                progress_percentage = progress_data.get("progress_percentage", 0)
                message = progress_data.get("message", "")
                current_step_name = progress_data.get("current_step_name", "")
                
                # 只在消息变化时打印
                if message != last_message:
                    print(f"[{status.upper()}] 步骤 {current_step + 1}/{total_steps} ({progress_percentage * 100:.1f}%)")
                    print(f"  📍 {current_step_name}")
                    print(f"  💬 {message}")
                    print()
                    last_message = message
                
                # 检查是否完成
                if status in ["completed", "failed", "cancelled"]:
                    print(f"🏁 分析{status}: {message}")
                    break
                    
            else:
                print(f"❌ 获取进度失败: {progress_response.status_code}")
                break
                
        except Exception as e:
            print(f"❌ 请求错误: {e}")
            break
            
        time.sleep(2)  # 每2秒检查一次

if __name__ == "__main__":
    test_analysis_with_detailed_progress()