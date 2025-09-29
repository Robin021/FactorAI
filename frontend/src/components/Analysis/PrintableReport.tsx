import React from 'react';
import {
  Card,
  Typography,
  Descriptions,
  Tag,
  Row,
  Col,
  Statistic,
  Timeline,
  Table,
  Divider
} from 'antd';
import {
  TrophyOutlined,
  DollarOutlined,
  TrendingUpOutlined,
  CalendarOutlined
} from '@ant-design/icons';
import { Analysis } from '@/types';
import './PrintableReport.css';

const { Title, Text, Paragraph } = Typography;

interface PrintableReportProps {
  analysis: Analysis;
  includeCharts?: boolean;
  includeDetailedAnalysis?: boolean;
}

const PrintableReport: React.FC<PrintableReportProps> = ({
  analysis,
  includeCharts = false,
  includeDetailedAnalysis = true
}) => {
  const resultData = analysis.resultData || {};

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

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      pending: '等待中',
      running: '分析中',
      completed: '已完成',
      failed: '失败',
    };
    return texts[status] || status;
  };

  const renderHeader = () => (
    <div className="print-header">
      <div className="header-content">
        <Title level={2} className="report-title">
          股票分析报告
        </Title>
        <div className="header-info">
          <Text className="stock-code">{analysis.stockCode}</Text>
          <Text className="report-date">
            报告日期: {new Date(analysis.createdAt).toLocaleDateString()}
          </Text>
        </div>
      </div>
      <div className="header-logo">
        {/* Company logo or branding can go here */}
        <Text type="secondary">TradingAgents 分析系统</Text>
      </div>
    </div>
  );

  const renderExecutiveSummary = () => (
    <Card title="执行摘要" className="print-section">
      <Row gutter={[24, 16]} className="summary-stats">
        <Col span={8}>
          <div className="summary-stat">
            <TrophyOutlined className="stat-icon" />
            <div className="stat-content">
              <Text type="secondary">综合评分</Text>
              <Title level={3} style={{ color: getScoreColor(resultData.overallScore), margin: 0 }}>
                {resultData.overallScore || 'N/A'}/10
              </Title>
            </div>
          </div>
        </Col>
        <Col span={8}>
          <div className="summary-stat">
            <DollarOutlined className="stat-icon" />
            <div className="stat-content">
              <Text type="secondary">目标价格</Text>
              <Title level={3} style={{ color: '#faad14', margin: 0 }}>
                ¥{resultData.targetPrice || 'N/A'}
              </Title>
            </div>
          </div>
        </Col>
        <Col span={8}>
          <div className="summary-stat">
            <TrendingUpOutlined className="stat-icon" />
            <div className="stat-content">
              <Text type="secondary">投资建议</Text>
              <Tag 
                color={getRecommendationColor(resultData.recommendation)}
                className="recommendation-tag"
              >
                {resultData.recommendation || 'N/A'}
              </Tag>
            </div>
          </div>
        </Col>
      </Row>

      <Divider />

      <div className="summary-text">
        <Title level={4}>分析概述</Title>
        <Paragraph>
          {resultData.summary || '本次分析针对股票代码 ' + analysis.stockCode + ' 进行了全面的基本面、技术面和市场情绪分析。'}
        </Paragraph>
      </div>
    </Card>
  );

  const renderBasicInfo = () => (
    <Card title="基本信息" className="print-section">
      <Descriptions bordered column={2} size="small">
        <Descriptions.Item label="股票代码">{analysis.stockCode}</Descriptions.Item>
        <Descriptions.Item label="分析状态">
          <Tag color="success">{getStatusText(analysis.status)}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="分析开始时间">
          {new Date(analysis.createdAt).toLocaleString()}
        </Descriptions.Item>
        <Descriptions.Item label="分析完成时间">
          {analysis.completedAt ? new Date(analysis.completedAt).toLocaleString() : 'N/A'}
        </Descriptions.Item>
        <Descriptions.Item label="分析师类型">
          {resultData.analysts?.join(', ') || '综合分析'}
        </Descriptions.Item>
        <Descriptions.Item label="数据源">
          {resultData.dataSources?.join(', ') || '多源数据'}
        </Descriptions.Item>
      </Descriptions>
    </Card>
  );

  const renderAnalysisDetails = () => {
    if (!includeDetailedAnalysis) return null;

    const analysisTypes = [
      {
        key: 'fundamental',
        title: '基本面分析',
        data: resultData.fundamentalAnalysis
      },
      {
        key: 'technical',
        title: '技术分析',
        data: resultData.technicalAnalysis
      },
      {
        key: 'market',
        title: '市场分析',
        data: resultData.marketAnalysis
      },
      {
        key: 'news',
        title: '新闻分析',
        data: resultData.newsAnalysis
      }
    ];

    return (
      <div className="analysis-details">
        {analysisTypes.map(({ key, title, data }) => {
          if (!data) return null;

          return (
            <Card key={key} title={title} className="print-section analysis-section">
              {data.summary && (
                <div className="analysis-summary">
                  <Title level={5}>分析摘要</Title>
                  <Paragraph>{data.summary}</Paragraph>
                </div>
              )}

              {data.keyMetrics && (
                <div className="key-metrics">
                  <Title level={5}>关键指标</Title>
                  <Row gutter={[16, 8]}>
                    {Object.entries(data.keyMetrics).map(([metricKey, value]: [string, any]) => (
                      <Col span={12} key={metricKey}>
                        <Statistic
                          title={getMetricName(metricKey)}
                          value={value}
                          precision={2}
                          className="metric-item"
                        />
                      </Col>
                    ))}
                  </Row>
                </div>
              )}

              {data.keyPoints && (
                <div className="key-points">
                  <Title level={5}>关键要点</Title>
                  <Timeline size="small">
                    {data.keyPoints.map((point: string, index: number) => (
                      <Timeline.Item key={index}>{point}</Timeline.Item>
                    ))}
                  </Timeline>
                </div>
              )}

              {data.recommendations && (
                <div className="recommendations">
                  <Title level={5}>建议</Title>
                  <ul className="recommendation-list">
                    {data.recommendations.map((rec: string, index: number) => (
                      <li key={index}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </Card>
          );
        })}
      </div>
    );
  };

  const renderRiskDisclaimer = () => (
    <Card title="风险提示" className="print-section disclaimer">
      <Paragraph type="secondary" className="disclaimer-text">
        本报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。
        本分析基于公开信息和历史数据，市场情况可能发生变化。
        投资者应根据自身情况做出独立判断，并承担相应风险。
      </Paragraph>
    </Card>
  );

  const renderFooter = () => (
    <div className="print-footer">
      <div className="footer-content">
        <Text type="secondary">
          报告生成时间: {new Date().toLocaleString()}
        </Text>
        <Text type="secondary">
          TradingAgents 智能分析系统
        </Text>
      </div>
    </div>
  );

  const getMetricName = (key: string) => {
    const names: Record<string, string> = {
      pe: '市盈率',
      pb: '市净率',
      roe: 'ROE',
      roa: 'ROA',
      revenue: '营收',
      profit: '净利润',
      eps: '每股收益',
      bvps: '每股净资产',
      currentRatio: '流动比率',
      debtRatio: '资产负债率',
      grossMargin: '毛利率',
      netMargin: '净利率',
    };
    return names[key] || key;
  };

  return (
    <div className="printable-report">
      {renderHeader()}
      {renderExecutiveSummary()}
      {renderBasicInfo()}
      {renderAnalysisDetails()}
      {renderRiskDisclaimer()}
      {renderFooter()}
    </div>
  );
};

export default PrintableReport;