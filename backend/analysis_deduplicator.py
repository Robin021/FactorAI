
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
