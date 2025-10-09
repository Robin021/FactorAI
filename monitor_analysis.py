#!/usr/bin/env python3
"""
分析监控脚本
"""

import time
import requests
import json

def monitor_analysis(analysis_id):
    """监控分析进度，检测重复执行"""
    
    seen_steps = set()
    duplicate_count = 0
    
    while True:
        try:
            response = requests.get(f"http://localhost:8000/api/v1/analysis/{analysis_id}/progress")
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                message = data.get("message", "")
                
                # 检测重复步骤
                if message in seen_steps:
                    duplicate_count += 1
                    print(f"⚠️ 检测到重复步骤: {message} (第{duplicate_count}次)")
                else:
                    seen_steps.add(message)
                    print(f"📊 新步骤: {message}")
                
                if status in ["completed", "failed"]:
                    print(f"✅ 分析完成，状态: {status}")
                    print(f"📈 总重复次数: {duplicate_count}")
                    break
                    
            time.sleep(5)
            
        except Exception as e:
            print(f"❌ 监控错误: {e}")
            break

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        analysis_id = sys.argv[1]
        monitor_analysis(analysis_id)
    else:
        print("用法: python monitor_analysis.py <analysis_id>")
