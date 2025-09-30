import React from 'react';
import { Row, Col, Typography, Tabs, Card, Tag, Button, Spin, Empty, Space } from 'antd';
import { BarChartOutlined, SettingOutlined, HistoryOutlined } from '@ant-design/icons';
import AnalysisForm from '@/components/Analysis/AnalysisForm';
import RealTimeProgressDashboard from '@/components/Analysis/RealTimeProgressDashboard';
import AnalysisResults from '@/components/Analysis/AnalysisResults';
import { useAnalysis } from '@/hooks/useAnalysis';
import './Analysis.css';
import '@/styles/themes.css';
import '@/styles/theme-override.css';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

const Analysis: React.FC = () => {
  const { currentAnalysis, analysisHistory, refreshHistory, setCurrentAnalysis, historyLoading } =
    useAnalysis();
  const [activeTab, setActiveTab] = React.useState('analysis');

  // Auto-switch behavior
  React.useEffect(() => {
    console.log('🔄 [Analysis] currentAnalysis changed:', {
      id: currentAnalysis?.id,
      status: currentAnalysis?.status,
      progress: currentAnalysis?.progress,
      currentTab: activeTab,
    });

    if (!currentAnalysis) return;

    // 运行中 -> 自动切到 实时进度（但不要打断用户正在看历史记录）
    if (currentAnalysis.status === 'running' || currentAnalysis.status === 'pending') {
      if (activeTab !== 'history' && activeTab !== 'progress') setActiveTab('progress');
      return;
    }

    // 已完成 -> 仅当从进度页完成后自动回到“分析与结果”，不打断用户看“历史记录”
    if (currentAnalysis.status === 'completed') {
      if (activeTab === 'progress') setActiveTab('analysis');
    }
  }, [currentAnalysis, activeTab]);

  const renderAnalysisContent = () => (
    <Row gutter={[24, 24]} style={{ margin: 0 }}>
      <Col xs={24} sm={24} md={10} lg={8} xl={8}>
        <AnalysisForm />
      </Col>

      <Col xs={24} sm={24} md={14} lg={16} xl={16}>
        <AnalysisResults analysis={currentAnalysis} />
      </Col>
    </Row>
  );

  const renderProgressContent = () => {
    if (!currentAnalysis) {
      return (
        <div className="no-progress-message">
          <Title level={4} type="secondary">
            暂无分析任务
          </Title>
          <p>请先在分析页面开始一个新的分析任务</p>
        </div>
      );
    }

    return (
      <RealTimeProgressDashboard
        analysis={currentAnalysis}
        onComplete={() => {
          setActiveTab('analysis');
        }}
        onError={error => {
          console.error('Analysis error:', error);
          setActiveTab('analysis');
        }}
        onCancel={() => {
          setActiveTab('analysis');
        }}
      />
    );
  };

  const renderHistoryContent = () => (
    <div className="analysis-history">
      <Space style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
        <Title level={4} style={{ margin: 0 }}>
          分析历史
        </Title>
        <Button size="small" onClick={() => refreshHistory()}>
          刷新
        </Button>
      </Space>
      {historyLoading ? (
        <div style={{ padding: 24, textAlign: 'center' }}>
          <Spin tip="加载历史记录中..." />
        </div>
      ) : analysisHistory.length === 0 ? (
        <Empty description="暂无历史分析记录" />
      ) : (
        <div className="history-list">
          {analysisHistory.map(item => (
            <Card key={item.id} style={{ marginBottom: 12 }} hoverable>
              <Row align="middle" justify="space-between">
                <Col flex="auto">
                  <Space direction="vertical" size={2}>
                    <Text strong>{item.stockCode}</Text>
                    <Text type="secondary">
                      状态：{item.status}，进度：{Math.round(item.progress)}%
                    </Text>
                    <Text type="secondary">
                      创建时间：{item.createdAt ? new Date(item.createdAt).toLocaleString() : '-'}
                    </Text>
                  </Space>
                </Col>
                <Col>
                  <Space>
                    <Button
                      type="link"
                      onClick={() => {
                        setCurrentAnalysis(item);
                        setActiveTab('analysis');
                      }}
                    >
                      查看报告
                    </Button>
                  </Space>
                </Col>
              </Row>
            </Card>
          ))}
        </div>
      )}
    </div>
  );

  return (
    <div className="analysis-page">
      <Tabs activeKey={activeTab} onChange={setActiveTab} className="analysis-tabs" size="large">
        <TabPane
          tab={
            <span>
              <BarChartOutlined />
              分析与结果
            </span>
          }
          key="analysis"
        >
          {renderAnalysisContent()}
        </TabPane>

        <TabPane
          tab={
            <span>
              <SettingOutlined />
              实时进度
              {currentAnalysis &&
                (currentAnalysis.status === 'running' || currentAnalysis.status === 'pending') && (
                  <span className="progress-indicator" />
                )}
            </span>
          }
          key="progress"
        >
          {renderProgressContent()}
        </TabPane>

        <TabPane
          tab={
            <span>
              <HistoryOutlined />
              历史记录
            </span>
          }
          key="history"
        >
          {renderHistoryContent()}
        </TabPane>
      </Tabs>
    </div>
  );
};

export default Analysis;
