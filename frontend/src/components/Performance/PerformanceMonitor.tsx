/**
 * 性能监控组件
 */
import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Progress, Alert, Table, Tag, Button } from 'antd';
import { 
  DashboardOutlined, 
  WarningOutlined, 
  CheckCircleOutlined,
  ReloadOutlined 
} from '@ant-design/icons';
import { usePerformance } from '../../hooks/usePerformance';
import { performanceMonitor } from '../../utils/performance';

interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  available_memory: number;
}

interface HealthStatus {
  status: 'healthy' | 'warning' | 'critical' | 'error';
  timestamp: number;
  system: SystemMetrics;
  issues: string[];
  monitoring_active: boolean;
}

interface Alert {
  alert_key: string;
  rule_name: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  metric_name: string;
  current_value: number;
  threshold: number;
  timestamp: number;
  tags: Record<string, string>;
}

const PerformanceMonitor: React.FC = () => {
  const { metrics, renderCount } = usePerformance();
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(false);

  // 获取系统健康状态
  const fetchHealthStatus = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/performance/health');
      const data = await response.json();
      setHealthStatus(data);
    } catch (error) {
      console.error('Failed to fetch health status:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取报警信息
  const fetchAlerts = async () => {
    try {
      const response = await fetch('/api/v1/performance/alerts');
      const data = await response.json();
      if (data.success) {
        setAlerts(data.data.alert_history || []);
      }
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
    }
  };

  useEffect(() => {
    fetchHealthStatus();
    fetchAlerts();

    // 定期刷新数据
    const interval = setInterval(() => {
      fetchHealthStatus();
      fetchAlerts();
    }, 30000); // 30秒

    return () => clearInterval(interval);
  }, []);

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'var(--success-color)';
      case 'warning':
        return 'var(--warning-color)';
      case 'critical':
        return '#ff4d4f';
      case 'error':
        return '#ff4d4f';
      default:
        return '#d9d9d9';
    }
  };

  // 获取严重程度标签颜色
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low':
        return 'blue';
      case 'medium':
        return 'orange';
      case 'high':
        return 'red';
      case 'critical':
        return 'magenta';
      default:
        return 'default';
    }
  };

  // 报警表格列定义
  const alertColumns = [
    {
      title: '规则名称',
      dataIndex: 'rule_name',
      key: 'rule_name',
    },
    {
      title: '严重程度',
      dataIndex: 'severity',
      key: 'severity',
      render: (severity: string) => (
        <Tag color={getSeverityColor(severity)}>{severity.toUpperCase()}</Tag>
      ),
    },
    {
      title: '指标',
      dataIndex: 'metric_name',
      key: 'metric_name',
    },
    {
      title: '当前值',
      dataIndex: 'current_value',
      key: 'current_value',
      render: (value: number) => value.toFixed(2),
    },
    {
      title: '阈值',
      dataIndex: 'threshold',
      key: 'threshold',
      render: (value: number) => value.toFixed(2),
    },
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp: number) => new Date(timestamp * 1000).toLocaleString(),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>
          <DashboardOutlined style={{ marginRight: '8px' }} />
          性能监控
        </h2>
        <Button 
          icon={<ReloadOutlined />} 
          onClick={() => {
            fetchHealthStatus();
            fetchAlerts();
          }}
          loading={loading}
        >
          刷新
        </Button>
      </div>

      {/* 系统状态概览 */}
      {healthStatus && (
        <Card title="系统状态" style={{ marginBottom: '24px' }}>
          <Row gutter={16}>
            <Col span={6}>
              <Statistic
                title="系统状态"
                value={healthStatus.status}
                valueStyle={{ color: getStatusColor(healthStatus.status) }}
                prefix={
                  healthStatus.status === 'healthy' ? 
                    <CheckCircleOutlined /> : 
                    <WarningOutlined />
                }
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="CPU 使用率"
                value={healthStatus.system.cpu_usage}
                suffix="%"
                valueStyle={{ 
                  color: healthStatus.system.cpu_usage > 80 ? '#ff4d4f' : 'var(--success-color)'
                }}
              />
              <Progress 
                percent={healthStatus.system.cpu_usage} 
                size="small" 
                status={healthStatus.system.cpu_usage > 80 ? 'exception' : 'normal'}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="内存使用率"
                value={healthStatus.system.memory_usage}
                suffix="%"
                valueStyle={{ 
                  color: healthStatus.system.memory_usage > 80 ? '#ff4d4f' : 'var(--success-color)'
                }}
              />
              <Progress 
                percent={healthStatus.system.memory_usage} 
                size="small" 
                status={healthStatus.system.memory_usage > 80 ? 'exception' : 'normal'}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="磁盘使用率"
                value={healthStatus.system.disk_usage}
                suffix="%"
                precision={1}
                valueStyle={{ 
                  color: healthStatus.system.disk_usage > 80 ? '#ff4d4f' : 'var(--success-color)'
                }}
              />
              <Progress 
                percent={healthStatus.system.disk_usage} 
                size="small" 
                status={healthStatus.system.disk_usage > 80 ? 'exception' : 'normal'}
              />
            </Col>
          </Row>

          {/* 系统问题提示 */}
          {healthStatus.issues && healthStatus.issues.length > 0 && (
            <Alert
              message="系统问题"
              description={
                <ul>
                  {healthStatus.issues.map((issue, index) => (
                    <li key={index}>{issue}</li>
                  ))}
                </ul>
              }
              type="warning"
              showIcon
              style={{ marginTop: '16px' }}
            />
          )}
        </Card>
      )}

      {/* 前端性能指标 */}
      <Card title="前端性能" style={{ marginBottom: '24px' }}>
        <Row gutter={16}>
          <Col span={6}>
            <Statistic
              title="页面加载时间"
              value={metrics.loadTime || 0}
              suffix="ms"
              precision={0}
              valueStyle={{ 
                color: (metrics.loadTime || 0) > 3000 ? '#ff4d4f' : 'var(--success-color)'
              }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="首次内容绘制"
              value={metrics.firstContentfulPaint || 0}
              suffix="ms"
              precision={0}
              valueStyle={{ 
                color: (metrics.firstContentfulPaint || 0) > 2000 ? '#ff4d4f' : 'var(--success-color)'
              }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="最大内容绘制"
              value={metrics.largestContentfulPaint || 0}
              suffix="ms"
              precision={0}
              valueStyle={{ 
                color: (metrics.largestContentfulPaint || 0) > 4000 ? '#ff4d4f' : 'var(--success-color)'
              }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="内存使用"
              value={metrics.memoryUsage || 0}
              suffix="MB"
              precision={1}
              valueStyle={{ 
                color: (metrics.memoryUsage || 0) > 100 ? '#ff4d4f' : 'var(--success-color)'
              }}
            />
          </Col>
        </Row>

        <Row gutter={16} style={{ marginTop: '16px' }}>
          <Col span={6}>
            <Statistic
              title="首次输入延迟"
              value={metrics.firstInputDelay || 0}
              suffix="ms"
              precision={1}
              valueStyle={{ 
                color: (metrics.firstInputDelay || 0) > 100 ? '#ff4d4f' : 'var(--success-color)'
              }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="累积布局偏移"
              value={metrics.cumulativeLayoutShift || 0}
              precision={3}
              valueStyle={{ 
                color: (metrics.cumulativeLayoutShift || 0) > 0.25 ? '#ff4d4f' : 'var(--success-color)'
              }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="组件渲染次数"
              value={renderCount}
              suffix="次"
            />
          </Col>
          <Col span={6}>
            <Button 
              type="primary" 
              onClick={() => performanceMonitor.reportMetrics()}
            >
              上报性能数据
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 报警历史 */}
      <Card title="报警历史">
        <Table
          columns={alertColumns}
          dataSource={alerts}
          rowKey="alert_key"
          pagination={{ pageSize: 10 }}
          size="small"
        />
      </Card>
    </div>
  );
};

export default PerformanceMonitor;
