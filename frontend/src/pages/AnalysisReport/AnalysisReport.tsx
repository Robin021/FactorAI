import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Typography,
  Tabs,
  Button,
  Space,
  Drawer,
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
  SearchOutlined,
  FileTextOutlined,
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  TrophyOutlined,
  RiseOutlined,
  InfoCircleOutlined,
  ExportOutlined,
  MoreOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { Analysis } from '@/types';
import { useAnalysisStore } from '@/stores/analysisStore';
import { analysisService } from '@/services/analysis';
import ChartViewer from '@/components/Charts/ChartViewer';
import AnalysisForm from '@/components/Analysis/AnalysisForm';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './AnalysisReport.css';

const { Title, Text, Paragraph } = Typography;
// Tabs 使用 items API
const { Option } = Select;
const { RangePicker } = DatePicker;

interface AnalysisReportProps { }

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
  const [newAnalysisOpen, setNewAnalysisOpen] = useState(false);

  // 辅助函数
  const getScoreColor = (score: number) => {
    if (score >= 8) return '#52c41a';
    if (score >= 6) return '#faad14';
    if (score >= 4) return '#fa8c16';
    return '#f5222d';
  };

  const getRiskColor = (risk: number) => {
    if (risk <= 3) return '#52c41a';
    if (risk <= 5) return '#faad14';
    if (risk <= 7) return '#fa8c16';
    return '#f5222d';
  };

  const getRecommendationColor = (recommendation: string) => {
    const rec = recommendation?.toLowerCase();
    if (rec?.includes('买入') || rec?.includes('buy')) return 'green';
    if (rec?.includes('卖出') || rec?.includes('sell')) return 'red';
    if (rec?.includes('持有') || rec?.includes('hold')) return 'blue';
    return 'default';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'processing';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed': return '已完成';
      case 'running': return '进行中';
      case 'failed': return '失败';
      default: return '未知';
    }
  };

  useEffect(() => {
    if (id) {
      console.log('📊 加载分析报告:', id);
      // 强制重新获取最新数据
      getAnalysisResult(id);
    }
  }, [id]); // 移除 getAnalysisResult 依赖，避免重复调用

  useEffect(() => {
    loadAnalysisHistory();
  }, [loadAnalysisHistory]);

  // 自动刷新：如果分析状态是 running，每5秒刷新一次
  useEffect(() => {
    if (!currentAnalysis || !id) return;

    const status = currentAnalysis.status;
    
    // 如果分析正在进行中，设置定时刷新
    if (status === 'running' || status === 'pending') {
      console.log('⏳ 分析进行中，启动自动刷新...');
      const intervalId = setInterval(() => {
        console.log('🔄 自动刷新分析数据...');
        getAnalysisResult(id);
      }, 5000); // 每5秒刷新一次

      return () => {
        console.log('⏹️ 停止自动刷新');
        clearInterval(intervalId);
      };
    } else if (status === 'completed' && !currentAnalysis.resultData) {
      // 如果状态是完成但没有结果数据，立即重新获取
      console.log('✅ 分析已完成但缺少结果数据，重新获取...');
      getAnalysisResult(id);
    }
  }, [currentAnalysis?.status, currentAnalysis?.resultData, id]);

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
  const resultData = analysis?.resultData || {};

  // 调试：打印分析数据
  console.log('=== 分析报告数据 ===');
  console.log('analysis:', {
    id: analysis?.id,
    stockCode: analysis?.stockCode,
    status: analysis?.status,
    createdAt: analysis?.createdAt,
    completedAt: analysis?.completedAt,
    createdAtTime: analysis?.createdAt ? new Date(analysis.createdAt).getTime() : null,
    completedAtTime: analysis?.completedAt ? new Date(analysis.completedAt).getTime() : null,
    timeDiff: (analysis?.createdAt && analysis?.completedAt) 
      ? new Date(analysis.completedAt).getTime() - new Date(analysis.createdAt).getTime() 
      : null
  });
  console.log('resultData keys:', Object.keys(resultData));
  console.log('stock_name:', resultData.stock_name);
  console.log('company_name:', resultData.company_name);
  console.log('symbol_name:', resultData.symbol_name);
  console.log('==================');

  // 基于股票代码推断货币符号（简单判断：A股=¥，港股=HK$，美股=$）
  // 注意：不要在早期 return 之后再使用 hook，使用普通求值避免 hooks 次数不一致
  const currencySymbol = (() => {
    const code = analysis?.stockCode || '';
    if (/^\d{6}$/.test(code)) return '¥'; // A股6位数字
    if (/^\d{4,5}\.HK$/i.test(code)) return 'HK$'; // 港股
    return '$'; // 其他默认美元
  })();

  // 从后端返回的数据结构中提取信息
  const decision = resultData.decision || {};
  const reports = {
    market: resultData.china_market_report || '', // 中国市场分析（A股特点、政策影响等）
    technical: resultData.market_report || '', // 技术分析（价格走势、技术指标等）
    fundamental: resultData.fundamentals_report || '',
    sentiment: resultData.sentiment_report || '',
    news: resultData.news_report || ''
  };

  // 组装“研究团队决策”与“风险管理团队决策”Markdown内容
  const buildResearchTeamDecision = (): string => {
    const debate = resultData.investment_debate_state || {};
    const bull = debate?.bull_history || '';
    const bear = debate?.bear_history || '';
    const judge = debate?.judge_decision || '';
    if (!bull && !bear && !judge) return '';
    return [
      '### 🔬 研究团队决策',
      bull ? `#### 📈 多头研究员分析\n${bull}` : '',
      bear ? `#### 📉 空头研究员分析\n${bear}` : '',
      judge ? `#### 🎯 研究经理综合决策\n${judge}` : ''
    ].filter(Boolean).join('\n\n');
  };

  const buildRiskManagementDecision = (): string => {
    const risk = resultData.risk_debate_state || {};
    const risky = risk?.current_risky_response || risk?.risky_history || '';
    const safe = risk?.current_safe_response || risk?.safe_history || '';
    const neutral = risk?.current_neutral_response || risk?.neutral_history || '';
    const judge = risk?.judge_decision || '';
    if (!risky && !safe && !neutral && !judge) return '';
    return [
      '### 🛡️ 风险管理团队决策',
      risky ? `#### 🚀 激进分析师\n${risky}` : '',
      safe ? `#### 🛡️ 保守分析师\n${safe}` : '',
      neutral ? `#### ⚖️ 中性分析师\n${neutral}` : '',
      judge ? `#### 🎯 投资组合经理最终决策\n${judge}` : ''
    ].filter(Boolean).join('\n\n');
  };

  // 计算分析时长
  const calculateDuration = () => {
    if (!analysis?.createdAt || !analysis?.completedAt) return '未知';
    
    try {
      const start = new Date(analysis.createdAt).getTime();
      const end = new Date(analysis.completedAt).getTime();
      
      // 检查时间是否有效
      if (isNaN(start) || isNaN(end) || end < start) {
        return '未知';
      }
      
      const durationMs = end - start;
      
      // 如果时间差小于1秒，可能是数据异常（创建时就设置了完成时间）
      if (durationMs < 1000) {
        return '未知';
      }
      
      const seconds = Math.floor(durationMs / 1000);
      const minutes = Math.floor(seconds / 60);
      const hours = Math.floor(minutes / 60);
      
      if (hours > 0) {
        return `${hours}小时${minutes % 60}分钟`;
      } else if (minutes > 0) {
        return `${minutes}分钟${seconds % 60}秒`;
      } else {
        return `${seconds}秒`;
      }
    } catch (error) {
      console.error('计算时长失败:', error);
      return '未知';
    }
  };

  // 获取股票名称（从多个可能的字段中获取）
  const getStockName = () => {
    // 优先使用 analysis 对象中的 stockName（从数据库获取）
    if (analysis?.stockName && !analysis.stockName.startsWith('股票')) {
      return analysis.stockName;
    }
    // 尝试从结果数据中获取
    if (resultData.stock_name && !resultData.stock_name.startsWith('股票')) {
      return resultData.stock_name;
    }
    // 其他可能的字段
    if (resultData.company_name && !resultData.company_name.startsWith('股票')) {
      return resultData.company_name;
    }
    if (resultData.symbol_name && !resultData.symbol_name.startsWith('股票')) {
      return resultData.symbol_name;
    }
    // 最后使用股票代码
    return analysis?.stockCode || '未指定';
  };

  // 报告分类和组织（按照后端分析顺序排列）
  const reportSections = {
    overview: {
      title: '概览',
      icon: <BarChartOutlined />,
      data: {
        overallScore: (decision.confidence || 0) * 10, // 将0-1的置信度转换为0-10分
        targetPrice: decision.target_price || 0,
        recommendation: decision.action || '暂无建议',
        summary: decision.reasoning || '暂无分析摘要',
        riskScore: (decision.risk_score || 0) * 10,
        stockName: getStockName(),
        duration: calculateDuration()
      }
    },
    // 阶段1：分析师团队报告（按执行顺序）
    technical: {
      title: '技术分析',
      icon: <RiseOutlined />,
      data: {
        report: reports.technical
      }
    },
    news: {
      title: '新闻分析',
      icon: <FileTextOutlined />,
      data: {
        report: reports.news
      }
    },
    fundamental: {
      title: '基本面分析',
      icon: <LineChartOutlined />,
      data: {
        report: reports.fundamental
      }
    },
    sentiment: {
      title: '情绪分析',
      icon: <FileTextOutlined />,
      data: {
        report: reports.sentiment
      }
    },
    // 阶段2：研究团队决策
    research: {
      title: '研究团队决策',
      icon: <FileTextOutlined />,
      data: {
        report: buildResearchTeamDecision()
      }
    },
    // 阶段3：风险管理团队决策
    risk_management: {
      title: '风险管理团队决策',
      icon: <ExclamationCircleOutlined />,
      data: {
        report: buildRiskManagementDecision()
      }
    },
    // 可选：中国市场分析（如果有）
    market: {
      title: '市场分析',
      icon: <PieChartOutlined />,
      data: {
        report: reports.market
      }
    }
  };

  const renderOverview = () => {
    const overviewData = reportSections.overview.data;

    return (
      <div className="report-overview">
        <Row gutter={[16, 16]} className="overview-stats">
          <Col xs={24} sm={6}>
            <Card className="stat-card">
              <Statistic
                title="置信度评分"
                value={overviewData.overallScore}
                precision={1}
                suffix="/10"
                valueStyle={{ color: getScoreColor(overviewData.overallScore) }}
                prefix={<TrophyOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card className="stat-card">
              <Statistic
                title="目标价格"
                value={overviewData.targetPrice}
                precision={2}
                prefix={currencySymbol}
                valueStyle={{ color: 'var(--warning-color)' }}
                suffix={
                  <Tooltip title="基于分析师预测的目标价格">
                    <InfoCircleOutlined />
                  </Tooltip>
                }
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card className="stat-card">
              <Statistic
                title="风险评分"
                value={overviewData.riskScore}
                precision={1}
                suffix="/10"
                valueStyle={{ color: getRiskColor(overviewData.riskScore) }}
                prefix={<ExclamationCircleOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card className="stat-card">
              <div className="recommendation-stat">
                <Text type="secondary">投资建议</Text>
                <Tag
                  color={getRecommendationColor(overviewData.recommendation)}
                  className="recommendation-tag"
                >
                  {overviewData.recommendation}
                </Tag>
              </div>
            </Card>
          </Col>
        </Row>

        <Card title="分析摘要" className="summary-card">
          <Paragraph className="summary-text">
            {overviewData.summary}
          </Paragraph>
        </Card>

        <Card title="基本信息">
          <Descriptions bordered column={{ xs: 1, sm: 2, md: 3 }}>
            <Descriptions.Item label="股票代码">{analysis?.stockCode}</Descriptions.Item>
            <Descriptions.Item label="股票名称">{overviewData.stockName}</Descriptions.Item>
            <Descriptions.Item label="分析时长">{overviewData.duration}</Descriptions.Item>
            <Descriptions.Item label="分析时间">
              {analysis?.createdAt ? new Date(analysis.createdAt).toLocaleString() : 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="完成时间">
              {analysis?.completedAt ? new Date(analysis.completedAt).toLocaleString() : 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="分析状态">
              <Tag color={getStatusColor(analysis?.status || 'unknown')}>{getStatusText(analysis?.status || 'unknown')}</Tag>
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
  };

  const renderDetailedAnalysis = (sectionKey: string) => {
    const section = reportSections[sectionKey as keyof typeof reportSections];
    if (!section) return <Empty description="暂无数据" />;

    const data = section.data as any; // 使用 any 类型避免类型检查问题

    return (
      <div className="detailed-analysis">
        {data.report && (
          <Card title="详细报告">
            <div className="markdown-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {data.report}
              </ReactMarkdown>
            </div>
          </Card>
        )}

        {data.keyMetrics && (
          <Card title="关键指标">
            <Row gutter={[16, 16]}>
              {Object.entries(data.keyMetrics).map(([key, value]: [string, any]) => (
                <Col xs={12} sm={8} md={6} key={key}>
                  <Statistic
                    title={key}
                    value={value}
                    precision={2}
                  />
                </Col>
              ))}
            </Row>
          </Card>
        )}

        {data.charts && (
          <Card title="图表分析">
            <ChartViewer charts={data.charts} />
          </Card>
        )}

        {data.recommendations && (
          <Card title="建议">
            <Timeline
              items={data.recommendations.map((rec: string) => ({ children: rec }))}
            />
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
                  setSelectedAnalyses(selectedAnalyses.filter((id: string) => id !== record.id));
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
              {Array.from(new Set(analysisHistory.map((a: Analysis) => a.stockCode))).map((code: string) => (
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

  const handleShare = (key: string) => {
    message.info(`分享功能正在开发中: ${key}`);
    setShareModalVisible(false);
  };

  const handleExport = async (format: string) => {
    if (!id) return;

    try {
      message.loading(`正在导出为 ${format} 格式...`, 0);

      if (format === 'pdf') {
        // 与“分析与结果”页面导出保持一致：打开新窗口写入简化 HTML 再打印
        message.destroy();
        const rd: any = resultData || {};
        // 构建研究团队决策内容
        const investmentDebate = rd.investment_debate_state || {};
        const researchTeamSection = (investmentDebate.bull_history || investmentDebate.bear_history || investmentDebate.judge_decision) ? `
          <div class="section">
            <h2>🔬 研究团队决策</h2>
            ${investmentDebate.bull_history ? `
              <div class="subsection">
                <h3>📈 多头研究员分析</h3>
                <pre>${investmentDebate.bull_history}</pre>
              </div>
            ` : ''}
            ${investmentDebate.bear_history ? `
              <div class="subsection">
                <h3>📉 空头研究员分析</h3>
                <pre>${investmentDebate.bear_history}</pre>
              </div>
            ` : ''}
            ${investmentDebate.judge_decision ? `
              <div class="subsection">
                <h3>🎯 研究经理综合决策</h3>
                <pre>${investmentDebate.judge_decision}</pre>
              </div>
            ` : ''}
          </div>
        ` : '';

        // 构建风险管理团队决策内容
        const riskDebate = rd.risk_debate_state || {};
        const riskManagementSection = (riskDebate.risky_history || riskDebate.safe_history || riskDebate.neutral_history || riskDebate.judge_decision) ? `
          <div class="section">
            <h2>🛡️ 风险管理团队决策</h2>
            ${riskDebate.risky_history || riskDebate.current_risky_response ? `
              <div class="subsection">
                <h3>🚀 激进分析师观点</h3>
                <pre>${riskDebate.current_risky_response || riskDebate.risky_history}</pre>
              </div>
            ` : ''}
            ${riskDebate.safe_history || riskDebate.current_safe_response ? `
              <div class="subsection">
                <h3>🛡️ 保守分析师观点</h3>
                <pre>${riskDebate.current_safe_response || riskDebate.safe_history}</pre>
              </div>
            ` : ''}
            ${riskDebate.neutral_history || riskDebate.current_neutral_response ? `
              <div class="subsection">
                <h3>⚖️ 中性分析师观点</h3>
                <pre>${riskDebate.current_neutral_response || riskDebate.neutral_history}</pre>
              </div>
            ` : ''}
            ${riskDebate.judge_decision ? `
              <div class="subsection">
                <h3>🎯 投资组合经理最终决策</h3>
                <pre>${riskDebate.judge_decision}</pre>
              </div>
            ` : ''}
          </div>
        ` : '';

        // 构建最终决策内容
        const dec = decision || {};
        const finalDecisionSection = (rd.final_trade_decision || dec.action) ? `
          <div class="section">
            <h2>🎯 最终交易决策</h2>
            ${rd.final_trade_decision ? `<pre>${rd.final_trade_decision}</pre>` : ''}
            ${dec.action ? `
              <div class="decision-summary">
                <p><strong>操作建议:</strong> ${dec.action}</p>
                ${dec.target_price ? `<p><strong>目标价格:</strong> ${currencySymbol}${dec.target_price}</p>` : ''}
                ${dec.confidence ? `<p><strong>置信度:</strong> ${(dec.confidence * 100).toFixed(1)}%</p>` : ''}
                ${dec.reasoning ? `<p><strong>决策理由:</strong> ${dec.reasoning}</p>` : ''}
              </div>
            ` : ''}
          </div>
        ` : '';

        const printContent = `
          <html>
            <head>
              <meta charset="utf-8" />
              <title>股票分析报告 - ${analysis?.stockCode || ''}</title>
              <style>
                body { font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 20px; line-height: 1.6; color: #333; }
                .header { text-align: center; border-bottom: 2px solid #0f766e; padding-bottom: 20px; margin-bottom: 30px; }
                .header h1 { color: #0f766e; margin-bottom: 10px; }
                .section { margin-bottom: 30px; page-break-inside: avoid; }
                .section h2 { color: #0f766e; border-left: 4px solid #0f766e; padding-left: 10px; margin-bottom: 15px; }
                .subsection { margin: 20px 0; padding-left: 20px; }
                .subsection h3 { color: #14b8a6; font-size: 16px; margin-bottom: 10px; }
                pre { white-space: pre-wrap; background: #f5f5f5; padding: 15px; border-radius: 5px; border-left: 3px solid #14b8a6; }
                .decision-summary { background: #f0fdfa; padding: 15px; border-radius: 5px; border: 1px solid #14b8a6; }
                .decision-summary p { margin: 8px 0; }
                @media print {
                  body { margin: 15px; }
                  .section { page-break-inside: avoid; }
                }
              </style>
            </head>
            <body>
              <div class="header">
                <h1>📊 股票分析报告</h1>
                <p><strong>股票代码:</strong> ${analysis?.stockCode || ''}</p>
                <p><strong>分析日期:</strong> ${analysis?.createdAt ? new Date(analysis.createdAt).toLocaleDateString('zh-CN') : ''}</p>
                <p><strong>完成时间:</strong> ${analysis?.completedAt ? new Date(analysis.completedAt).toLocaleDateString('zh-CN') : ''}</p>
              </div>
              
              ${finalDecisionSection}
              
              <div class="section">
                <h2>📊 投资建议</h2>
                <pre>${rd.trader_investment_plan || rd.investment_plan || '暂无投资建议'}</pre>
              </div>
              
              ${researchTeamSection}
              
              ${riskManagementSection}
              
              <div class="section">
                <h2>📈 基本面分析</h2>
                <pre>${rd.fundamentals_report || '暂无基本面分析'}</pre>
              </div>
              
              <div class="section">
                <h2>📉 市场与技术分析</h2>
                <pre>${rd.market_report || '暂无市场分析'}</pre>
              </div>
              
              <div class="section">
                <h2>💭 市场情绪分析</h2>
                <pre>${rd.sentiment_report || '暂无情绪分析'}</pre>
              </div>
              
              <div class="section">
                <h2>⚠️ 风险评估</h2>
                <pre>${rd.risk_assessment || '暂无风险评估'}</pre>
              </div>
            </body>
          </html>`;

        const win = window.open('', '_blank');
        if (win) {
          win.document.write(printContent);
          win.document.close();
          win.onload = () => { win.print(); win.close(); };
          message.success('正在生成 PDF...');
        } else {
          message.error('无法打开打印窗口，请检查浏览器设置');
        }
      } else if (format === 'json') {
        // 导出JSON数据
        const jsonData = JSON.stringify(analysis?.resultData || {}, null, 2);
        const blob = new Blob([jsonData], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${analysis?.stockCode || 'analysis'}_data.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        message.destroy();
        message.success('JSON 数据导出成功');
      } else {
        message.destroy();
        message.warning(`${format} 格式导出功能正在开发中`);
      }

      setExportModalVisible(false);
    } catch (error: any) {
      message.destroy();
      message.error(`导出失败: ${error.message}`);
    }
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
            <Button type="primary" icon={<SearchOutlined />} onClick={() => setNewAnalysisOpen(true)}>
              新建分析
            </Button>
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
          items={[
            {
              key: 'overview',
              label: (
                <span>
                  <BarChartOutlined /> 概览
                </span>
              ),
              children: renderOverview(),
              forceRender: true,
            },
            ...Object.entries(reportSections)
              .slice(1)
              .filter(([key, section]) => {
                // 过滤掉空的报告部分
                const report = section.data?.report;
                return report && report.trim().length > 0;
              })
              .map(([key, section]) => ({
                key,
                label: (
                  <span>
                    {section.icon}
                    {section.title}
                  </span>
                ),
                children: renderDetailedAnalysis(key),
                forceRender: true,
              })),
          ]}
        />
      </div>

      {/* 历史记录对话框 */}
      <Modal
        title="历史分析记录"
        open={historyVisible}
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
        open={exportModalVisible}
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
        open={shareModalVisible}
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

      {/* 快速新建分析抽屉（在报告页也可直接发起新的分析） */}
      <Drawer
        title="新建股票分析"
        open={newAnalysisOpen}
        onClose={() => setNewAnalysisOpen(false)}
        width={520}
        destroyOnClose
      >
        <AnalysisForm
          onStarted={() => {
            setNewAnalysisOpen(false);
            // 启动后跳到“实时进度”页
            navigate('/analysis?focus=progress');
          }}
        />
      </Drawer>

    </div>
  );
};

export default AnalysisReport;
