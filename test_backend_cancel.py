#!/usr/bin/env python3
"""
测试后端取消分析功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 测试后端的取消逻辑
def test_backend_cancel():
    """测试后端取消逻辑"""
    
    print("🧪 测试后端取消分析逻辑...")
    
    try:
        # 导入后端模块
        from backend.app.services.progress_tracker import SimpleProgressTracker, AnalysisStatus
        
        # 创建一个进度跟踪器
        tracker = SimpleProgressTracker(
            analysis_id="test_analysis_123",
            analysts=["market", "fundamentals"],
            research_depth=2,
            llm_provider="deepseek"
        )
        
        print(f"✅ 创建进度跟踪器，初始状态: {tracker.status}")
        
        # 模拟开始分析
        tracker.status = AnalysisStatus.RUNNING
        tracker.update_progress("开始分析...")
        print(f"📊 分析开始，状态: {tracker.status}")
        
        # 模拟取消
        tracker.mark_cancelled()
        print(f"⏹️ 执行取消，状态: {tracker.status}")
        
        # 验证状态
        if tracker.status == AnalysisStatus.CANCELLED:
            print("✅ 后端取消逻辑正常工作！")
            return True
        else:
            print(f"❌ 后端取消逻辑失败，期望状态: CANCELLED，实际状态: {tracker.status}")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False

def test_simulate_analysis_cancel():
    """测试模拟分析的取消逻辑"""
    
    print("\n🧪 测试模拟分析的取消逻辑...")
    
    try:
        from backend.app.services.progress_tracker import SimpleProgressTracker, AnalysisStatus
        import threading
        import time
        
        # 创建进度跟踪器
        tracker = SimpleProgressTracker(
            analysis_id="test_cancel_123",
            analysts=["market"],
            research_depth=1,
            llm_provider="deepseek"
        )
        
        # 模拟分析函数（简化版）
        def simulate_analysis_with_cancel_check():
            steps = [
                ("步骤1", 2),
                ("步骤2", 2),
                ("步骤3", 2),
            ]
            
            tracker.status = AnalysisStatus.RUNNING
            
            for i, (message, duration) in enumerate(steps):
                # 检查是否已被取消
                if tracker.status == AnalysisStatus.CANCELLED:
                    print(f"🛑 在步骤 {i} 检测到取消，停止执行")
                    return False
                    
                tracker.update_progress(message, step=i)
                print(f"📊 执行步骤 {i}: {message}")
                
                # 分段睡眠，模拟可中断的操作
                for _ in range(duration):
                    if tracker.status == AnalysisStatus.CANCELLED:
                        print(f"🛑 在步骤 {i} 的子操作中检测到取消")
                        return False
                    time.sleep(0.1)  # 短暂睡眠
            
            tracker.mark_completed(success=True)
            return True
        
        # 在后台线程启动分析
        analysis_thread = threading.Thread(target=simulate_analysis_with_cancel_check, daemon=True)
        analysis_thread.start()
        
        # 等待分析开始
        time.sleep(0.3)
        
        # 取消分析
        print("⏹️ 发送取消信号...")
        tracker.mark_cancelled()
        
        # 等待线程结束
        analysis_thread.join(timeout=2)
        
        # 检查最终状态
        if tracker.status == AnalysisStatus.CANCELLED:
            print("✅ 模拟分析取消逻辑正常工作！")
            return True
        else:
            print(f"❌ 模拟分析取消逻辑失败，最终状态: {tracker.status}")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始测试后端取消功能...")
    
    # 测试基本取消逻辑
    test1_result = test_backend_cancel()
    
    # 测试模拟分析取消
    test2_result = test_simulate_analysis_cancel()
    
    print(f"\n📊 测试结果:")
    print(f"  基本取消逻辑: {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"  模拟分析取消: {'✅ 通过' if test2_result else '❌ 失败'}")
    
    if test1_result and test2_result:
        print("🎉 所有测试通过！取消功能修复成功。")
    else:
        print("⚠️ 部分测试失败，需要进一步检查。")