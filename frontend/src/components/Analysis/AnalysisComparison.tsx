import React, { useState, useEffect } from 'react';
import {
  Card,
  Typography,
  Table,
  Tag,
  Button,
  Space,
  Row,
  Col,
  Statistic,
  Select,
  DatePicker,
  Checkbox,
  Empty,
  Spin,
  Alert,
  Tooltip,
  Progress,
  Divider
} from 'antd';
import {
  CompareArrowsOutlined,
  TrophyOutlined,
  DollarOutlined,
  TrendingUpOutlined,
  BarChartOutlined,
  LineChartOutlined,
  InfoCircleOutlined,
  ExportOutlined
} from '@ant-design/icons';
import { Analysis } from '@/types';
import { useAnalysisStore } from '@/stores/analysisStore';
import ChartViewer from '@/components/Charts/ChartViewer';
import './AnalysisComparison.css';

const { Title, Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

interface AnalysisComparisonProps {
  selectedAnalyses: string[];
  onClose: () => void;
}

const AnalysisComparison: React.FC<AnalysisComparisonProps> = ({
  selectedAnalyses,
  onClose
}) => {
  const { analysisHistory, isLoading } = useAnalysisStore();
  const [comparisonData, setComparisonData] = useState<Analysis[]>([]);
  const [comparisonMode, setComparisonMode] = useState<'overview' | 'detailed'>('overview');
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>([
    'overallScore',
    'targetPrice',
    'recommendation'
  ]);

  useEffect(() => {
    const data = analysisHistory.filter(analysis => 
      selectedAnalyses.includes(analysis.id) && analysis.status === 'completed'
    );
    setComparisonData(data);
  }, [selectedAnalyses, analysisHistory]);

  if (isLoading) {
    return (
      <div className="comparison-loading">
        <Spin size="large" tip="正在加载对比数据..." />
      </div>
    );
  }

  if (comparisonData.length < 2) {
    return (
      <div className="comparison-empty">
        <Empty
          description="请至少选择两个已完成的分析进行对比"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
        <Button type="primary" onClick={onClose}>
          返回
        </Button>
      </div>
    );
  }

  const renderOverviewComparison = () => {
    const columns = [
      {
        title: '分析项目',
        dataIndex: 'metric',
        key: 'metric',
        fixed: 'left' as const,
        width: 120,
        render: (text: string) => <Text strong>{text}</Text>
      },
      ...comparisonData.map((analysis, index) => ({
        title: (
          <div className="comparison-header">
            <div>{analysis.stockCode}</div>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {new Date(analysis.createdAt).toLocaleDateString()}
            </Text>
          </div>
        ),
        dataIndex: `analysis_${index}`,
        key: `analysis_${index}`,
        width: 150,
        render: (value: any, record: any) => {
          if (record.type === 'score') {
            return (
              <div className="score-cell">
                <Progress
                  type="circle"
                  size={60}
                  percent={value * 10}
                  format={() => value}
                  strokeColor={getScoreColor(value)}
                />
              </div>
            );
          }
          if (record.type === 'price') {
            return (
              <Statistic
                value={value}
                precision={2}
                prefix="¥"
                valueStyle={{ fontSize: '16px' }}
              />
            );
          }
          if (record.type === 'recommendation') {
            return (
              <Tag color={getRecommendationColor(value)}>
                {value || 'N/A'}
              </Tag>
            );
          }
          return value || 'N/A';
        }
      }))
    ];

    const dataSource = [
      {
        key: 'score',
        metric: '综合评分',
        type: 'score',
        ...comparisonData.reduce((acc, analysis, index) => ({
          ...acc,
          [`analysis_${index}`]: analysis.resultData?.overallScore || 0
        }), {})
      },
      {
        key: 'price',
        metric: '目标价格',
        type: 'price',
        ...comparisonData.reduce((acc, analysis, index) => ({
          ...acc,
          [`analysis_${index}`]: analysis.resultData?.targetPrice || 0
        }), {})
      },
      {
        key: 'recommendation',
        metric: '投资建议',
        type: 'recommendation',
        ...comparisonData.reduce((acc, analysis, index) => ({
          ...acc,
          [`analysis_${index}`]: analysis.resultData?.recommendation
        }), {})
      }
    ];

    return (
      <div className="overview-comparison">
        <Card title="核心指标对比" className="comparison-card">
          <Table
            columns={columns}
            dataSource={dataSource}
            pagination={false}
            scroll={{ x: 'max-content' }}
            className="comparison-table"
          />
        </Card>

        <Row gutter={[16, 16]} className="comparison-stats">
          {comparisonData.map((analysis, index) => (
            <Col xs={24} sm={12} md={8} lg={6} key={analysis.id}>
              <Card className="analysis-summary-card">
                <div className="card-header">
                  <Title level={5}>{analysis.stockCode}</Title>
                  <Text type="secondary">
                    {new Date(analysis.createdAt).toLocaleDateString()}
                  </Text>
                </div>
                
                <div className="card-metrics">
                  <div className="metric-item">
                    <TrophyOutlined className="metric-icon" />
                    <div>
                      <Text type="secondary">评分</Text>
                      <div className="metric-value">
                        {analysis.resultData?.overallScore || 'N/A'}
                      </div>
                    </div>
                  </div>
                  
                  <div className="metric-item">
                    <DollarOutlined className="metric-icon" />
                    <div>
                      <Text type="secondary">目标价</Text>
                      <div className="metric-value">
                        ¥{analysis.resultData?.targetPrice || 'N/A'}
                      </div>
                    </div>
                  </div>
                  
                  <div className="metric-item">
                    <TrendingUpOutlined className="metric-icon" />
                    <div>
                      <Text type="secondary">建议</Text>
                      <Tag 
                        color={getRecommendationColor(analysis.resultData?.recommendation)}
                        className="recommendation-tag"
                      >
                        {analysis.resultData?.recommendation || 'N/A'}
                      </Tag>
                    </div>
                  </div>
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      </div>
    );
  };

  const renderDetailedComparison = () => {
    const detailColumns = [
      {
        title: '分析维度',
        dataIndex: 'dimension',
        key: 'dimension',
        fixed: 'left' as const,
        width: 150,
        render: (text: string) => <Text strong>{text}</Text>
      },
      ...comparisonData.map((analysis, index) => ({
        title: analysis.stockCode,
        dataIndex: `analysis_${index}`,
        key: `analysis_${index}`,
        render: (value: any, record: any) => {
          if (record.type === 'chart') {
            return (
              <div className="chart-preview">
                <ChartViewer 
                  charts={value} 
                  height={200}
                  preview={true}
                />
              </div>
            );
          }
          if (record.type === 'list') {
            return (
              <ul className="comparison-list">
                {(value || []).slice(0, 3).map((item: string, idx: number) => (
                  <li key={idx}>{item}</li>
                ))}
                {value && value.length > 3 && (
                  <li>... 还有 {value.length - 3} 项</li>
                )}
              </ul>
            );
          }
          return (
            <div className="comparison-text">
              {typeof value === 'string' ? (
                value.length > 100 ? `${value.substring(0, 100)}...` : value
              ) : (
                JSON.stringify(value) || 'N/A'
              )}
            </div>
          );
        }
      }))
    ];

    const detailDataSource = [
      {
        key: 'fundamental',
        dimension: '基本面分析',
        type: 'text',
        ...comparisonData.reduce((acc, analysis, index) => ({
          ...acc,
          [`analysis_${index}`]: analysis.resultData?.fundamentalAnalysis?.summary
        }), {})
      },
      {
        key: 'technical',
        dimension: '技术分析',
        type: 'text',
        ...comparisonData.reduce((acc, analysis, index) => ({
          ...acc,
          [`analysis_${index}`]: analysis.resultData?.technicalAnalysis?.summary
        }), {})
      },
      {
        key: 'news',
        dimension: '新闻分析',
        type: 'list',
        ...comparisonData.reduce((acc, analysis, index) => ({
          ...acc,
          [`analysis_${index}`]: analysis.resultData?.newsAnalysis?.keyPoints
        }), {})
      },
      {
        key: 'charts',
        dimension: '图表对比',
        type: 'chart',
        ...comparisonData.reduce((acc, analysis, index) => ({
          ...acc,
          [`analysis_${index}`]: analysis.resultData?.charts
        }), {})
      }
    ];

    return (
      <div className="detailed-comparison">
        <Card title="详细对比分析" className="comparison-card">
          <Table
            columns={detailColumns}
            dataSource={detailDataSource}
            pagination={false}
            scroll={{ x: 'max-content' }}
            className="detailed-comparison-table"
          />
        </Card>
      </div>
    );
  };

  const getScoreColor = (score: number) => {
    if (score >= 8) return '#52c41a';
    if (score >= 6) return '#faad14';
    return '#ff4d4f';
  };

  const getRecommendationColor = (recommendation: string) => {
    const colors: Record<string, string> = {
      '强烈买入': 'green',
      '买入': 'blue',
      '持有': 'orange',
      '卖出': 'red',
      '强烈卖出': 'red',
    };
    return colors[recommendation] || 'default';
  };

  const handleExportComparison = () => {
    // TODO: Implement export comparison functionality
    console.log('Export comparison data');
  };

  return (
    <div className="analysis-comparison">
      <div className="comparison-header">
        <div className="header-info">
          <Title level={4}>
            <CompareArrowsOutlined /> 分析对比
          </Title>
          <Text type="secondary">
            对比 {comparisonData.length} 个分析结果
          </Text>
        </div>
        
        <Space>
          <Select
            value={comparisonMode}
            onChange={setComparisonMode}
            style={{ width: 120 }}
          >
            <Option value="overview">概览对比</Option>
            <Option value="detailed">详细对比</Option>
          </Select>
          
          <Button 
            icon={<ExportOutlined />}
            onClick={handleExportComparison}
          >
            导出对比
          </Button>
          
          <Button onClick={onClose}>
            关闭
          </Button>
        </Space>
      </div>

      <div className="comparison-content">
        {comparisonMode === 'overview' ? renderOverviewComparison() : renderDetailedComparison()}
      </div>

      <div className="comparison-summary">
        <Card title="对比总结" className="summary-card">
          <div className="summary-insights">
            <Title level={5}>关键洞察</Title>
            <ul>
              <li>
                最高评分: {Math.max(...comparisonData.map(a => a.resultData?.overallScore || 0)).toFixed(1)}
                (来自 {comparisonData.find(a => a.resultData?.overallScore === Math.max(...comparisonData.map(a => a.resultData?.overallScore || 0)))?.stockCode})
              </li>
              <li>
                最高目标价: ¥{Math.max(...comparisonData.map(a => a.resultData?.targetPrice || 0)).toFixed(2)}
                (来自 {comparisonData.find(a => a.resultData?.targetPrice === Math.max(...comparisonData.map(a => a.resultData?.targetPrice || 0)))?.stockCode})
              </li>
              <li>
                建议分布: {Array.from(new Set(comparisonData.map(a => a.resultData?.recommendation).filter(Boolean))).join(', ')}
              </li>
            </ul>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default AnalysisComparison;