import React from 'react';
import { Card, Progress, Typography, Steps, Button, Alert, Space, Tag } from 'antd';
import {
  LoadingOutlined,
  ClockCircleOutlined,
  StopOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import { Analysis } from '@/types';
import { useAnalysis } from '@/hooks/useAnalysis';
import { usePolling } from '@/hooks/usePolling';
import './AnalysisProgress.css';

const { Title, Text } = Typography;
const { Step } = Steps;

interface AnalysisProgressProps {
  analysis: Analysis;
}

interface ProgressData {
  progress: number;
  currentStep: string;
  message: string;
  steps: Array<{
    title: string;
    status: 'wait' | 'process' | 'finish' | 'error';
    description?: string;
  }>;
  estimatedTimeRemaining?: number;
}

const AnalysisProgress: React.FC<AnalysisProgressProps> = ({ analysis }) => {
  const { cancelAnalysis } = useAnalysis();
  const [progressData, setProgressData] = React.useState<ProgressData>({
    progress: 0,
    currentStep: '准备分析',
    message: '正在初始化分析任务...',
    steps: [
      { title: '初始化', status: 'process', description: '准备分析环境' },
      { title: '数据获取', status: 'wait', description: '获取股票数据' },
      { title: '分析师工作', status: 'wait', description: '执行分析任务' },
      { title: '结果整理', status: 'wait', description: '整理分析结果' },
      { title: '完成', status: 'wait', description: '分析完成' },
    ],
  });

  // 彻底禁用轮询，避免疯狂刷新
  // const { isPolling, error: pollingError } = usePolling(`/analysis/${analysis.id}/status`, {
  //   // ... 轮询逻辑已禁用
  // });
  const isPolling = false; // 强制禁用轮询
  const pollingError = null;

  const handleCancel = async () => {
    try {
      await cancelAnalysis(analysis.id);
    } catch (error) {
      console.error('Failed to cancel analysis:', error);
    }
  };

  const formatTime = (seconds: number) => {
    if (seconds < 60) {
      return `${Math.round(seconds)}秒`;
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = Math.round(seconds % 60);
      return `${minutes}分${remainingSeconds}秒`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours}小时${minutes}分钟`;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <LoadingOutlined spin style={{ color: '#1890ff' }} />;
      case 'pending':
        return <ClockCircleOutlined style={{ color: '#faad14' }} />;
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'failed':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'processing';
      case 'pending':
        return 'warning';
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <div className="analysis-progress-container">
      <Card className="progress-card">
        <div className="progress-header">
          <Space align="center">
            {getStatusIcon(analysis.status)}
            <div>
              <Title level={4} style={{ margin: 0 }}>
                分析进行中
              </Title>
              <Text type="secondary">
                {analysis.stockCode} - {progressData.currentStep}
              </Text>
            </div>
          </Space>

          <Space>
            <Tag color={getStatusColor(analysis.status)}>
              {analysis.status === 'running'
                ? '运行中'
                : analysis.status === 'pending'
                  ? '等待中'
                  : analysis.status}
            </Tag>
            {!isPolling && <Tag color="red">{pollingError ? '连接异常' : '已停止'}</Tag>}
          </Space>
        </div>

        <div className="progress-content">
          <div className="progress-bar-section">
            <Progress
              percent={Math.round(progressData.progress)}
              status={analysis.status === 'failed' ? 'exception' : 'active'}
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
              size="default"
            />

            <div className="progress-info">
              <Text>{progressData.message}</Text>
              {progressData.estimatedTimeRemaining && (
                <Text type="secondary" className="time-remaining">
                  预计剩余时间: {formatTime(progressData.estimatedTimeRemaining)}
                </Text>
              )}
            </div>
          </div>

          <div className="steps-section">
            <Title level={5}>分析步骤</Title>
            <Steps
              direction="vertical"
              size="small"
              current={progressData.steps.findIndex(step => step.status === 'process')}
            >
              {progressData.steps.map((step, index) => (
                <Step
                  key={index}
                  title={step.title}
                  description={step.description}
                  status={step.status}
                />
              ))}
            </Steps>
          </div>

          {analysis.status === 'failed' && (
            <Alert
              message="分析失败"
              description="分析过程中出现错误，请检查参数后重试。"
              type="error"
              showIcon
              style={{ marginTop: 16 }}
            />
          )}

          {!isPolling && pollingError && (
            <Alert
              message="连接异常"
              description="与服务器的连接不稳定，进度更新可能延迟。"
              type="warning"
              showIcon
              style={{ marginTop: 16 }}
            />
          )}
        </div>

        <div className="progress-actions">
          <Button
            type="default"
            danger
            icon={<StopOutlined />}
            onClick={handleCancel}
            disabled={analysis.status !== 'running' && analysis.status !== 'pending'}
          >
            取消分析
          </Button>
        </div>
      </Card>

      <Card title="分析详情" className="analysis-details-card">
        <div className="analysis-info">
          <div className="info-item">
            <Text strong>股票代码:</Text>
            <Text>{analysis.stockCode}</Text>
          </div>
          <div className="info-item">
            <Text strong>创建时间:</Text>
            <Text>{new Date(analysis.createdAt).toLocaleString()}</Text>
          </div>
          <div className="info-item">
            <Text strong>分析ID:</Text>
            <Text code>{analysis.id}</Text>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default AnalysisProgress;
