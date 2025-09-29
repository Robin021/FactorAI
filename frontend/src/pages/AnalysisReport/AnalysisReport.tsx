import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Typography,
  Tabs,
  Button,
  Space,
  Tag,
  Descriptions,
  Alert,
  Spin,
  Empty,
  Row,
  Col,
  Statistic,
  Timeline,
  Table,
  Modal,
  message,
  Dropdown,
  Menu,
  Tooltip,
  Select,
  DatePicker,
  Checkbox
} from 'antd';
import {
  ArrowLeftOutlined,
  DownloadOutlined,
  ShareAltOutlined,
  PrinterOutlined,
  HistoryOutlined,
  FileTextOutlined,
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  TrophyOutlined,
  RiseOutlined,
  InfoCircleOutlined,
  ExportOutlined,
  MoreOutlined
} from '@ant-design/icons';
import { Analysis } from '@/types';
import { useAnalysisStore } from '@/stores/analysisStore';
import ChartViewer from '@/components/Charts/ChartViewer';
import './AnalysisReport.css';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { Option } = Select;
const { RangePicker } = DatePicker;

interface AnalysisReportProps {}

const AnalysisReport: React.FC<AnalysisReportProps> = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const printRef = useRef<HTMLDivElement>(null);
  
  const {
    currentAnalysis,
    analysisHistory,
    isLoading,
    error,
    getAnalysisResult,
    loadAnalysisHistory
  } = useAnalysisStore();

  const [activeTab, setActiveTab] = useState('overview');
  const [selectedAnalyses, setSelectedAnalyses] = useState<string[]>([]);
  const [historyVisible, setHistoryVisible] = useState(false);
  const [exportModalVisible, setExportModalVisible] = useState(false);
  const [shareModalVisible, setShareModalVisible] = useState(false);

  useEffect(() => {
    if (id) {
      getAnalysisResult(id);
    }
  }, [id, getAnalysisResult]);

  useEffect(() => {
    loadAnalysisHistory();
  }, [loadAnalysisHistory]);

  if (isLoading) {
    return (
      <div className="analysis-report-loading">
        <Spin size="large" tip="正在加载分析报告..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="analysis-report-error">
        <Alert
          message="加载失败"
          description={error}
          type="error"
          showIcon
          action={
            <Button size="small" onClick={() => id && getAnalysisResult(id)}>
              重试
            </Button>
          }
        />
      </div>
    );
  }

  if (!currentAnalysis) {
    return (
      <div className="analysis-report-empty">
        <Empty
          description="未找到分析报告"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
        <Button type="primary" onClick={() => navigate('/analysis')}>
          返回分析页面
        </Button>
      </div>
    );
  }

  const analysis = currentAnalysis;
  const resultData = analysis.resultData || {};

  // 报告分类和组织
  const reportSections = {
    overview: {
      title: '概览',
      icon: <BarChartOutlined />,
      data: {
        overallScore: resultData.overallScore,
        targetPrice: resultData.targetPrice,
        recommendation: resultData.recommendation,
        summary: resultData.summary
      }
    },
    fundamental: {
      title: '基本面分析',
      icon: <LineChartOutlined />,
      data: resultData.fundamentalAnalysis || {}
    },
    technical: {
      title: '技术分析',
      icon: <RiseOutlined />,
      data: resultData.technicalAnalysis || {}
    },
    market: {
      title: '市场分析',
      icon: <PieChartOutlined />,
      data: resultData.marketAnalysis || {}
    },
    news: {
      title: '新闻分析',
      icon: <FileTextOutlined />,
      data: resultData.newsAnalysis || {}
    }
  };

  const renderOverview = () => (
    <div className="report-overview">
      <Row gutter={[16, 16]} className="overview-stats">
        <Col xs={24} sm={8}>
          <Card className="stat-card">
            <Statistic
              title="综合评分"
              value={resultData.overallScore || 0}
              precision={1}
              suffix="/10"
              valueStyle={{ color: getScoreColor(resultData.overallScore) }}
              prefix={<TrophyOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card className="stat-card">
            <Statistic
              title="目标价格"
              value={resultData.targetPrice || 0}
              precision={2}
              prefix="¥"
              valueStyle={{ color: '#faad14' }}
              suffix={
                <Tooltip title="基于分析师预测的目标价格">
                  <InfoCircleOutlined />
                </Tooltip>
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card className="stat-card">
            <div className="recommendation-stat">
              <Text type="secondary">投资建议</Text>
              <Tag 
                color={getRecommendationColor(resultData.recommendation)}
                className="recommendation-tag"
              >
                {resultData.recommendation || '暂无建议'}
              </Tag>
            </div>
          </Card>
        </Col>
      </Row>

      <Card title="分析摘要" className="summary-card">
        <Paragraph className="summary-text">
          {resultData.summary || '暂无分析摘要'}
        </Paragraph>
      </Card>

      <Card title="基本信息">
        <Descriptions bordered column={{ xs: 1, sm: 2, md: 3 }}>
          <Descriptions.Item label="股票代码">{analysis.stockCode}</Descriptions.Item>
          <Descriptions.Item label="分析时间">
            {new Date(analysis.createdAt).toLocaleString()}
          </Descriptions.Item>
          <Descriptions.Item label="完成时间">
            {analysis.completedAt ? new Date(analysis.completedAt).toLocaleString() : 'N/A'}
          </Descriptions.Item>
          <Descriptions.Item label="分析状态">
            <Tag color={getStatusColor(analysis.status)}>{getStatusText(analysis.status)}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="分析师">
            {resultData.analysts?.join(', ') || '未指定'}
          </Descriptions.Item>
          <Descriptions.Item label="数据源">
            {resultData.dataSources?.join(', ') || '未指定'}
          </Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  );

  const renderDetailedAnalysis = (sectionKey: string) => {
    const section = reportSections[sectionKey as keyof typeof reportSections];
    if (!section) return <Empty description="暂无数据" />;

    const data = section.data;
    
    return (
      <div className="detailed-analysis">
        {data.summary && (
          <Card title="分析摘要" className="analysis-summary">
            <Paragraph>{data.summary}</Paragraph>
          </Card>
        )}

        {data.keyMetrics && (
          <Card title="关键指标">
            <Row gutter={[16, 16]}>
              {Object.entries(data.keyMetrics).map(([key, value]: [string, any]) => (
                <Col xs={12} sm={8} md={6} key={key}>
                  <Statistic
                    title={getMetricName(key)}
                    value={value}
                    precision={2}
                  />
                </Col>
              ))}
            </Row>
          </Card>
        )}

        {data.analysis && (
          <Card title="详细分析">
            <Paragraph>{data.analysis}</Paragraph>
          </Card>
        )}

        {data.charts && (
          <Card title="图表分析">
            <ChartViewer charts={data.charts} />
          </Card>
        )}

        {data.recommendations && (
          <Card title="建议">
            <Timeline>
              {data.recommendations.map((rec: string, index: number) => (
                <Timeline.Item key={index}>{rec}</Timeline.Item>
              ))}
            </Timeline>
          </Card>
        )}
      </div>
    );
  };

  const renderHistoryComparison = () => {
    const historyColumns = [
      {
        title: '分析时间',
        dataIndex: 'createdAt',
        key: 'createdAt',
        render: (date: string) => new Date(date).toLocaleDateString(),
      },
      {
        title: '股票代码',
        dataIndex: 'stockCode',
        key: 'stockCode',
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        render: (status: string) => (
          <Tag color={getStatusColor(status)}>{getStatusText(status)}</Tag>
        ),
      },
      {
        title: '综合评分',
        dataIndex: 'resultData',
        key: 'score',
        render: (resultData: any) => resultData?.overallScore || 'N/A',
      },
      {
        title: '操作',
        key: 'actions',
        render: (record: Analysis) => (
          <Space>
            <Button size="small" onClick={() => navigate(`/analysis/report/${record.id}`)}>
              查看
            </Button>
            <Checkbox
              checked={selectedAnalyses.includes(record.id)}
              onChange={(e) => {
                if (e.target.checked) {
                  setSelectedAnalyses([...selectedAnalyses, record.id]);
                } else {
                  setSelectedAnalyses(selectedAnalyses.filter(id => id !== record.id));
                }
              }}
            >
              对比
            </Checkbox>
          </Space>
        ),
      },
    ];

    return (
      <div className="history-comparison">
        <div className="history-controls">
          <Space>
            <RangePicker placeholder={['开始日期', '结束日期']} />
            <Select placeholder="选择股票代码" style={{ width: 120 }}>
              {Array.from(new Set(analysisHistory.map(a => a.stockCode))).map(code => (
                <Option key={code} value={code}>{code}</Option>
              ))}
            </Select>
            <Button 
              type="primary" 
              disabled={selectedAnalyses.length < 2}
              onClick={() => console.log('Compare analyses:', selectedAnalyses)}
            >
              对比分析 ({selectedAnalyses.length})
            </Button>
          </Space>
        </div>

        <Table
          columns={historyColumns}
          dataSource={analysisHistory}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          className="history-table"
        />
      </div>
    );
  };

  const handlePrint = () => {
    window.print();
  };

  const handleExport = (format: string) => {
    // TODO: Implement export functionality
    message.success(`正在导出为 ${format} 格式...`);
    setExportModalVisible(false);
  };

  const handleShare = (method: string) => {
    // TODO: Implement share functionality
    message.success(`正在通过 ${method} 分享...`);
    setShareModalVisible(false);
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

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'processing',
      running: 'processing',
      completed: 'success',
      failed: 'error',
    };
    return colors[status] || 'default';
  };

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      pending: '等待中',
      running: '分析中',
      completed: '已完成',
      failed: '失败',
    };
    return texts[status] || status;
  };

  const getMetricName = (key: string) => {
    const names: Record<string, string> = {
      pe: '市盈率',
      pb: '市净率',
      roe: 'ROE',
      roa: 'ROA',
      revenue: '营收',
      profit: '净利润',
      // Add more metric names as needed
    };
    return names[key] || key;
  };

  const exportMenu = (
    <Menu onClick={({ key }) => handleExport(key)}>
      <Menu.Item key="pdf">PDF 报告</Menu.Item>
      <Menu.Item key="excel">Excel 数据</Menu.Item>
      <Menu.Item key="word">Word 文档</Menu.Item>
      <Menu.Item key="json">JSON 数据</Menu.Item>
    </Menu>
  );

  const shareMenu = (
    <Menu onClick={({ key }) => handleShare(key)}>
      <Menu.Item key="email">邮件分享</Menu.Item>
      <Menu.Item key="link">生成链接</Menu.Item>
      <Menu.Item key="wechat">微信分享</Menu.Item>
    </Menu>
  );

  const moreMenu = (
    <Menu>
      <Menu.Item key="duplicate" onClick={() => navigate(`/analysis?template=${analysis.id}`)}>
        复制分析
      </Menu.Item>
      <Menu.Item key="schedule">
        定时分析
      </Menu.Item>
      <Menu.Item key="alert">
        设置提醒
      </Menu.Item>
    </Menu>
  );

  return (
    <div className="analysis-report" ref={printRef}>
      <div className="report-header no-print">
        <div className="header-left">
          <Button 
            icon={<ArrowLeftOutlined />} 
            onClick={() => navigate('/analysis')}
            className="back-button"
          >
            返回
          </Button>
          <div className="header-info">
            <Title level={3} className="report-title">
              {analysis.stockCode} 分析报告
            </Title>
            <Text type="secondary">
              {new Date(analysis.createdAt).toLocaleString()}
            </Text>
          </div>
        </div>

        <div className="header-actions">
          <Space>
            <Button 
              icon={<HistoryOutlined />}
              onClick={() => setHistoryVisible(true)}
            >
              历史记录
            </Button>
            <Button 
              icon={<PrinterOutlined />}
              onClick={handlePrint}
            >
              打印
            </Button>
            <Dropdown overlay={exportMenu} placement="bottomRight">
              <Button icon={<DownloadOutlined />}>
                导出
              </Button>
            </Dropdown>
            <Dropdown overlay={shareMenu} placement="bottomRight">
              <Button icon={<ShareAltOutlined />}>
                分享
              </Button>
            </Dropdown>
            <Dropdown overlay={moreMenu} placement="bottomRight">
              <Button icon={<MoreOutlined />} />
            </Dropdown>
          </Space>
        </div>
      </div>

      <div className="report-content">
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab}
          className="report-tabs"
          tabPosition="top"
        >
          <TabPane 
            tab={
              <span>
                <BarChartOutlined />
                概览
              </span>
            } 
            key="overview"
          >
            {renderOverview()}
          </TabPane>

          {Object.entries(reportSections).slice(1).map(([key, section]) => (
            <TabPane
              tab={
                <span>
                  {section.icon}
                  {section.title}
                </span>
              }
              key={key}
            >
              {renderDetailedAnalysis(key)}
            </TabPane>
          ))}
        </Tabs>
      </div>

      {/* 历史记录对话框 */}
      <Modal
        title="历史分析记录"
        visible={historyVisible}
        onCancel={() => setHistoryVisible(false)}
        width={1000}
        footer={null}
        className="history-modal"
      >
        {renderHistoryComparison()}
      </Modal>

      {/* 导出对话框 */}
      <Modal
        title="导出分析报告"
        visible={exportModalVisible}
        onCancel={() => setExportModalVisible(false)}
        footer={null}
      >
        <div className="export-options">
          <Title level={5}>选择导出格式</Title>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Button block onClick={() => handleExport('pdf')}>
              <ExportOutlined /> PDF 报告 (推荐)
            </Button>
            <Button block onClick={() => handleExport('excel')}>
              <ExportOutlined /> Excel 数据表
            </Button>
            <Button block onClick={() => handleExport('word')}>
              <ExportOutlined /> Word 文档
            </Button>
            <Button block onClick={() => handleExport('json')}>
              <ExportOutlined /> JSON 数据
            </Button>
          </Space>
        </div>
      </Modal>

      {/* 分享对话框 */}
      <Modal
        title="分享分析报告"
        visible={shareModalVisible}
        onCancel={() => setShareModalVisible(false)}
        footer={null}
      >
        <div className="share-options">
          <Title level={5}>选择分享方式</Title>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Button block onClick={() => handleShare('email')}>
              <ShareAltOutlined /> 邮件分享
            </Button>
            <Button block onClick={() => handleShare('link')}>
              <ShareAltOutlined /> 生成分享链接
            </Button>
            <Button block onClick={() => handleShare('wechat')}>
              <ShareAltOutlined /> 微信分享
            </Button>
          </Space>
        </div>
      </Modal>
    </div>
  );
};

export default AnalysisReport;