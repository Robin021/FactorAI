import React from 'react';
import { Row, Col, Typography, Tabs, Card, Tag, Button, Spin, Empty, Space, Modal, message, Checkbox } from 'antd';
import { BarChartOutlined, SettingOutlined, HistoryOutlined, ExclamationCircleOutlined, DeleteOutlined } from '@ant-design/icons';
import AnalysisForm from '@/components/Analysis/AnalysisForm';
import SevenStepProgress from '@/components/Analysis/SevenStepProgress';
import AnalysisResults from '@/components/Analysis/AnalysisResults';
import { useAnalysis } from '@/hooks/useAnalysis';
import { analysisService } from '@/services/analysis';
import './Analysis.css';
import '@/styles/themes.css';
import '@/styles/theme-override.css';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

const Analysis: React.FC = () => {
  const { currentAnalysis, analysisHistory, refreshHistory, setCurrentAnalysis, historyLoading } =
    useAnalysis();
  const [activeTab, setActiveTab] = React.useState('analysis');
  const [selectedAnalyses, setSelectedAnalyses] = React.useState<string[]>([]);

  // 删除分析记录
  const handleDeleteAnalysis = (analysisId: string) => {
    const analysisItem = analysisHistory.find(item => item.id === analysisId);
    
    if (!analysisItem) {
      message.error('找不到要删除的分析记录');
      return;
    }

    // 检查是否为运行中的分析
    if (analysisItem.status === 'running' || analysisItem.status === 'pending') {
      message.warning('无法删除运行中的分析，请先取消分析');
      return;
    }
    
    Modal.confirm({
      title: '确认删除分析记录',
      icon: <ExclamationCircleOutlined />,
      content: (
        <div>
          <p>确定要删除以下分析记录吗？</p>
          <div style={{ padding: '8px 0', background: '#f5f5f5', borderRadius: '4px', margin: '8px 0' }}>
            <p><strong>股票代码：</strong>{analysisItem.stockCode}</p>
            <p><strong>状态：</strong>{analysisItem.status}</p>
            <p><strong>创建时间：</strong>{analysisItem.createdAt ? new Date(analysisItem.createdAt).toLocaleString() : '-'}</p>
          </div>
          <p style={{ color: '#ff4d4f' }}>⚠️ 此操作不可撤销，分析结果将永久丢失。</p>
        </div>
      ),
      okText: '确认删除',
      okType: 'danger',
      cancelText: '取消',
      width: 480,
      onOk: async () => {
        try {
          await analysisService.deleteAnalysis(analysisId);
          message.success('分析记录已删除');
          
          // 如果删除的是当前正在查看的分析，清除当前分析
          if (currentAnalysis?.id === analysisId) {
            setCurrentAnalysis(null);
          }
          
          // 刷新历史记录
          refreshHistory();
        } catch (error: any) {
          console.error('删除分析记录失败:', error);
          message.error(error.message || '删除失败，请重试');
        }
      },
    });
  };

  // 批量删除分析记录
  const handleBatchDelete = () => {
    if (selectedAnalyses.length === 0) {
      message.warning('请选择要删除的分析记录');
      return;
    }

    const selectedItems = analysisHistory.filter(item => selectedAnalyses.includes(item.id));
    const runningItems = selectedItems.filter(item => item.status === 'running' || item.status === 'pending');
    
    if (runningItems.length > 0) {
      message.warning(`无法删除 ${runningItems.length} 个运行中的分析，请先取消这些分析`);
      return;
    }

    Modal.confirm({
      title: `确认批量删除 ${selectedAnalyses.length} 个分析记录`,
      icon: <ExclamationCircleOutlined />,
      content: (
        <div>
          <p>确定要删除以下 {selectedAnalyses.length} 个分析记录吗？</p>
          <div style={{ maxHeight: '200px', overflow: 'auto', padding: '8px', background: '#f5f5f5', borderRadius: '4px', margin: '8px 0' }}>
            {selectedItems.map(item => (
              <p key={item.id} style={{ margin: '4px 0' }}>
                • {item.stockCode} ({item.status}) - {item.createdAt ? new Date(item.createdAt).toLocaleString() : '-'}
              </p>
            ))}
          </div>
          <p style={{ color: '#ff4d4f' }}>⚠️ 此操作不可撤销，所有分析结果将永久丢失。</p>
        </div>
      ),
      okText: '确认删除',
      okType: 'danger',
      cancelText: '取消',
      width: 600,
      onOk: async () => {
        try {
          // 并行删除所有选中的分析
          await Promise.all(selectedAnalyses.map(id => analysisService.deleteAnalysis(id)));
          
          message.success(`已删除 ${selectedAnalyses.length} 个分析记录`);
          
          // 如果删除的包含当前正在查看的分析，清除当前分析
          if (currentAnalysis && selectedAnalyses.includes(currentAnalysis.id)) {
            setCurrentAnalysis(null);
          }
          
          // 清空选择
          setSelectedAnalyses([]);
          
          // 刷新历史记录
          refreshHistory();
        } catch (error: any) {
          console.error('批量删除分析记录失败:', error);
          message.error(error.message || '批量删除失败，请重试');
        }
      },
    });
  };

  // 处理单个选择
  const handleSelectAnalysis = (analysisId: string, checked: boolean) => {
    if (checked) {
      setSelectedAnalyses(prev => [...prev, analysisId]);
    } else {
      setSelectedAnalyses(prev => prev.filter(id => id !== analysisId));
    }
  };

  // 处理全选
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      // 只选择非运行中的分析
      const selectableIds = analysisHistory
        .filter(item => item.status !== 'running' && item.status !== 'pending')
        .map(item => item.id);
      setSelectedAnalyses(selectableIds);
    } else {
      setSelectedAnalyses([]);
    }
  };

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
      if (activeTab === 'progress') {
        // 从进度页面完成后，跳转到专门的报告页面
        console.log('🎯 分析完成，跳转到报告页面:', currentAnalysis.id);
        window.location.href = `/analysis/report/${currentAnalysis.id}`;
      }
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
      <SevenStepProgress
        analysisId={currentAnalysis.id}
        onComplete={(success) => {
          console.log('Analysis completed:', success);
          setActiveTab('analysis');
        }}
        onCancel={() => {
          setActiveTab('analysis');
        }}
        showCancelButton={true}
      />
    );
  };

  const renderHistoryContent = () => (
    <div className="analysis-history">
      <Space style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
        <Title level={4} style={{ margin: 0 }}>
          分析历史 ({analysisHistory.length})
        </Title>
        <Space>
          {analysisHistory.length > 0 && (
            <>
              <Checkbox
                indeterminate={selectedAnalyses.length > 0 && selectedAnalyses.length < analysisHistory.filter(item => item.status !== 'running' && item.status !== 'pending').length}
                checked={selectedAnalyses.length > 0 && selectedAnalyses.length === analysisHistory.filter(item => item.status !== 'running' && item.status !== 'pending').length}
                onChange={(e) => handleSelectAll(e.target.checked)}
              >
                全选
              </Checkbox>
              {selectedAnalyses.length > 0 && (
                <Button
                  size="small"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={handleBatchDelete}
                >
                  删除选中 ({selectedAnalyses.length})
                </Button>
              )}
            </>
          )}
          <Button size="small" onClick={() => refreshHistory()}>
            刷新
          </Button>
        </Space>
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
                <Col flex="none" style={{ marginRight: 12 }}>
                  <Checkbox
                    checked={selectedAnalyses.includes(item.id)}
                    disabled={item.status === 'running' || item.status === 'pending'}
                    onChange={(e) => handleSelectAnalysis(item.id, e.target.checked)}
                  />
                </Col>
                <Col flex="auto">
                  <Space direction="vertical" size={2}>
                    <Space>
                      <Text strong>{item.stockCode}</Text>
                      <Tag color={
                        item.status === 'completed' ? 'green' :
                        item.status === 'running' ? 'blue' :
                        item.status === 'pending' ? 'orange' :
                        item.status === 'failed' ? 'red' : 'default'
                      }>
                        {item.status === 'completed' ? '已完成' :
                         item.status === 'running' ? '运行中' :
                         item.status === 'pending' ? '等待中' :
                         item.status === 'failed' ? '失败' :
                         item.status === 'cancelled' ? '已取消' : item.status}
                      </Tag>
                    </Space>
                    <Text type="secondary">
                      进度：{Math.round(item.progress)}%
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
                    <Button
                      type="link"
                      danger
                      onClick={() => handleDeleteAnalysis(item.id)}
                      disabled={item.status === 'running' || item.status === 'pending'}
                    >
                      删除
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
