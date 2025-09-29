import React, { useState, useEffect } from 'react';
import {
    List,
    Card,
    Tag,
    Button,
    Space,
    Typography,
    Progress,
    Empty,
    Spin,
    message,
    Modal
} from 'antd';
import {
    ClockCircleOutlined,
    CheckCircleOutlined,
    ExclamationCircleOutlined,
    EyeOutlined,
    ReloadOutlined
} from '@ant-design/icons';
import { analysisHistoryService, AnalysisHistoryItem } from '@/services/analysisHistory';
import AnalysisProgress from './AnalysisProgress';

const { Title, Text } = Typography;

interface AnalysisHistoryProps {
    onSelectAnalysis?: (analysisId: string) => void;
}

const AnalysisHistory: React.FC<AnalysisHistoryProps> = ({ onSelectAnalysis }) => {
    const [analyses, setAnalyses] = useState<AnalysisHistoryItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedAnalysis, setSelectedAnalysis] = useState<any>(null);
    const [progressModalVisible, setProgressModalVisible] = useState(false);

    const loadAnalysisHistory = async () => {
        try {
            setLoading(true);
            console.log('🔄 Loading analysis history...');
            const response = await analysisHistoryService.getAnalysisHistory();
            console.log('📥 Analysis history response:', response);
            console.log('📊 Number of analyses:', response.analyses?.length || 0);
            setAnalyses(response.analyses || []);
        } catch (error) {
            message.error('加载分析历史失败');
            console.error('❌ Load analysis history error:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadAnalysisHistory();
    }, []);

    const getStatusTag = (status: string) => {
        switch (status) {
            case 'running':
                return <Tag icon={<ClockCircleOutlined />} color="processing">分析中</Tag>;
            case 'completed':
                return <Tag icon={<CheckCircleOutlined />} color="success">已完成</Tag>;
            case 'failed':
                return <Tag icon={<ExclamationCircleOutlined />} color="error">失败</Tag>;
            default:
                return <Tag color="default">{status}</Tag>;
        }
    };

    const formatElapsedTime = (seconds: number) => {
        if (seconds < 60) {
            return `${Math.round(seconds)}秒`;
        } else if (seconds < 3600) {
            return `${Math.round(seconds / 60)}分钟`;
        } else {
            return `${Math.round(seconds / 3600)}小时`;
        }
    };

    const handleViewProgress = async (item: AnalysisHistoryItem) => {
        try {
            const progressData = await analysisHistoryService.getAnalysisProgress(item.analysis_id);
            setSelectedAnalysis({
                id: item.analysis_id,  // 确保使用正确的 analysis_id
                stockCode: item.symbol,
                userId: 'current_user',
                status: progressData.status || 'running',
                progress: progressData.progress_percentage || 0,
                createdAt: new Date().toISOString(),
                marketType: 'CN',
                analysisType: 'comprehensive',
                resultData: progressData.results || null
            });
            setProgressModalVisible(true);
        } catch (error) {
            message.error('获取分析进度失败');
            console.error('Get analysis progress error:', error);
        }
    };

    const handleViewResults = async (item: AnalysisHistoryItem) => {
        try {
            await analysisHistoryService.getAnalysisResults(item.analysis_id);
            // 这里可以跳转到结果页面或显示结果模态框
            onSelectAnalysis?.(item.analysis_id);
            message.success('跳转到分析结果页面');
        } catch (error) {
            message.error('获取分析结果失败');
            console.error('Get analysis results error:', error);
        }
    };

    if (loading) {
        return (
            <div style={{ textAlign: 'center', padding: '50px' }}>
                <Spin size="large" />
                <div style={{ marginTop: 16 }}>加载分析历史...</div>
            </div>
        );
    }

    return (
        <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <Title level={4}>分析历史</Title>
                <Button
                    icon={<ReloadOutlined />}
                    onClick={loadAnalysisHistory}
                    loading={loading}
                >
                    刷新
                </Button>
            </div>

            {analyses.length === 0 ? (
                <Empty
                    description="暂无分析记录"
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
            ) : (
                <List
                    dataSource={analyses}
                    renderItem={(item) => (
                        <List.Item key={item.analysis_id}>
                            <Card
                                style={{ width: '100%' }}
                                size="small"
                                actions={[
                                    <Button
                                        key="progress"
                                        type="link"
                                        icon={<EyeOutlined />}
                                        onClick={() => handleViewProgress(item)}
                                    >
                                        查看进度
                                    </Button>,
                                    ...(item.status === 'completed' ? [
                                        <Button
                                            key="results"
                                            type="link"
                                            icon={<CheckCircleOutlined />}
                                            onClick={() => handleViewResults(item)}
                                        >
                                            查看结果
                                        </Button>
                                    ] : [])
                                ]}
                            >
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                    <div style={{ flex: 1 }}>
                                        <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                                <Text strong style={{ fontSize: 16 }}>{item.symbol}</Text>
                                                {getStatusTag(item.status)}
                                            </div>

                                            <Text type="secondary" style={{ fontSize: 12 }}>
                                                分析ID: {item.analysis_id.slice(0, 8)}...
                                            </Text>

                                            {item.status === 'running' && (
                                                <div>
                                                    <Progress
                                                        percent={item.progress_percentage}
                                                        size="small"
                                                        status="active"
                                                    />
                                                    <Text type="secondary" style={{ fontSize: 12 }}>
                                                        {item.current_step_name}
                                                    </Text>
                                                </div>
                                            )}

                                            <div style={{ display: 'flex', gap: 16 }}>
                                                <Text type="secondary" style={{ fontSize: 12 }}>
                                                    创建时间: {new Date(item.created_at).toLocaleString()}
                                                </Text>
                                                {item.elapsed_time > 0 && (
                                                    <Text type="secondary" style={{ fontSize: 12 }}>
                                                        耗时: {formatElapsedTime(item.elapsed_time)}
                                                    </Text>
                                                )}
                                            </div>
                                        </Space>
                                    </div>
                                </div>
                            </Card>
                        </List.Item>
                    )}
                />
            )}

            <Modal
                title={`分析进度 - ${selectedAnalysis?.stockCode}`}
                open={progressModalVisible}
                onCancel={() => setProgressModalVisible(false)}
                footer={null}
                width={800}
            >
                {selectedAnalysis && (
                    <AnalysisProgress analysis={selectedAnalysis} />
                )}
            </Modal>
        </div>
    );
};

export default AnalysisHistory;