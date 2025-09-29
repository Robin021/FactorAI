import React from 'react';
import { Card, Row, Col, Statistic, Progress, Timeline, Button, Space, Tag } from 'antd';
import {
  ClockCircleOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  PauseCircleOutlined,
  PlayCircleOutlined,
  StopOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { Analysis } from '@/types';
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

  // 动态生成步骤，与后端保持一致
  const generateSteps = React.useCallback(() => {
    const baseSteps: StepInfo[] = [
      {
        id: 'data_validation',
        name: '数据验证',
        status: 'pending',
        progress: 0,
        message: '等待开始...',
        subTasks: ['验证股票代码', '预获取基础数据', '数据准备'],
      },
      {
        id: 'env_setup',
        name: '环境准备',
        status: 'pending',
        progress: 0,
        message: '等待开始...',
        subTasks: ['成本预估', '环境变量检查', '参数配置'],
      },
      {
        id: 'analysis_init',
        name: '分析初始化',
        status: 'pending',
        progress: 0,
        message: '等待开始...',
        subTasks: ['创建目录', '准备分析环境', '初始化引擎'],
      },
      {
        id: 'market_analysis',
        name: '市场分析',
        status: 'pending',
        progress: 0,
        message: '等待开始...',
        subTasks: ['市场数据收集', '技术指标计算', '趋势分析'],
      },
      {
        id: 'fundamental_analysis',
        name: '基本面分析',
        status: 'pending',
        progress: 0,
        message: '等待开始...',
        subTasks: ['财务数据分析', '财务比率计算', '盈利能力评估'],
      },
      {
        id: 'technical_analysis',
        name: '技术分析',
        status: 'pending',
        progress: 0,
        message: '等待开始...',
        subTasks: ['技术形态识别', 'MACD分析', 'RSI指标'],
      },
      {
        id: 'sentiment_analysis',
        name: '情绪分析',
        status: 'pending',
        progress: 0,
        message: '等待开始...',
        subTasks: ['新闻收集', '情绪评估', '市场情绪分析'],
      },
      {
        id: 'ai_collaboration',
        name: '智能体协作',
        status: 'pending',
        progress: 0,
        message: '等待开始...',
        subTasks: ['多智能体分析', '结果整合', '协作决策'],
      },
      {
        id: 'report_generation',
        name: '报告生成',
        status: 'pending',
        progress: 0,
        message: '等待开始...',
        subTasks: ['生成图表', '编写报告', '保存结果'],
      },
      {
        id: 'completion',
        name: '分析完成',
        status: 'pending',
        progress: 0,
        message: '等待开始...',
        subTasks: ['最终检查', '报告保存', '分析完成'],
      },
    ];

    // 根据分析师动态添加步骤
    const analystNames: Record<string, string> = {
      market: '市场分析师',
      fundamentals: '基本面分析师',
      technical: '技术分析师',
      sentiment: '情绪分析师',
      news: '新闻分析师',
    };

    const analystTasks: Record<string, string[]> = {
      market: ['分析市场趋势', '计算技术指标', '识别支撑阻力位', '评估市场风险'],
      fundamentals: ['分析财务报表', '计算财务比率', '评估盈利能力', '行业对比分析'],
      technical: ['技术形态识别', '移动平均线分析', 'MACD和RSI指标', '买卖信号识别'],
      sentiment: ['市场情绪分析', '社交媒体监控', '投资者情绪指数', '情绪趋势预测'],
      news: ['收集相关新闻', '新闻影响分析', '事件驱动分析', '风险事件识别'],
    };

    // 从分析对象中获取分析师列表，如果没有则使用默认值
    const analysts = analysis.analysts || ['market', 'fundamentals'];
    
    analysts.forEach(analyst => {
      const name = analystNames[analyst] || analyst;
      const tasks = analystTasks[analyst] || [`执行${name}分析`];
      
      baseSteps.push({
        id: `analyst_${analyst}`,
        name: `${name}分析`,
        status: 'pending',
        progress: 0,
        message: '等待开始...',
        subTasks: tasks,
      });
    });

    // 添加最后的结果整理步骤
    baseSteps.push({
      id: 'result_processing',
      name: '结果整理',
      status: 'pending',
      progress: 0,
      message: '等待开始...',
      subTasks: ['整理分析结果', '生成图表', '编写报告', '优化格式'],
    });

    return baseSteps;
  }, [analysis.analysts]);

  const [steps, setSteps] = React.useState<StepInfo[]>(() => generateSteps());

  const [lastUpdateTime, setLastUpdateTime] = React.useState<Date | null>(null);
  const [isRefreshing, setIsRefreshing] = React.useState(false);
  const [isPolling, setIsPolling] = React.useState(false);
  
  const pollingIntervalRef = React.useRef<NodeJS.Timeout | null>(null);
  const POLL_INTERVAL = 1000; // 1秒轮询一次，确保不错过步骤

  // 手动刷新功能
  const refreshProgress = React.useCallback(async () => {
    setIsRefreshing(true);
    try {
      // 使用正确的API路径
      const token = localStorage.getItem('auth_token');
      
      if (!token) {
        console.warn('No auth token found, cannot fetch progress');
        setLastUpdateTime(new Date());
        return;
      }
      
      const response = await fetch(`/api/v1/analysis/${analysis.id}/status`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Progress data received:', data);
        handleProgressUpdate(data);
        setLastUpdateTime(new Date());
      } else if (response.status === 401) {
        console.error('Authentication failed, token may be expired');
      } else {
        console.error('Failed to fetch progress:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Failed to refresh progress:', error);
    } finally {
      setIsRefreshing(false);
    }
  }, [analysis.id]);

  // 开始轮询
  const startPolling = React.useCallback(() => {
    if (pollingIntervalRef.current || analysis.status === 'completed' || analysis.status === 'failed' || analysis.status === 'cancelled') {
      return;
    }
    
    setIsPolling(true);
    pollingIntervalRef.current = setInterval(refreshProgress, POLL_INTERVAL);
  }, [refreshProgress, analysis.status]);

  // 停止轮询
  const stopPolling = React.useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  // 自动轮询管理
  React.useEffect(() => {
    if (analysis.status === 'running' || analysis.status === 'pending') {
      startPolling();
    } else {
      stopPolling();
    }

    return () => {
      stopPolling();
    };
  }, [analysis.status, startPolling, stopPolling]);

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
    // 处理后端返回的AnalysisProgress格式
    console.log('Progress update received:', data);

    // 更新总体进度 - 当前API返回的是0-100的数值
    if (data.progress !== undefined) {
      setMetrics(prev => ({
        ...prev,
        overallProgress: data.progress,
      }));
    }

    // 更新当前步骤信息
    if (data.current_step) {
      setMetrics(prev => ({
        ...prev,
        currentStep: data.current_step,
      }));
    }

    // 更新消息 - 显示详细的步骤信息
    if (data.message) {
      console.log('Current message:', data.message);
      
      // 根据后端的current_step（1-10）映射到前端步骤索引（0-9）
      let currentStepIndex = 0;
      if (data.current_step && typeof data.current_step === 'number') {
        currentStepIndex = Math.max(0, Math.min(data.current_step - 1, steps.length - 1));
      } else {
        // 如果没有current_step，根据进度百分比估算
        const progressPercent = data.progress || 0;
        if (progressPercent >= 95) currentStepIndex = 9;
        else if (progressPercent >= 90) currentStepIndex = 8;
        else if (progressPercent >= 80) currentStepIndex = 7;
        else if (progressPercent >= 70) currentStepIndex = 6;
        else if (progressPercent >= 60) currentStepIndex = 5;
        else if (progressPercent >= 50) currentStepIndex = 4;
        else if (progressPercent >= 35) currentStepIndex = 3;
        else if (progressPercent >= 25) currentStepIndex = 2;
        else if (progressPercent >= 10) currentStepIndex = 1;
        else currentStepIndex = 0;
      }
      
      // 更新步骤状态
      setSteps(prev => 
        prev.map((step, index) => {
          if (index < currentStepIndex) {
            return {
              ...step,
              status: 'completed' as const,
              progress: 100,
              message: '已完成',
            };
          } else if (index === currentStepIndex) {
            return {
              ...step,
              status: data.status === 'completed' ? 'completed' : 'running' as const,
              progress: data.status === 'completed' ? 100 : Math.min(progressPercent, 100),
              message: data.message,
            };
          }
          return step;
        })
      );
    }

    // 更新预计剩余时间
    if (data.estimated_time_remaining) {
      setMetrics(prev => ({
        ...prev,
        estimatedTimeRemaining: data.estimated_time_remaining,
      }));
    }

    // 处理分析状态变化
    if (data.status) {
      switch (data.status) {
        case 'completed':
          // 所有步骤标记为完成
          setSteps(prev =>
            prev.map(step => ({
              ...step,
              status: 'completed' as const,
              progress: 100,
              message: '已完成',
            }))
          );
          setMetrics(prev => ({
            ...prev,
            completedSteps: prev.totalSteps,
            overallProgress: 100,
          }));
          
          // 停止轮询
          stopPolling();
          
          // 通知分析完成
          onComplete?.();
          break;
        case 'failed':
          // 标记当前步骤为错误
          setSteps(prev =>
            prev.map(step => ({
              ...step,
              status: step.status === 'running' ? 'error' : step.status,
              message: step.status === 'running' ? data.message || '步骤失败' : step.message,
            }))
          );
          onError?.(data.message || '分析失败');
          break;
        case 'cancelled':
          // 分析被取消
          setSteps(prev =>
            prev.map(step => ({
              ...step,
              status: step.status === 'running' ? 'error' : step.status,
              message: step.status === 'running' ? '分析已取消' : step.message,
            }))
          );
          onCancel?.();
          break;
      }
    }

    // 更新预计剩余时间
    if (data.estimated_time_remaining) {
      setMetrics(prev => ({
        ...prev,
        estimatedTimeRemaining: data.estimated_time_remaining,
      }));
    }
  }

  const handleStepStart = (data: any) => {
    setSteps(prev =>
      prev.map(step =>
        step.id === data.stepId
          ? {
              ...step,
              status: 'running',
              startTime: Date.now(),
              message: data.message || '正在执行...',
            }
          : step
      )
    );

    setMetrics(prev => ({
      ...prev,
      currentStep: data.stepName || prev.currentStep,
    }));
  };

  const handleStepProgress = (data: any) => {
    setSteps(prev =>
      prev.map(step =>
        step.id === data.stepId ? { ...step, progress: data.progress, message: data.message } : step
      )
    );
  };

  const handleStepComplete = (data: any) => {
    setSteps(prev =>
      prev.map(step =>
        step.id === data.stepId
          ? { ...step, status: 'completed', endTime: Date.now(), progress: 100, message: '已完成' }
          : step
      )
    );

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

  // 检查认证状态
  const token = localStorage.getItem('auth_token');
  const isAuthenticated = !!token;

  if (!isAuthenticated) {
    return (
      <div className="realtime-progress-dashboard">
        <Card>
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <h3>🔐 需要登录</h3>
            <p>请先登录以查看分析进度</p>
            <Button type="primary" onClick={() => window.location.href = '/login'}>
              前往登录
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="realtime-progress-dashboard">
      <ProgressNotifications analysis={analysis} enabled={true} />

      {/* Header with analysis info */}
      <Card className="dashboard-header">
        <Row justify="space-between" align="middle">
          <Col>
            <Space>
              <h3>分析进度 - {analysis.stockCode}</h3>
              <Tag color={getStatusColor(analysis.status)}>
                {analysis.status === 'running'
                  ? '运行中'
                  : analysis.status === 'pending'
                    ? '等待中'
                    : analysis.status === 'completed'
                      ? '已完成'
                      : analysis.status === 'failed'
                        ? '失败'
                        : analysis.status}
              </Tag>
              {lastUpdateTime && (
                <Tag color="blue">最后更新: {lastUpdateTime.toLocaleTimeString()}</Tag>
              )}
            </Space>
          </Col>
          <Col>
            <Space>
              <Button icon={<ReloadOutlined />} onClick={refreshProgress} loading={isRefreshing}>
                手动刷新
              </Button>
              {isPolling && (
                <Tag color="green" icon={<PlayCircleOutlined />}>
                  自动轮询中
                </Tag>
              )}
              {analysis.status === 'running' && (
                <Button danger icon={<StopOutlined />} onClick={handleCancel}>
                  取消分析
                </Button>
              )}
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
              value={
                metrics.estimatedTimeRemaining > 0
                  ? formatTime(metrics.estimatedTimeRemaining)
                  : '--'
              }
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

      {/* Detailed Steps */}
      <Card title="详细步骤" className="steps-card">
        <Timeline>
          {steps.map(step => (
            <Timeline.Item
              key={step.id}
              color={
                step.status === 'completed'
                  ? 'green'
                  : step.status === 'running'
                    ? 'blue'
                    : step.status === 'error'
                      ? 'red'
                      : 'gray'
              }
            >
              <div className="step-item">
                <div className="step-header">
                  <h4>{step.name}</h4>
                  <Tag color={getStatusColor(step.status)}>
                    {step.status === 'pending'
                      ? '等待中'
                      : step.status === 'running'
                        ? '进行中'
                        : step.status === 'completed'
                          ? '已完成'
                          : '错误'}
                  </Tag>
                </div>

                <p className="step-message">{step.message}</p>

                {step.status === 'running' && (
                  <Progress percent={step.progress} size="small" strokeColor="#1890ff" />
                )}

                {step.subTasks && step.subTasks.length > 0 && (
                  <div className="sub-tasks">
                    <p>
                      <strong>子任务:</strong>
                    </p>
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
