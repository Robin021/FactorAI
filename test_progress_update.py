#!/usr/bin/env python3
"""
测试进度更新修复
"""

def test_progress_callback():
    """模拟进度回调测试"""
    
    # 模拟分析进度存储
    analysis_progress_store = {
        "test_analysis": {
            "progress_percentage": 0.0,
            "current_step": 0,
            "current_step_name": "准备中"
        }
    }
    
    def progress_callback(message, step=None, total_steps=None):
        """模拟后端的进度回调函数"""
        print(f"📊 进度更新: {message}")
        print(f"   步骤: {step}/{total_steps}")
        
        # 模拟步骤匹配逻辑
        step_names = [
            "股票识别",    # 10%
            "市场分析",    # 15% 
            "基本面分析",  # 15%
            "新闻分析",    # 10%
            "情绪分析",    # 10%
            "投资辩论",    # 25%
            "风险评估"     # 15%
        ]
        step_weights = [0.10, 0.15, 0.15, 0.10, 0.10, 0.25, 0.15]
        
        detected_step = None
        
        # 检测步骤
        if "✅ 基本面分析师完成" in message:
            detected_step = 2
        elif "✅ 市场分析师完成" in message or "📈 市场分析师完成" in message:
            detected_step = 1
        elif "✅ 新闻分析师完成" in message:
            detected_step = 3
        elif "✅ 社交媒体分析师完成" in message:
            detected_step = 4
        
        if detected_step is not None:
            completed_weight = sum(step_weights[:detected_step])
            current_weight = step_weights[detected_step]
            progress_percentage = completed_weight + current_weight
            current_step_num = detected_step + 1
            current_step_name = step_names[detected_step]
            
            print(f"   ✅ 检测到步骤: {current_step_name}")
            print(f"   📈 进度: {progress_percentage*100:.1f}%")
            
            # 更新存储
            analysis_progress_store["test_analysis"].update({
                "progress_percentage": progress_percentage,
                "current_step": current_step_num,
                "current_step_name": current_step_name
            })
        else:
            print(f"   ⚠️ 未匹配到步骤")
        
        print()
    
    # 测试各个分析师的完成消息
    print("🧪 测试进度更新修复")
    print("=" * 50)
    
    test_messages = [
        "✅ 股票识别完成: 中国A股 - 600580",
        "📈 市场分析师完成分析: 600580",
        "✅ 基本面分析师完成分析: 600580", 
        "✅ 新闻分析师完成分析: 600580",
        "✅ 社交媒体分析师完成分析: 600580"
    ]
    
    for i, message in enumerate(test_messages):
        print(f"测试 {i+1}: {message}")
        progress_callback(message, i, 7)
    
    print("📊 最终进度状态:")
    final_state = analysis_progress_store["test_analysis"]
    print(f"   进度: {final_state['progress_percentage']*100:.1f}%")
    print(f"   当前步骤: {final_state['current_step']}")
    print(f"   步骤名称: {final_state['current_step_name']}")

if __name__ == "__main__":
    test_progress_callback()