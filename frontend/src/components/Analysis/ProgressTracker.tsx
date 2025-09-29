import React from 'react';
import { Card, Progress, Typography, Timeline, Button, Space, Alert, Statistic } from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  LoadingOutlined,
} from '@ant-design/icons';
import { Analysis } from '@/types';
import { usePolling } from '@/hooks/usePolling';
import { useAnalysis } from '@/hooks/useAnalysis';
import './ProgressTracker.css';

const { Title, Text } = Typography;

interface ProgressStep {
  id: string;
  title: string;
  description: string;
  status: 'waiting' | 'running' | 'completed' | 'error';
  startTime?: number;
  endTime?: number;
  progress?: number;
  details?: string[];
}

interface ProgressTrackerProps {
  analysis: Analysis;
  onCancel?: () => void;
}

const ProgressTracker: React.FC<ProgressTrackerProps> = ({ analysis, onCancel }) => {
  const { cancelAnalysis } = useAnalysis();
  const [steps, setSteps] = React.useState<ProgressStep[]>([
    {
      id: 'init',
      title: '初始化分析',
      description: '准备分析环境和参数',
      status: 'running',
    },
    {
      id: 'data_fetch',
      title: '数据获取',
      description: '获取股票基础数据和市场信息',
      status: 'waiting',
    },
    {
      id: 'market_analysis',
      title: '市场分析',
      description: '执行技术面和市场趋势分析',
      status: 'waiting',
    },
    {
      id: 'fundamental_analysis',
      title: '基本面分析',
      description: '分析财务数据和公司基本面',
      status: 'waiting',
    },
    {
      id: 'news_analysis',
      title: '新闻分析',
      description: '分析相关新闻和市场动态',
      status: 'waiting',
    },
    {
      id: 'result_compilation',
      title: '结果整理',
      description: '整合分析结果和生成报告',
      status: 'waiting',
    },
  ]);

  const [overallProgress, setOverallProgress] = React.useState(0);
  const [currentMessage, setCurrentMessage] = React.useState('正在初始化分析...');
  const [estimatedTime, setEstimatedTime] = React.useState<number | null>(null);
  const [elapsedTime, setElapsedTime] = React.useState(0);
  const [canCancel, setCanCancel] = React.useState(true);

  // 不再独立轮询，避免重复请求
  // const { isPolling } = usePolling(`/analysis/${analysis.id}/progress`, {
  // 禁用轮询，因为此组件未被使用
  // const { isPolling } = usePolling(`/analysis/${analysis.id}/status`, {
  //   onData: handleProgressUpdate,
  //   onError: () => console.log('Progress polling error'),
  // });

  // Timer for elapsed time
  React.useEffect(() => {
    const startTime = new Date(analysis.createdAt).getTime();

    const timer = setInterval(() => {
      const now = Date.now();
      const elapsed = Math.floor((now - startTime) / 1000);
      setElapsedTime(elapsed);
    }, 1000);

    return () => clearInterval(timer);
  }, [analysis.createdAt]);

  const handleProgressUpdate = (data: any) => {
    // 处理后端返回的AnalysisProgress格式
    console.log('Progress update received:', data);

    // 更新总体进度
    if (data.progress !== undefined) {
      setOverallProgress(data.progress);
    }

    // 更新当前消息
    if (data.message) {
      setCurrentMessage(data.message);
    }

    // 更新预计剩余时间
    if (data.estimated_time_remaining) {
      setEstimatedTime(data.estimated_time_remaining);
    }

    // 处理分析状态变化
    if (data.status) {
      switch (data.status) {
        case 'completed':
          setOverallProgress(100);
          setCurrentMessage('分析完成');
          setCanCancel(false);
          break;
        case 'failed':
          setCurrentMessage(`分析失败: ${data.message || '未知错误'}`);
          setCanCancel(false);
          break;
        case 'running':
          // 分析正在运行，继续轮询
          break;
        case 'pending':
          // 分析等待中
          break;
        case 'cancelled':
          // 分析被取消
          setCanCancel(false);
          break;
        default:
          console.log('Unknown analysis status:', data.status);
      }
    }

    // 更新步骤状态（基于当前步骤）
    if (data.current_step) {
      setSteps(prev =>
        prev.map((step, index) => {
          if (index < parseInt(data.current_step) - 1) {
            return { ...step, status: 'completed', progress: 100 };
          } else if (index === parseInt(data.current_step) - 1) {
            return { ...step, status: 'running', progress: data.progress || 0 };
          } else {
            return { ...step, status: 'pending', progress: 0 };
          }
        })
      );
    }
  };

  const handleCancel = async () => {
    try {
      await cancelAnalysis(analysis.id);
      onCancel?.();
    } catch (error) {
      console.error('Failed to cancel analysis:', error);
    }
  };

  const handlePause = () => {
    sendMessage({ type: 'pause_analysis' });
  };

  const handleResume = () => {
    sendMessage({ type: 'resume_analysis' });
  };

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const getStepIcon = (status: ProgressStep['status']) => {
    switch (status) {
      case 'running':
        return <LoadingOutlined spin style={{ color: '#1890ff' }} />;
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'error':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />;
    }
  };

  const getStepColor = (status: ProgressStep['status']) => {
    switch (status) {
      case 'running':
        return '#1890ff';
      case 'completed':
        return '#52c41a';
      case 'error':
        return '#ff4d4f';
      default:
        return '#d9d9d9';
    }
  };

  return (
    <div className="progress-tracker">
      <Card className="progress-overview-card">
        <div className="progress-header">
          <Title level={4}>分析进度 - {analysis.stockCode}</Title>

          <Space>
            <Statistic
              title="已用时间"
              value={formatTime(elapsedTime)}
              prefix={<ClockCircleOutlined />}
            />
            {estimatedTime && (
              <Statistic
                title="预计剩余"
                value={formatTime(estimatedTime)}
                prefix={<ClockCircleOutlined />}
              />
            )}
          </Space>
        </div>

        <div className="progress-main">
          <Progress
            percent={Math.round(overallProgress)}
            status={analysis.status === 'failed' ? 'exception' : 'active'}
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#87d068',
            }}
            size="default"
            showInfo={true}
          />

          <div className="progress-message">
            <Text>{currentMessage}</Text>
          </div>
        </div>

        {!isPolling && (
          <Alert
            message="连接状态"
            description="与服务器的连接已断开，进度更新可能不准确"
            type="warning"
            showIcon
            style={{ marginTop: 16 }}
          />
        )}

        <div className="progress-controls">
          <Space>
            <Button
              icon={<PauseCircleOutlined />}
              disabled={!canCancel || analysis.status !== 'running'}
              onClick={handlePause}
            >
              暂停
            </Button>
            <Button icon={<PlayCircleOutlined />} disabled={!canCancel} onClick={handleResume}>
              继续
            </Button>
            <Button danger icon={<StopOutlined />} disabled={!canCancel} onClick={handleCancel}>
              取消分析
            </Button>
          </Space>
        </div>
      </Card>

      <Card title="详细步骤" className="progress-steps-card">
        <Timeline>
          {steps.map(step => (
            <Timeline.Item
              key={step.id}
              dot={getStepIcon(step.status)}
              color={getStepColor(step.status)}
            >
              <div className="step-content">
                <div className="step-header">
                  <Text strong>{step.title}</Text>
                  {step.progress !== undefined && step.status === 'running' && (
                    <Text type="secondary">({step.progress}%)</Text>
                  )}
                </div>

                <Text type="secondary" className="step-description">
                  {step.description}
                </Text>

                {step.progress !== undefined && step.status === 'running' && (
                  <Progress
                    percent={step.progress}
                    size="small"
                    showInfo={false}
                    style={{ marginTop: 8 }}
                  />
                )}

                {step.details && step.details.length > 0 && (
                  <div className="step-details">
                    {step.details.map((detail, index) => (
                      <Text key={index} type="secondary" className="step-detail">
                        • {detail}
                      </Text>
                    ))}
                  </div>
                )}

                {step.startTime && step.endTime && (
                  <Text type="secondary" className="step-duration">
                    耗时: {formatTime(Math.floor((step.endTime - step.startTime) / 1000))}
                  </Text>
                )}
              </div>
            </Timeline.Item>
          ))}
        </Timeline>
      </Card>
    </div>
  );
};

export default ProgressTracker;
