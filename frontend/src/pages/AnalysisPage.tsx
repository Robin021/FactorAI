/**
 * 分析页面示例
 */

import React, { useState } from 'react';
import { Card, Form, Input, Select, Button, Space, message, Row, Col } from 'antd';
import SimpleAnalysisProgress from '../components/SimpleAnalysisProgress';

const { Option } = Select;

interface AnalysisRequest {
  stock_symbol: string;
  market_type: string;
  analysis_date: string;
  analysts: string[];
  research_depth: number;
  llm_provider: string;
  llm_model: string;
}

const AnalysisPage: React.FC = () => {
  const [form] = Form.useForm();
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [isStarting, setIsStarting] = useState(false);

  // 启动分析
  const handleStartAnalysis = async (values: AnalysisRequest) => {
    setIsStarting(true);
    try {
      const response = await fetch('/api/analysis/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...values,
          analysis_date: new Date().toISOString().split('T')[0], // 今天的日期
        }),
      });

      if (response.ok) {
        const result = await response.json();
        setAnalysisId(result.analysis_id);
        message.success('分析已启动！');
      } else {
        const error = await response.json();
        message.error(error.detail || '启动分析失败');
      }
    } catch (err) {
      console.error('Failed to start analysis:', err);
      message.error('网络请求失败');
    } finally {
      setIsStarting(false);
    }
  };

  // 分析完成回调
  const handleAnalysisComplete = (success: boolean) => {
    if (success) {
      message.success('分析完成！');
    } else {
      message.error('分析失败！');
    }
  };

  // 取消分析回调
  const handleAnalysisCancel = () => {
    message.info('分析已取消');
    setAnalysisId(null);
  };

  // 重新开始分析
  const handleRestart = () => {
    setAnalysisId(null);
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <Row gutter={24}>
        {/* 左侧：分析配置表单 */}
        <Col span={analysisId ? 12 : 24}>
          <Card title="📋 股票分析配置" style={{ marginBottom: 24 }}>
            <Form
              form={form}
              layout="vertical"
              onFinish={handleStartAnalysis}
              initialValues={{
                market_type: 'A股',
                analysts: ['market', 'fundamentals'],
                research_depth: 2,
                llm_provider: 'dashscope',
                llm_model: 'qwen-plus'
              }}
            >
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="stock_symbol"
                    label="股票代码"
                    rules={[{ required: true, message: '请输入股票代码' }]}
                  >
                    <Input placeholder="如：000001, AAPL" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="market_type"
                    label="市场类型"
                    rules={[{ required: true }]}
                  >
                    <Select>
                      <Option value="A股">A股</Option>
                      <Option value="美股">美股</Option>
                      <Option value="港股">港股</Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                name="analysts"
                label="分析师团队"
                rules={[{ required: true, message: '请选择至少一个分析师' }]}
              >
                <Select mode="multiple" placeholder="选择分析师">
                  <Option value="market">市场分析师</Option>
                  <Option value="fundamentals">基本面分析师</Option>
                  <Option value="technical">技术分析师</Option>
                  <Option value="sentiment">情绪分析师</Option>
                  <Option value="news">新闻分析师</Option>
                </Select>
              </Form.Item>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="research_depth"
                    label="研究深度"
                    rules={[{ required: true }]}
                  >
                    <Select>
                      <Option value={1}>1级 - 快速分析</Option>
                      <Option value={2}>2级 - 基础分析</Option>
                      <Option value={3}>3级 - 标准分析</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="llm_provider"
                    label="AI模型提供商"
                    rules={[{ required: true }]}
                  >
                    <Select>
                      <Option value="dashscope">阿里百炼</Option>
                      <Option value="deepseek">DeepSeek</Option>
                      <Option value="google">Google AI</Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item>
                <Space>
                  <Button 
                    type="primary" 
                    htmlType="submit" 
                    loading={isStarting}
                    disabled={!!analysisId}
                  >
                    🚀 开始分析
                  </Button>
                  {analysisId && (
                    <Button onClick={handleRestart}>
                      重新开始
                    </Button>
                  )}
                </Space>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        {/* 右侧：进度显示 */}
        {analysisId && (
          <Col span={12}>
            <SimpleAnalysisProgress
              analysisId={analysisId}
              onComplete={handleAnalysisComplete}
              onCancel={handleAnalysisCancel}
              showCancelButton={true}
            />
          </Col>
        )}
      </Row>
    </div>
  );
};

export default AnalysisPage;