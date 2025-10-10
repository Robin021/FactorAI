/**
 * 7步真实进度显示组件
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Card,
  Progress,
  Typography,
  Timeline,
  Button,
  Space,
  Tag,
  Row,
  Col,
  Statistic,
} from 'antd';
import {
  PlayCircleOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  StopOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { webSocketService } from '@/services/websocket';

const { Title, Text } = Typography;

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
  step_results?: Record<string, any>;
  llm_result?: string;
  analyst_type?: string;
}

interface StepInfo {
  id: string;
  name: string;
  description: string;
  weight: number;
  status: 'pending' | 'running' | 'completed' | 'error';
  icon: string;
  subTasks: string[];
}

interface SevenStepProgressProps {
  analysisId: string;
  onComplete?: (success: boolean) => void;
  onCancel?: () => void;
  showCancelButton?: boolean;
}

const SevenStepProgress: React.FC<SevenStepProgressProps> = ({
  analysisId,
  onComplete,
  onCancel,
  showCancelButton = true,
}) => {
  const [progressData, setProgressData] = useState<ProgressData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 🔧 新增：存储LLM分析结果
  const [llmResults, setLlmResults] = useState<{
    [key: string]: {
      analyst_type: string;
      result: string;
      timestamp: number;
    };
  }>({});

  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // 定义7个真实分析步骤
  const analysisSteps: StepInfo[] = [
    {
      id: 'stock_identification',
      name: '股票识别',
      description: '识别股票类型并获取基本信息',
      weight: 10,
      status: 'pending',
      icon: '🔍',
      subTasks: ['识别股票类型', '获取公司名称', '确定交易市场'],
    },
    {
      id: 'market_analysis',
      name: '市场分析',
      description: '技术指标分析和价格走势研究',
      weight: 15,
      status: 'pending',
      icon: '📈',
      subTasks: ['技术指标计算', '价格走势分析', '支撑阻力位识别'],
    },
    {
      id: 'fundamentals_analysis',
      name: '基本面分析',
      description: '财务数据分析和估值评估',
      weight: 15,
      status: 'pending',
      icon: '📊',
      subTasks: ['财务报表分析', '估值指标计算', '行业对比分析'],
    },
    {
      id: 'news_analysis',
      name: '新闻分析',
      description: '新闻事件影响和行业动态分析',
      weight: 10,
      status: 'pending',
      icon: '📰',
      subTasks: ['新闻事件收集', '影响评估', '政策分析'],
    },
    {
      id: 'sentiment_analysis',
      name: '情绪分析',
      description: '社交媒体情绪和市场热度分析',
      weight: 10,
      status: 'pending',
      icon: '💭',
      subTasks: ['社交媒体监控', '情绪指标计算', '热度分析'],
    },
    {
      id: 'investment_debate',
      name: '投资辩论',
      description: '多空观点辩论和投资决策制定',
      weight: 25,
      status: 'pending',
      icon: '⚖️',
      subTasks: ['多头观点分析', '空头风险评估', '综合决策制定'],
    },
    {
      id: 'risk_assessment',
      name: '风险评估',
      description: '风险管理评估和最终决策优化',
      weight: 15,
      status: 'pending',
      icon: '🛡️',
      subTasks: ['风险因素识别', '仓位建议', '最终决策优化'],
    },
  ];

  // 格式化时间显示
  const formatTime = useCallback((seconds: number): string => {
    if (seconds < 60) {
      return `${seconds.toFixed(0)}秒`;
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
      case 'pending':
        return 'default';
      case 'running':
        return 'processing';
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'cancelled':
        return 'warning';
      default:
        return 'default';
    }
  }, []);

  // 获取状态图标
  const getStatusIcon = useCallback((status: string) => {
    switch (status) {
      case 'pending':
        return <ClockCircleOutlined />;
      case 'running':
        return <PlayCircleOutlined spin />;
      case 'completed':
        return <CheckCircleOutlined />;
      case 'failed':
        return <ExclamationCircleOutlined />;
      case 'cancelled':
        return <StopOutlined />;
      default:
        return <ClockCircleOutlined />;
    }
  }, []);

  // 获取进度数据
  const fetchProgress = useCallback(async () => {
    if (isLoading) return;

    setIsLoading(true);
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/v1/analysis/${analysisId}/progress`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        // 避免浏览器缓存导致的陈旧进度
        cache: 'no-store'
      });

      if (response.ok) {
        const data: ProgressData = await response.json();
        setProgressData(data);
        setError(null);

        // 🔧 处理LLM分析结果
        if (data.llm_result && data.analyst_type) {
          const analystKey = `${data.analyst_type}_${Date.now()}`;  // 使用时间戳避免覆盖
          setLlmResults(prev => ({
            ...prev,
            [analystKey]: {
              analyst_type: data.analyst_type as string,
              result: data.llm_result as string,
              timestamp: Date.now(),
            },
          }));
        }

        // 检查是否完成
        if (data.status === 'completed' || data.status === 'failed') {
          onComplete?.(data.status === 'completed');
          // 停止轮询
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          
          // 如果分析成功完成，3秒后自动跳转到报告页面
          if (data.status === 'completed') {
            setTimeout(() => {
              console.log('🎯 分析完成，自动跳转到报告页面:', analysisId);
              window.location.href = `/analysis/report/${analysisId}`;
            }, 3000); // 3秒延迟，让用户看到完成状态
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
  }, [analysisId, onComplete]); // 移除isLoading依赖，避免重复创建定时器

  const fetchProgressRef = useRef(fetchProgress);
  fetchProgressRef.current = fetchProgress;

  // 使用 WebSocket 进行实时更新（与轮询并行，谁先到用谁）
  useEffect(() => {
    const listener = (data: any) => {
      if (!data || data.analysisId !== analysisId) return;
      setProgressData(prev => ({
        analysis_id: analysisId,
        status: (data.status || prev?.status || 'running') as any,
        current_step: typeof data.currentStep === 'number' ? (data.currentStep < 1 ? data.currentStep + 1 : data.currentStep) : (prev?.current_step || 0),
        total_steps: prev?.total_steps || 7,
        progress_percentage: typeof data.progress === 'number' ? Math.max(0, Math.min(1, data.progress / 100)) : (prev?.progress_percentage || 0),
        message: data.message || prev?.message || '分析中...',
        elapsed_time: prev?.elapsed_time || 0,
        estimated_remaining: prev?.estimated_remaining || 0,
        current_step_name: prev?.current_step_name || '分析中',
        timestamp: Date.now(),
      } as any));
    };

    try {
      webSocketService.subscribeToAnalysis(analysisId, listener);
    } catch (e) {
      // 忽略WS错误，轮询仍然有效
    }

    return () => {
      try { webSocketService.unsubscribeFromAnalysis(analysisId, listener); } catch (_) {}
    };
  }, [analysisId]);

  // 取消分析
  const handleCancel = useCallback(async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/v1/analysis/${analysisId}/cancel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
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

  // 手动刷新
  const handleRefresh = useCallback(() => {
    fetchProgress();
  }, [fetchProgress]);

  // 轮询逻辑 - 使用ref避免依赖问题
  useEffect(() => {
    // 立即获取一次进度
    fetchProgressRef.current();

    // 设置简单的轮询定时器
    intervalRef.current = setInterval(() => {
      fetchProgressRef.current();
    }, 3000); // 3秒轮询间隔

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [analysisId]); // 只依赖analysisId

  // 监听进度状态，完成时停止轮询
  useEffect(() => {
    if (progressData?.status === 'completed' || progressData?.status === 'failed') {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }
  }, [progressData?.status]);

  // 更新步骤状态
  const getUpdatedSteps = useCallback(() => {
    if (!progressData) return analysisSteps;

    // 兼容不同后端：有的返回0-based（0-6），有的返回1-based（1-7），还有可能是字符串
    const raw = (progressData as any).current_step;
    let currentStepNumber = 0; // 统一成 1-7 的编号

    if (typeof raw === 'number') {
      currentStepNumber = raw < 1 ? raw + 1 : raw; // 0-based -> +1
    } else if (typeof raw === 'string') {
      const n = parseInt(raw, 10);
      if (!Number.isNaN(n)) currentStepNumber = n < 1 ? n + 1 : n;
    }

    // 如果还拿不到，尝试用进度百分比推断当前步骤
    if (!currentStepNumber && typeof progressData.progress_percentage === 'number') {
      const total = progressData.total_steps || analysisSteps.length;
      const p = Math.max(0, Math.min(1, progressData.progress_percentage));
      currentStepNumber = Math.min(total, Math.max(1, Math.ceil(p * total)));
    }

    return analysisSteps.map((step, index) => {
      const stepNumber = index + 1; // 1-based
      if (stepNumber < currentStepNumber) return { ...step, status: 'completed' as const };
      if (stepNumber === currentStepNumber) return { ...step, status: 'running' as const };
      return { ...step, status: 'pending' as const };
    });
  }, [progressData, analysisSteps]);

  const currentSteps = getUpdatedSteps();

  if (!progressData && !error) {
    return (
      <Card title="📊 分析进度" loading={isLoading}>
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <Text>正在获取分析进度...</Text>
        </div>
      </Card>
    );
  }

  const { progress_percentage, message, elapsed_time, estimated_remaining, status } =
    progressData || {};



  return (
    <Card
      title={
        <Space>
          <span>📊 股票分析进度</span>
          {status && (
            <Tag color={getStatusColor(status)} icon={getStatusIcon(status)}>
              {status === 'running'
                ? '分析中'
                : status === 'completed'
                  ? '已完成'
                  : status === 'failed'
                    ? '失败'
                    : status === 'cancelled'
                      ? '已取消'
                      : '等待中'}
            </Tag>
          )}
        </Space>
      }
      extra={
        <Space>
          <Button
            type="text"
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
            loading={isLoading}
            size="small"
          >
            刷新
          </Button>
          {showCancelButton && (status === 'running' || status === 'pending') && (
            <Button type="text" danger icon={<StopOutlined />} onClick={handleCancel} size="small">
              取消
            </Button>
          )}
        </Space>
      }
    >
      {error && (
        <div style={{ marginBottom: 16 }}>
          <Text type="danger">{error}</Text>
        </div>
      )}

      {progressData && (
        <>
          {/* 总体进度条 */}
          <div style={{ marginBottom: 24 }}>
            <Progress
              percent={Math.round((progress_percentage || 0) * 100)}
              status={
                status === 'completed'
                  ? 'success'
                  : status === 'failed'
                    ? 'exception'
                    : status === 'running'
                      ? 'active'
                      : 'normal'
              }
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
              trailColor="#f0f0f0"
              showInfo={true}
            />
          </div>

          {/* 当前状态 */}
          <div style={{ marginBottom: 16 }}>
            <Title level={5}>当前状态</Title>
            <Text strong>{message}</Text>
          </div>

          {/* 7步骤详细显示 */}
          <div style={{ marginBottom: 16 }}>
            <Title level={5}>分析步骤</Title>
            <Timeline
              items={currentSteps.map(step => ({
                color:
                  step.status === 'completed'
                    ? 'green'
                    : step.status === 'running'
                      ? 'blue'
                      : 'gray',
                dot:
                  step.status === 'completed' ? (
                    <CheckCircleOutlined style={{ color: '#52c41a' }} />
                  ) : step.status === 'running' ? (
                    <PlayCircleOutlined spin style={{ color: 'var(--accent-color)' }} />
                  ) : (
                    <ClockCircleOutlined style={{ color: '#d9d9d9' }} />
                  ),
                children: (
                  <div>
                    <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
                      {step.icon} {step.name} ({step.weight}%)
                    </div>
                    <div style={{ color: '#666', marginBottom: '8px' }}>{step.description}</div>
                    <div style={{ fontSize: '12px', color: '#999' }}>
                      {step.subTasks.join(' • ')}
                    </div>
                  </div>
                ),
              }))}
            />
          </div>

          {/* 时间统计 */}
          <div style={{ marginBottom: 16 }}>
            <Title level={5}>时间统计</Title>
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="已用时间"
                  value={formatTime(elapsed_time || 0)}
                  prefix={<ClockCircleOutlined />}
                  valueStyle={{ fontSize: '16px' }}
                />
              </Col>
              {(estimated_remaining || 0) > 0 && status === 'running' && (
                <Col span={12}>
                  <Statistic
                    title="预计剩余"
                    value={formatTime(estimated_remaining || 0)}
                    prefix={<ClockCircleOutlined />}
                    valueStyle={{ fontSize: '16px', color: 'var(--accent-color)' }}
                  />
                </Col>
              )}
            </Row>
          </div>

          {/* 最后更新时间 */}
          <div
            style={{
              fontSize: '12px',
              color: '#999',
              textAlign: 'right',
              borderTop: '1px solid #f0f0f0',
              paddingTop: '8px',
            }}
          >
            最后更新: {new Date().toLocaleTimeString()}
          </div>
        </>
      )}

      {/* 🔧 新增：LLM分析结果显示区域 */}
      {Object.keys(llmResults).length > 0 && (
        <Card title="🤖 AI分析师结果" style={{ marginTop: 16 }}>
          {Object.values(llmResults).map((result, index) => (
            <div key={index} style={{ marginBottom: 16 }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  marginBottom: 8,
                  padding: '8px 12px',
                  backgroundColor: '#f0f9ff',
                  borderRadius: '6px',
                  border: '1px solid #e6f7ff',
                }}
              >
                <span
                  style={{
                    fontWeight: 'bold',
                    color: 'var(--accent-color)',
                    marginRight: 8,
                  }}
                >
                  {result.analyst_type}
                </span>
                <span
                  style={{
                    fontSize: '12px',
                    color: '#666',
                    marginLeft: 'auto',
                  }}
                >
                  {new Date(result.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <div
                style={{
                  padding: '12px',
                  backgroundColor: '#fafafa',
                  borderRadius: '6px',
                  border: '1px solid #f0f0f0',
                  fontSize: '14px',
                  lineHeight: '1.6',
                  maxHeight: '200px',
                  overflowY: 'auto',
                  whiteSpace: 'pre-wrap',
                }}
              >
                {result.result}
              </div>
            </div>
          ))}
        </Card>
      )}
    </Card>
  );
};

export default SevenStepProgress;
