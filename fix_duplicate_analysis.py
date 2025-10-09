#!/usr/bin/env python3
"""
修复重复分析问题的脚本
"""

import os
import sys
from pathlib import Path

def fix_duplicate_analysis():
    """修复重复分析问题"""
    
    print("🔧 修复重复分析问题...")
    
    # 1. 检查服务器配置
    server_file = Path("backend/tradingagents_server.py")
    if server_file.exists():
        with open(server_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否有重复的分析师配置
        market_count = content.count('"market"')
        fundamentals_count = content.count('"fundamentals"')
        
        print(f"📊 分析师配置统计:")
        print(f"   - market: {market_count} 次")
        print(f"   - fundamentals: {fundamentals_count} 次")
        
        if market_count > 4 or fundamentals_count > 4:  # 允许一些正常的配置
            print("⚠️ 发现可能的重复配置")
        else:
            print("✅ 分析师配置看起来正常")
    
    # 2. 创建去重补丁
    patch_content = '''
# 分析去重补丁
class AnalysisDeduplicator:
    def __init__(self):
        self.running_analyses = set()
        self.completed_analyses = set()
    
    def is_duplicate(self, analysis_id, analyst_type):
        key = f"{analysis_id}_{analyst_type}"
        if key in self.running_analyses:
            return True
        self.running_analyses.add(key)
        return False
    
    def mark_completed(self, analysis_id, analyst_type):
        key = f"{analysis_id}_{analyst_type}"
        self.running_analyses.discard(key)
        self.completed_analyses.add(key)

# 全局去重器
_deduplicator = AnalysisDeduplicator()

def check_duplicate_analysis(analysis_id, analyst_type):
    """检查是否为重复分析"""
    return _deduplicator.is_duplicate(analysis_id, analyst_type)

def mark_analysis_completed(analysis_id, analyst_type):
    """标记分析完成"""
    _deduplicator.mark_completed(analysis_id, analyst_type)
'''
    
    # 保存补丁文件
    patch_file = Path("backend/analysis_deduplicator.py")
    with open(patch_file, 'w', encoding='utf-8') as f:
        f.write(patch_content)
    
    print(f"✅ 创建去重补丁: {patch_file}")
    
    # 3. 提供修复建议
    print("\n🎯 修复建议:")
    print("1. 统一分析师配置 - 确保只有一套分析师列表")
    print("2. 添加去重逻辑 - 防止同一分析师重复执行")
    print("3. 优化进度回调 - 确保进度回调正确传递")
    print("4. 监控分析流程 - 添加更详细的日志")
    
    # 4. 创建监控脚本
    monitor_script = '''#!/usr/bin/env python3
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
'''
    
    monitor_file = Path("monitor_analysis.py")
    with open(monitor_file, 'w', encoding='utf-8') as f:
        f.write(monitor_script)
    
    print(f"✅ 创建监控脚本: {monitor_file}")
    
    print("\n🚀 下一步:")
    print("1. 重启服务器以应用修复")
    print("2. 启动新的分析任务")
    print("3. 使用监控脚本观察是否还有重复")
    print("4. 如果仍有重复，需要深入调试TradingAgentsGraph")

if __name__ == "__main__":
    fix_duplicate_analysis()