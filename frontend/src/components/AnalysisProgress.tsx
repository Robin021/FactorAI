/**
 * 简单分析进度组件 - 轮询方案
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Progress, Card, Typography, Space, Tag, Button, Alert, Statistic } from 'antd';
import { 
  PlayCircleOutlined, 
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  StopOutlined,
  ReloadOutlined
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;

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

interface AnalysisProgressProps {
  analysisId: string;
  onComplete?: (success: boolean) => void;
  onCancel?: () => void;
  showCancelButton?: boolean;
}

const AnalysisProgress: React.FC<AnalysisProgressProps> = ({
  analysisId,
  onComplete,
  onCancel,
  showCancelButton = true
}) => {
  const [progressData, setProgressData] = useState<ProgressData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<number>(0);
  
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const POLL_INTERVAL = 2000; // 2秒轮询一次

  // 格式化时间显示
  const formatTime = useCallback((seconds: number): string => {
    if (seconds < 60) {
      return `${seconds.toFixed(1)}秒`;
    } else if (seconds < 3600) {
      const minutes = seconds / 60;
      return `${minutes.toFixed(1)}分钟`;
    } else {
      const hours = seconds / 3600;
      return `${hours.toFixed(1)}小时`;
    }
  }, []);

  // 获取状态颜色
  const getStatusColor = useCallback((status: string) => {
    switch (status) {
      case 'pending': return 'default';
      case 'running': return 'processing';
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'cancelled': return 'warning';
      default: return 'default';
    }
  }, []);

  // 获取状态图标
  const getStatusIcon = useCallback((status: string) => {
    switch (status) {
      case 'pending': return <ClockCircleOutlined />;
      case 'running': return <PlayCircleOutlined spin />;
      case 'completed': return <CheckCircleOutlined />;
      case 'failed': return <ExclamationCircleOutlined />;
      case 'cancelled': return <StopOutlined />;
      default: return <ClockCircleOutlined />;
    }
  }, []);

  // 获取进度数据
  const fetchProgress = useCallback(async () => {
    if (isLoading) return; // 防止重复请求
    
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
        setLastUpdate(Date.now());
        setError(null);
        
        // 检查是否完成
        if (data.status === 'completed' || data.status === 'failed') {
          onComplete?.(data.status === 'completed');
          // 停止轮询
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
        }
      } else if (response.status === 404) {
        setError('分析不存在');
        // 停止轮询
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

  // 开始轮询
  const startPolling = useCallback(() => {
    if (intervalRef.current) return; // 已经在轮询了
    
    // 立即获取一次
    fetchProgress();
    
    // 设置定时轮询
    intervalRef.current = setInterval(fetchProgress, POLL_INTERVAL);
  }, [fetchProgress]);

  // 停止轮询
  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

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

  // 组件挂载时开始轮询
  useEffect(() => {
    startPolling();

    return () => {
      stopPolling();
    };
  }, [startPolling, stopPolling]);

  // 如果没有进度数据，显示加载状态
  if (!progressData) {
    return (
      <Card title="📊 分析进度" loading={isLoading}>
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <Text>正在获取分析进度...</Text>
        </div>
      </Card>
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
  } = progressData;

  return (
    <Card 
      title={
        <Space>
          <span>📊 分析进度</span>
          <Tag color={getStatusColor(status)} icon={getStatusIcon(status)}>
            {status === 'running' ? '进行中' : 
             status === 'completed' ? '已完成' :
             status === 'failed' ? '失败' :
             status === 'cancelled' ? '已取消' : '等待中'}
          </Tag>
          {!isConnected && (
            <Tag color="orange">连接中...</Tag>
          )}
        </Space>
      }
      extra={
        showCancelButton && status === 'running' && (
          <Button 
            type="text" 
            danger 
            icon={<StopOutlined />}
            onClick={handleCancel}
          >
            取消分析
          </Button>
        )
      }
    >
      {error && (
        <Alert
          message="连接错误"
          description={error}
          type="error"
          showIcon
          closable
          onClose={() => setError(null)}
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 进度条 */}
      <div style={{ marginBottom: 24 }}>
        <Progress
          percent={Math.round(progress_percentage * 100)}
          status={
            status === 'completed' ? 'success' :
            status === 'failed' ? 'exception' :
            status === 'running' ? 'active' : 'normal'
          }
          strokeColor={{
            '0%': '#108ee9',
            '100%': '#87d068',
          }}
          trailColor="#f0f0f0"
          strokeWidth={8}
          showInfo={true}
          format={(percent) => `${percent}%`}
        />
      </div>

      {/* 当前状态 */}
      <div style={{ marginBottom: 16 }}>
        <Title level={5}>当前状态</Title>
        <Paragraph>
          <Text strong>📋 {message}</Text>
        </Paragraph>
      </div>

      {/* 步骤信息 */}
      <div style={{ marginBottom: 16 }}>
        <Title level={5}>进度详情</Title>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text>
            <strong>步骤进度:</strong> 第 {current_step + 1} 步，共 {total_steps} 步
          </Text>
          {current_step_info && (
            <Text type="secondary">
              <strong>当前步骤:</strong> {current_step_info.name} - {current_step_info.description}
            </Text>
          )}
        </Space>
      </div>

      {/* 时间统计 */}
      <div style={{ marginBottom: 16 }}>
        <Title level={5}>时间统计</Title>
        <Space size="large">
          <Statistic
            title="已用时间"
            value={formatTime(elapsed_time)}
            prefix={<ClockCircleOutlined />}
            valueStyle={{ fontSize: '16px' }}
          />
          {estimated_remaining > 0 && status === 'running' && (
            <Statistic
              title="预计剩余"
              value={formatTime(estimated_remaining)}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ fontSize: '16px', color: '#1890ff' }}
            />
          )}
        </Space>
      </div>

      {/* 连接状态指示器 */}
      <div style={{ 
        position: 'absolute', 
        top: 8, 
        right: 8,
        width: 8,
        height: 8,
        borderRadius: '50%',
        backgroundColor: isConnected ? '#52c41a' : '#ff4d4f',
        title: isConnected ? '已连接' : '连接断开'
      }} />
    </Card>
  );
};

export default AnalysisProgress;