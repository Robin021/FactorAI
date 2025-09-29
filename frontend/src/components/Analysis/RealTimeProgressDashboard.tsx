import React from 'react';
import { Card, Row, Col, Statistic, Progress, Timeline, Alert, Button, Space, Tag } from 'antd';
import { 
  ClockCircleOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  PauseCircleOutlined,
  PlayCircleOutlined,
  StopOutlined
} from '@ant-design/icons';
import { Analysis } from '@/types';
import { usePolling } from '@/hooks/usePolling';
import { useAnalysis } from '@/hooks/useAnalysis';
import ProgressNotifications from './ProgressNotifications';
import './RealTimeProgressDashboard.css';

interface RealTimeProgressDashboardProps {
  analysis: Analysis;
  onComplete?: () => void;
  onError?: (error: string) => void;
  onCancel?: () => void;
}

interface ProgressMetrics {
  totalSteps: number;
  completedSteps: number;
  currentStep: string;
  overallProgress: number;
  estimatedTimeRemaining: number;
  elapsedTime: number;
  averageStepTime: number;
  throughput: number; // steps per minute
}

interface StepInfo {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  startTime?: number;
  endTime?: number;
  progress: number;
  message: string;
  subTasks?: string[];
}

const RealTimeProgressDashboard: React.FC<RealTimeProgressDashboardProps> = ({
  analysis,
  onComplete,
  onError,
  onCancel,
}) => {
  const { cancelAnalysis } = useAnalysis();
  
  const [metrics, setMetrics] = React.useState<ProgressMetrics>({
    totalSteps: 6,
    completedSteps: 0,
    currentStep: '初始化',
    overallProgress: 0,
    estimatedTimeRemaining: 0,
    elapsedTime: 0,
    averageStepTime: 0,
    throughput: 0,
  });

  const [steps, setSteps] = React.useState<StepInfo[]>([
    {
      id: 'init',
      name: '初始化分析环境',
      status: 'running',
      progress: 0,
      message: '正在准备分析环境...',
    },
    {
      id: 'data_collection',
      name: '数据收集',
      status: 'pending',
      progress: 0,
      message: '等待开始...',
      subTasks: ['获取股票基础信息', '获取历史价格数据', '获取财务数据'],
    },
    {
      id: 'market_analysis',
      name: '市场分析',
      status: 'pending',
      progress: 0,
      message: '等待开始...',
      subTasks: ['技术指标计算', '趋势分析', '支撑阻力位分析'],
    },
    {
      id: 'fundamental_analysis',
      name: '基本面分析',
      status: 'pending',
      progress: 0,
      message: '等待开始...',
      subTasks: ['财务比率分析', '盈利能力分析', '估值分析'],
    },
    {
      id: 'news_sentiment',
      name: '新闻情绪分析',
      status: 'pending',
      progress: 0,
      message: '等待开始...',
      subTasks: ['新闻收集', '情绪分析', '影响评估'],
    },
    {
      id: 'report_generation',
      name: '报告生成',
      status: 'pending',
      progress: 0,
      message: '等待开始...',
      subTasks: ['结果整合', '报告编写', '图表生成'],
    },
  ]);

  const [connectionStatus, setConnectionStatus] = React.useState<'connected' | 'disconnected' | 'reconnecting'>('disconnected');
  const [isPaused, setIsPaused] = React.useState(false);

  // 不再独立轮询，避免重复请求
  // const { isPolling } = usePolling(`/analysis/${analysis.id}/progress`, {
  //   onData: handleProgressUpdate,
  //   onError: () => setConnectionStatus('disconnected'),
  // });
  const isPolling = false; // 临时禁用

  // Update connection status
  React.useEffect(() => {
    setConnectionStatus(isPolling ? 'connected' : 'disconnected');
  }, [isPolling]);

  // Timer for elapsed time calculation
  React.useEffect(() => {
    const startTime = new Date(analysis.createdAt).getTime();
    
    const timer = setInterval(() => {
      const now = Date.now();
      const elapsed = Math.floor((now - startTime) / 1000);
      
      setMetrics(prev => ({
        ...prev,
        elapsedTime: elapsed,
      }));
    }, 1000);

    return () => clearInterval(timer);
  }, [analysis.createdAt]);

  function handleProgressUpdate(data: any) {
    switch (data.type) {
      case 'step_start':
        handleStepStart(data);
        break;
      case 'step_progress':
        handleStepProgress(data);
        break;
      case 'step_complete':
        handleStepComplete(data);
        break;
      case 'overall_progress':
        handleOverallProgress(data);
        break;
      case 'analysis_complete':
        handleAnalysisComplete();
        break;
      case 'analysis_error':
        handleAnalysisError(data.error);
        break;
      case 'analysis_paused':
        setIsPaused(true);
        break;
      case 'analysis_resumed':
        setIsPaused(false);
        break;
      default:
        console.log('Unknown progress update:', data);
    }
  }

  const handleStepStart = (data: any) => {
    setSteps(prev => prev.map(step => 
      step.id === data.stepId 
        ? { ...step, status: 'running', startTime: Date.now(), message: data.message || '正在执行...' }
        : step
    ));

    setMetrics(prev => ({
      ...prev,
      currentStep: data.stepName || prev.currentStep,
    }));
  };

  const handleStepProgress = (data: any) => {
    setSteps(prev => prev.map(step => 
      step.id === data.stepId 
        ? { ...step, progress: data.progress, message: data.message }
        : step
    ));
  };

  const handleStepComplete = (data: any) => {
    setSteps(prev => prev.map(step => 
      step.id === data.stepId 
        ? { ...step, status: 'completed', endTime: Date.now(), progress: 100, message: '已完成' }
        : step
    ));

    setMetrics(prev => {
      const completedSteps = prev.completedSteps + 1;
      const avgStepTime = prev.elapsedTime / completedSteps;
      const throughput = completedSteps / (prev.elapsedTime / 60); // steps per minute
      
      return {
        ...prev,
        completedSteps,
        averageStepTime: avgStepTime,
        throughput,
      };
    });
  };

  const handleOverallProgress = (data: any) => {
    setMetrics(prev => ({
      ...prev,
      overallProgress: data.progress,
      estimatedTimeRemaining: data.estimatedTimeRemaining || 0,
    }));
  };

  const handleAnalysisComplete = () => {
    setMetrics(prev => ({
      ...prev,
      overallProgress: 100,
      estimatedTimeRemaining: 0,
    }));
    onComplete?.();
  };

  const handleAnalysisError = (error: string) => {
    onError?.(error);
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'processing';
      case 'completed':
        return 'success';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getConnectionStatusTag = () => {
    switch (connectionStatus) {
      case 'connected':
        return <Tag color="green">已连接</Tag>;
      case 'reconnecting':
        return <Tag color="orange">重连中</Tag>;
      default:
        return <Tag color="red">连接断开</Tag>;
    }
  };

  return (
    <div className="realtime-progress-dashboard">
      <ProgressNotifications analysis={analysis} enabled={true} />
      
      {/* Header with connection status */}
      <Card className="dashboard-header">
        <Row justify="space-between" align="middle">
          <Col>
            <Space>
              <h3>实时分析进度 - {analysis.stockCode}</h3>
              {getConnectionStatusTag()}
              {isPaused && <Tag color="orange">已暂停</Tag>}
            </Space>
          </Col>
          <Col>
            <Space>
              <Button
                icon={isPaused ? <PlayCircleOutlined /> : <PauseCircleOutlined />}
                onClick={isPaused ? handleResume : handlePause}
                disabled={analysis.status !== 'running'}
              >
                {isPaused ? '继续' : '暂停'}
              </Button>
              <Button
                danger
                icon={<StopOutlined />}
                onClick={handleCancel}
                disabled={analysis.status === 'completed'}
              >
                取消
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Metrics Overview */}
      <Row gutter={[16, 16]} className="metrics-row">
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总体进度"
              value={metrics.overallProgress}
              suffix="%"
              prefix={<ThunderboltOutlined />}
            />
            <Progress 
              percent={metrics.overallProgress} 
              size="small" 
              showInfo={false}
              strokeColor="#1890ff"
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="已用时间"
              value={formatTime(metrics.elapsedTime)}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="预计剩余"
              value={metrics.estimatedTimeRemaining > 0 ? formatTime(metrics.estimatedTimeRemaining) : '--'}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="完成步骤"
              value={metrics.completedSteps}
              suffix={`/ ${metrics.totalSteps}`}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Connection Alert */}
      {connectionStatus !== 'connected' && (
        <Alert
          message="连接状态异常"
          description="与服务器的连接不稳定，进度更新可能延迟"
          type="warning"
          showIcon
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Detailed Steps */}
      <Card title="详细步骤" className="steps-card">
        <Timeline>
          {steps.map((step) => (
            <Timeline.Item
              key={step.id}
              color={
                step.status === 'completed' ? 'green' :
                step.status === 'running' ? 'blue' :
                step.status === 'error' ? 'red' : 'gray'
              }
            >
              <div className="step-item">
                <div className="step-header">
                  <h4>{step.name}</h4>
                  <Tag color={getStatusColor(step.status)}>
                    {step.status === 'pending' ? '等待中' :
                     step.status === 'running' ? '进行中' :
                     step.status === 'completed' ? '已完成' : '错误'}
                  </Tag>
                </div>
                
                <p className="step-message">{step.message}</p>
                
                {step.status === 'running' && (
                  <Progress 
                    percent={step.progress} 
                    size="small"
                    strokeColor="#1890ff"
                  />
                )}
                
                {step.subTasks && step.subTasks.length > 0 && (
                  <div className="sub-tasks">
                    <p><strong>子任务:</strong></p>
                    <ul>
                      {step.subTasks.map((task, index) => (
                        <li key={index}>{task}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {step.startTime && step.endTime && (
                  <p className="step-duration">
                    耗时: {formatTime(Math.floor((step.endTime - step.startTime) / 1000))}
                  </p>
                )}
              </div>
            </Timeline.Item>
          ))}
        </Timeline>
      </Card>
    </div>
  );
};

export default RealTimeProgressDashboard;