import React from 'react';
import { Row, Col, Typography, Tabs, Card, Tag } from 'antd';
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
  const { currentAnalysis, analysisHistory } = useAnalysis();
  const [activeTab, setActiveTab] = React.useState('analysis');

  // Auto-switch to progress tab when analysis starts
  React.useEffect(() => {
    if (
      currentAnalysis &&
      (currentAnalysis.status === 'running' || currentAnalysis.status === 'pending')
    ) {
      setActiveTab('progress');
    }
  }, [currentAnalysis]);

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
      <Title level={4}>分析历史</Title>
      {analysisHistory.length === 0 ? (
        <div className="no-history-message">
          <p>暂无历史分析记录</p>
        </div>
      ) : (
        <div className="history-list">
          {analysisHistory.map(analysis => (
            <AnalysisResults key={analysis.id} analysis={analysis} />
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
