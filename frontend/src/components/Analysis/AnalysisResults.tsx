import React from 'react';
import {
  Card,
  Typography,
  Empty,
  Tabs,
  Button,
  Space,
  Tag,
  Descriptions,
  Alert,
  Spin,
  message,
} from 'antd';
import { 
  BarChartOutlined,
  FileTextOutlined,
  DownloadOutlined,
  ShareAltOutlined,
  ReloadOutlined,
  TrophyOutlined,
  DollarOutlined,
  LineChartOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { Analysis } from '@/types';
import { useAnalysis } from '@/hooks/useAnalysis';
import './AnalysisResults.css';

const { Title, Text, Paragraph } = Typography;
// Tabs 使用 items API

interface AnalysisResultsProps {
  analysis: Analysis | null;
}

const AnalysisResults: React.FC<AnalysisResultsProps> = ({ analysis }) => {
  const { getAnalysisResult } = useAnalysis();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = React.useState('overview');

  // 自动获取分析结果
  React.useEffect(() => {
    if (analysis && analysis.status === 'completed' && !analysis.resultData) {
      console.log('Analysis completed, fetching results for:', analysis.id);
      getAnalysisResult(analysis.id);
    }
  }, [analysis?.id, analysis?.status, analysis?.resultData, getAnalysisResult]);

  const handleExport = async () => {
    if (!analysis?.resultData) {
      message.warning('暂无分析结果可导出');
      return;
    }

    try {
      const printContent = `
        <html>
          <head>
            <title>股票分析报告 - ${analysis.stockCode}</title>
            <style>
              body { font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 20px; line-height: 1.6; }
              .header { text-align: center; border-bottom: 2px solid #0f766e; padding-bottom: 20px; margin-bottom: 30px; }
              .section { margin-bottom: 30px; }
              .section h2 { color: #0f766e; border-left: 4px solid #0f766e; padding-left: 10px; }
              pre { white-space: pre-wrap; background: #f5f5f5; padding: 10px; border-radius: 5px; }
            </style>
          </head>
          <body>
            <div class="header">
              <h1>股票分析报告</h1>
              <p><strong>股票代码:</strong> ${analysis.stockCode}</p>
              <p><strong>分析日期:</strong> ${new Date(analysis.createdAt).toLocaleDateString('zh-CN')}</p>
            </div>
            
            <div class="section">
              <h2>📊 投资建议</h2>
              <pre>${analysis.resultData.trader_investment_plan || '暂无投资建议'}</pre>
            </div>

            <div class="section">
              <h2>📈 基本面分析</h2>
              <pre>${analysis.resultData.fundamentals_report || '暂无基本面分析'}</pre>
            </div>

            <div class="section">
              <h2>📉 技术面分析</h2>
              <pre>${analysis.resultData.market_report || '暂无技术面分析'}</pre>
            </div>

            <div class="section">
              <h2>💭 市场情绪分析</h2>
              <pre>${analysis.resultData.sentiment_report || '暂无情绪分析'}</pre>
            </div>

            <div class="section">
              <h2>⚠️ 风险评估</h2>
              <pre>${analysis.resultData.risk_assessment || '暂无风险评估'}</pre>
            </div>
          </body>
        </html>
      `;

      const printWindow = window.open('', '_blank');
      if (printWindow) {
        printWindow.document.write(printContent);
        printWindow.document.close();
        printWindow.onload = () => {
          printWindow.print();
          printWindow.close();
        };
        message.success('正在生成PDF报告...');
      } else {
        message.error('无法打开打印窗口，请检查浏览器设置');
      }
    } catch (error) {
      console.error('Export error:', error);
      message.error('导出失败，请重试');
    }
  };

  const handleShare = () => {
    message.info('分享功能开发中...');
  };

  if (!analysis) {
    return (
      <Card className="results-card analysis-results-container">
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            <div>
              <Text type="secondary">暂无分析结果</Text>
              <br />
              <Text type="secondary" style={{ fontSize: '12px' }}>
                请先配置分析参数并开始分析
              </Text>
            </div>
          }
        />
      </Card>
    );
  }

  if (analysis.status === 'failed') {
    return (
      <Card className="results-card analysis-results-container">
        <Alert
          message="分析失败"
          description="分析过程中出现错误，请检查参数后重试。"
          type="error"
          showIcon
          action={
            <Button size="small" danger>
              重新分析
            </Button>
          }
        />
      </Card>
    );
  }

  if (analysis.status === 'completed' && !analysis.resultData) {
    return (
      <Card className="results-card analysis-results-container">
        <div className="loading-container">
          <Spin size="large" tip="正在加载分析结果..." />
        </div>
      </Card>
    );
  }

  if (!analysis.resultData) {
    return (
      <Card className="results-card analysis-results-container">
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="分析尚未完成" />
      </Card>
    );
  }

  const resultData = analysis.resultData;

  const renderOverview = () => {
    const traderPlan = resultData.trader_investment_plan || '';
    const decision = resultData.decision || {};

    const getRecommendation = () => {
      if (traderPlan.includes('卖出')) return '卖出';
      if (traderPlan.includes('买入')) return '买入';
      if (decision.action) return decision.action;
      return '观望';
    };

    const getTargetPrice = () => {
      if (decision.target_price) return decision.target_price;
      const priceMatch = traderPlan.match(/目标价位?[：:]\s*¥?(\d+)/);
      return priceMatch ? priceMatch[1] : 'N/A';
    };

    const getConfidence = () => {
      if (decision.confidence) return Math.round(decision.confidence * 100) + '%';
      const confidenceMatch = traderPlan.match(/置信度[：:]\s*([\d.]+)/);
      return confidenceMatch ? Math.round(parseFloat(confidenceMatch[1]) * 100) + '%' : 'N/A';
    };

    return (
      <div className="overview-section">
        <div
          className="summary-cards"
          style={{ display: 'flex', gap: '16px', marginBottom: '24px' }}
        >
          <Card size="small" style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <TrophyOutlined style={{ fontSize: '24px', color: 'var(--success-color)' }} />
              <div>
                <Text type="secondary">置信度</Text>
                <Title level={4} style={{ margin: 0, color: 'var(--success-color)' }}>
                  {getConfidence()}
                </Title>
              </div>
            </div>
          </Card>

          <Card size="small" style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <DollarOutlined style={{ fontSize: '24px', color: 'var(--warning-color)' }} />
              <div>
                <Text type="secondary">目标价格</Text>
                <Title level={4} style={{ margin: 0, color: 'var(--warning-color)' }}>
                  ¥{getTargetPrice()}
                </Title>
              </div>
            </div>
          </Card>

          <Card size="small" style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <LineChartOutlined
                style={{
                  fontSize: '24px',
                  color:
                    getRecommendation() === '买入'
                      ? '#52c41a'
                      : getRecommendation() === '卖出'
                        ? '#ff4d4f'
                        : 'var(--accent-color)',
                }}
              />
              <div>
                <Text type="secondary">投资建议</Text>
                <Title
                  level={4}
                  style={{
                    margin: 0,
                    color:
                      getRecommendation() === '买入'
                        ? '#52c41a'
                        : getRecommendation() === '卖出'
                          ? '#ff4d4f'
                          : 'var(--accent-color)',
                  }}
                >
                  {getRecommendation()}
                </Title>
              </div>
            </div>
          </Card>
        </div>

        <Card title="投资建议摘要" style={{ marginBottom: '24px' }}>
          <Paragraph style={{ whiteSpace: 'pre-wrap' }}>
            {resultData.trader_investment_plan || '暂无投资建议'}
          </Paragraph>
        </Card>

        <Descriptions title="基本信息" bordered column={2}>
          <Descriptions.Item label="股票代码">{analysis.stockCode}</Descriptions.Item>
          <Descriptions.Item label="分析时间">
            {new Date(analysis.createdAt).toLocaleString()}
          </Descriptions.Item>
          <Descriptions.Item label="完成时间">
            {analysis.completedAt ? new Date(analysis.completedAt).toLocaleString() : 'N/A'}
          </Descriptions.Item>
          <Descriptions.Item label="分析状态">
            <Tag color="success">已完成</Tag>
          </Descriptions.Item>
        </Descriptions>
      </div>
    );
  };

  const renderAnalystReports = () => {
    const reports = [
      {
        key: 'fundamentals',
        title: '📊 基本面分析',
        content: resultData.fundamentals_report,
        icon: <DollarOutlined />,
      },
      {
        key: 'technical',
        title: '📈 技术面分析',
        content: resultData.market_report,
        icon: <LineChartOutlined />,
      },
      {
        key: 'sentiment',
        title: '💭 市场情绪分析',
        content: resultData.sentiment_report,
        icon: <BarChartOutlined />,
      },
      {
        key: 'risk',
        title: '⚠️ 风险评估',
        content: resultData.risk_assessment,
        icon: <EyeOutlined />,
      },
    ];

    return (
      <div className="analyst-reports">
        {reports.map(report => (
          <Card
            key={report.key}
            title={
              <span>
                {report.icon}
                <span style={{ marginLeft: 8 }}>{report.title}</span>
              </span>
            }
            style={{ marginBottom: 16 }}
          >
            <Paragraph style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
              {report.content || '暂无相关分析报告'}
            </Paragraph>
          </Card>
        ))}
      </div>
    );
  };

  const renderCharts = () => (
    <div className="charts-section">
      <Card title="📊 投资决策分析">
        <Paragraph style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
          {resultData.investment_plan || '暂无投资决策分析'}
        </Paragraph>
      </Card>

      {resultData.final_trade_decision && (
        <Card title="🎯 最终交易决策" style={{ marginTop: 16 }}>
          <Paragraph style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
            {resultData.final_trade_decision}
          </Paragraph>
        </Card>
      )}

      {!resultData.investment_plan && !resultData.final_trade_decision && (
        <Empty description="暂无图表数据" />
      )}
    </div>
  );

  return (
    <Card className="results-card analysis-results-container">
      <div className="results-header" style={{ marginBottom: '24px' }}>
        <div className="header-content">
          <Title level={3} style={{ margin: 0 }}>
            {analysis.stockCode} 分析结果
          </Title>
          <Text type="secondary">
            分析完成时间:{' '}
            {analysis.completedAt ? new Date(analysis.completedAt).toLocaleString() : 'N/A'}
          </Text>
        </div>

        <Space>
          <Button
            icon={<EyeOutlined />}
            onClick={() => navigate(`/analysis/report/${analysis.id}`)}
          >
            详细报告
          </Button>
          <Button icon={<DownloadOutlined />} onClick={handleExport}>
            导出PDF
          </Button>
          <Button icon={<ShareAltOutlined />} onClick={handleShare}>
            分享
          </Button>
          <Button icon={<ReloadOutlined />} type="primary">
            重新分析
          </Button>
        </Space>
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'overview',
            label: (
              <span>
                <BarChartOutlined /> 概览
              </span>
            ),
            children: renderOverview(),
          },
          {
            key: 'reports',
            label: (
              <span>
                <FileTextOutlined /> 分析师报告
              </span>
            ),
            children: renderAnalystReports(),
          },
          {
            key: 'charts',
            label: (
              <span>
                <LineChartOutlined /> 图表分析
              </span>
            ),
            children: renderCharts(),
          },
        ]}
      />
    </Card>
  );
};

export default AnalysisResults;
