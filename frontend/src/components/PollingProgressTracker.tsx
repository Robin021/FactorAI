/**
 * 轮询进度跟踪组件 - 集成到现有前端
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';

interface ProgressData {
  analysis_id: string;
  current_step: number;
  total_steps: number;
  progress_percentage: number;
  message: string;
  elapsed_time: number;
  estimated_remaining: number;
  current_step_name: string;
  timestamp: number;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
}

interface PollingProgressTrackerProps {
  analysisId: string;
  onComplete?: (success: boolean) => void;
  onCancel?: () => void;
  className?: string;
}

const PollingProgressTracker: React.FC<PollingProgressTrackerProps> = ({
  analysisId,
  onComplete,
  onCancel,
  className = ''
}) => {
  const [progressData, setProgressData] = useState<ProgressData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const POLL_INTERVAL = 5000; // 5秒轮询，减少频率

  // 格式化时间
  const formatTime = useCallback((seconds: number): string => {
    if (seconds < 60) return `${seconds.toFixed(0)}秒`;
    if (seconds < 3600) return `${(seconds / 60).toFixed(1)}分钟`;
    return `${(seconds / 3600).toFixed(1)}小时`;
  }, []);

  // 获取进度数据
  const fetchProgress = useCallback(async () => {
    if (isLoading) return;
    
    setIsLoading(true);
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/v1/analysis/${analysisId}/progress`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data: ProgressData = await response.json();
        setProgressData(data);
        setError(null);
        
        // 检查是否完成
        if (data.status === 'completed' || data.status === 'failed') {
          onComplete?.(data.status === 'completed');
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
        }
      } else if (response.status === 404) {
        setError('分析不存在');
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      } else {
        const errorData = await response.json();
        setError(errorData.detail || '获取进度失败');
      }
    } catch (err) {
      console.error('Failed to fetch progress:', err);
      setError('网络请求失败');
    } finally {
      setIsLoading(false);
    }
  }, [analysisId, isLoading, onComplete]);

  // 取消分析
  const handleCancel = useCallback(async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/v1/analysis/${analysisId}/cancel`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        onCancel?.();
      } else {
        const error = await response.json();
        setError(error.detail || '取消分析失败');
      }
    } catch (err) {
      console.error('Failed to cancel analysis:', err);
      setError('取消分析时发生错误');
    }
  }, [analysisId, onCancel]);

  // 开始轮询
  useEffect(() => {
    fetchProgress();
    intervalRef.current = setInterval(fetchProgress, POLL_INTERVAL);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchProgress]);

  if (!progressData && !error) {
    return (
      <div className={`progress-tracker loading ${className}`}>
        <div className="progress-header">
          <h3>📊 分析进度</h3>
          {isLoading && <span className="loading-indicator">🔄 加载中...</span>}
        </div>
        <p>正在获取分析进度...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`progress-tracker error ${className}`}>
        <div className="progress-header">
          <h3>📊 分析进度</h3>
          <button onClick={fetchProgress} disabled={isLoading}>
            🔄 重试
          </button>
        </div>
        <div className="error-message">❌ {error}</div>
      </div>
    );
  }

  const {
    current_step,
    total_steps,
    progress_percentage,
    message,
    elapsed_time,
    estimated_remaining,
    current_step_name,
    status
  } = progressData!;

  const progressPercent = Math.round(progress_percentage * 100);

  return (
    <div className={`progress-tracker ${status} ${className}`}>
      {/* 头部 */}
      <div className="progress-header">
        <h3>📊 分析进度</h3>
        <div className="progress-status">
          <span className={`status-badge ${status}`}>
            {status === 'running' ? '🔄 进行中' : 
             status === 'completed' ? '✅ 已完成' :
             status === 'failed' ? '❌ 失败' :
             status === 'cancelled' ? '⏹️ 已取消' : '⏳ 等待中'}
          </span>
          {isLoading && <span className="loading-indicator">🔄</span>}
        </div>
      </div>

      {/* 进度条 */}
      <div className="progress-bar-container">
        <div className="progress-bar">
          <div 
            className={`progress-fill ${status}`}
            style={{ width: `${progressPercent}%` }}
          />
        </div>
        <span className="progress-text">{progressPercent}%</span>
      </div>

      {/* 当前状态 */}
      <div className="progress-info">
        <div className="current-message">
          <strong>📋 {message}</strong>
        </div>
        
        <div className="step-info">
          <span>步骤: 第 {current_step + 1} 步，共 {total_steps} 步</span>
          <span className="step-name">当前: {current_step_name}</span>
        </div>

        <div className="time-info">
          <span>⏱️ 已用时间: {formatTime(elapsed_time)}</span>
          {estimated_remaining > 0 && status === 'running' && (
            <span>⏳ 预计剩余: {formatTime(estimated_remaining)}</span>
          )}
        </div>
      </div>

      {/* 操作按钮 */}
      {status === 'running' && (
        <div className="progress-actions">
          <button 
            onClick={handleCancel}
            className="cancel-button"
          >
            ⏹️ 取消分析
          </button>
        </div>
      )}

      {/* 最后更新时间 */}
      <div className="last-update">
        最后更新: {new Date().toLocaleTimeString()}
      </div>
    </div>
  );
};

export default PollingProgressTracker;