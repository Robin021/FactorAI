/**
 * 进度跟踪测试页面
 */

import React, { useState } from 'react';
import PollingProgressTracker from '../components/PollingProgressTracker';
import '../components/PollingProgressTracker.css';

const ProgressTest: React.FC = () => {
  const [analysisId, setAnalysisId] = useState<string>('');
  const [inputId, setInputId] = useState<string>('');
  const [isStarting, setIsStarting] = useState(false);

  // 启动测试分析
  const startTestAnalysis = async () => {
    setIsStarting(true);
    try {
      const response = await fetch('/api/analysis/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          stock_symbol: '000001',
          market_type: 'A股',
          analysis_date: new Date().toISOString().split('T')[0],
          analysts: ['market', 'fundamentals'],
          research_depth: 2,
          llm_provider: 'dashscope',
          llm_model: 'qwen-plus'
        }),
      });

      if (response.ok) {
        const result = await response.json();
        setAnalysisId(result.analysis_id);
        alert(`分析已启动！ID: ${result.analysis_id}`);
      } else {
        const error = await response.json();
        alert(`启动失败: ${error.detail}`);
      }
    } catch (err) {
      alert(`网络错误: ${err}`);
    } finally {
      setIsStarting(false);
    }
  };

  // 手动输入分析ID
  const useManualId = () => {
    if (inputId.trim()) {
      setAnalysisId(inputId.trim());
    }
  };

  const handleComplete = (success: boolean) => {
    alert(success ? '分析完成！' : '分析失败！');
  };

  const handleCancel = () => {
    alert('分析已取消');
    setAnalysisId('');
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>🧪 进度跟踪测试页面</h1>
      
      {/* 控制面板 */}
      <div style={{ 
        background: '#f5f5f5', 
        padding: '20px', 
        borderRadius: '8px', 
        marginBottom: '20px' 
      }}>
        <h3>测试控制</h3>
        
        {!analysisId && (
          <>
            <div style={{ marginBottom: '16px' }}>
              <button 
                onClick={startTestAnalysis}
                disabled={isStarting}
                style={{
                  background: '#1890ff',
                  color: 'white',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                {isStarting ? '启动中...' : '🚀 启动测试分析'}
              </button>
            </div>
            
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <input
                type="text"
                placeholder="或输入现有的分析ID"
                value={inputId}
                onChange={(e) => setInputId(e.target.value)}
                style={{
                  padding: '6px 12px',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                  flex: 1
                }}
              />
              <button 
                onClick={useManualId}
                disabled={!inputId.trim()}
                style={{
                  background: '#52c41a',
                  color: 'white',
                  border: 'none',
                  padding: '6px 12px',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                使用
              </button>
            </div>
          </>
        )}
        
        {analysisId && (
          <div>
            <p><strong>当前分析ID:</strong> {analysisId}</p>
            <button 
              onClick={() => setAnalysisId('')}
              style={{
                background: '#ff4d4f',
                color: 'white',
                border: 'none',
                padding: '6px 12px',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              重置
            </button>
          </div>
        )}
      </div>

      {/* 进度跟踪组件 */}
      {analysisId && (
        <PollingProgressTracker
          analysisId={analysisId}
          onComplete={handleComplete}
          onCancel={handleCancel}
        />
      )}

      {/* 说明 */}
      <div style={{ 
        background: '#e6f7ff', 
        padding: '16px', 
        borderRadius: '8px',
        marginTop: '20px'
      }}>
        <h4>📖 使用说明</h4>
        <ul>
          <li>点击"启动测试分析"会调用后端API开始一个模拟分析</li>
          <li>组件会每3秒轮询一次进度</li>
          <li>你也可以手动输入一个分析ID来跟踪现有分析</li>
          <li>确保后端服务在 http://localhost:8000 运行</li>
        </ul>
      </div>
    </div>
  );
};

export default ProgressTest;