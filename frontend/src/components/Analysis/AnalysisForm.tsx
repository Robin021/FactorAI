import React from 'react';
import { 
  Card, 
  Form, 
  Input, 
  Select, 
  DatePicker, 
  Slider, 
  Checkbox, 
  Button, 
  Row, 
  Col, 
  Typography,
  Alert,
  Space,
  Tooltip
} from 'antd';
import { 
  StockOutlined, 
  CalendarOutlined, 
  SearchOutlined,
  TeamOutlined,
  SettingOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { useAnalysis } from '@/hooks/useAnalysis';
import { AnalysisRequest } from '@/types';
import dayjs from 'dayjs';
import './AnalysisForm.css';

const { Title, Text } = Typography;
const { Option } = Select;

interface AnalysisFormData {
  stockCode: string;
  marketType: string;
  analysisDate: dayjs.Dayjs;
  researchDepth: number;
}

type AnalysisFormProps = {
  onStarted?: () => void;
};

const AnalysisForm: React.FC<AnalysisFormProps> = ({ onStarted }) => {
  const [form] = Form.useForm<AnalysisFormData>();
  const { startAnalysis, isLoading } = useAnalysis();
  const [selectedMarket, setSelectedMarket] = React.useState<string>('A股');

  // Market type options
  const marketOptions = [
    { value: 'A股', label: '🇨🇳 A股市场', description: '中国A股市场' },
    { value: '美股', label: '🇺🇸 美股市场', description: '美国股票市场' },
    { value: '港股', label: '🇭🇰 港股市场', description: '香港股票市场' },
  ];

  // Analyst team - 固定的分析师团队，不再让用户选择
  const analystTeam = [
    {
      value: 'market',
      label: '市场分析师',
      icon: '📈',
      description: '技术面分析、价格趋势、技术指标',
    },
    {
      value: 'news',
      label: '新闻分析师',
      icon: '📰',
      description: '新闻事件分析、市场动态影响',
    },
    {
      value: 'fundamentals',
      label: '基本面分析师',
      icon: '💰',
      description: '财务数据、公司基本面、估值水平',
    },
    {
      value: 'market_sentiment',
      label: '市场情绪分析师',
      icon: '📊',
      description: '多维度情绪评估、综合情绪评分',
    },
  ];

  // Research depth options
  const researchDepthMarks = {
    1: '快速',
    2: '基础',
    3: '标准',
    4: '深度',
    5: '全面',
  };

  const handleMarketChange = (value: string) => {
    setSelectedMarket(value);
    
    // Clear stock code when market changes
    form.setFieldValue('stockCode', '');
  };

  const getStockCodePlaceholder = (market: string) => {
    switch (market) {
      case 'A股':
        return '输入A股代码，如 000001, 600519';
      case '美股':
        return '输入美股代码，如 AAPL, TSLA, MSFT';
      case '港股':
        return '输入港股代码，如 0700.HK, 9988.HK';
      default:
        return '输入股票代码';
    }
  };

  const validateStockCode = (market: string, code: string) => {
    if (!code) return false;
    
    switch (market) {
      case 'A股':
        return /^[0-9]{6}$/.test(code);
      case '美股':
        return /^[A-Z]{1,5}$/.test(code.toUpperCase());
      case '港股':
        // 支持多种港股格式：00981, 0981, 0981.HK, 00981.HK
        return /^[0-9]{4,5}(\.HK)?$/i.test(code);
      default:
        return false;
    }
  };

  const handleSubmit = async (values: AnalysisFormData) => {
    try {
      // 使用固定的分析师团队，不再从表单获取
      const analysisRequest: AnalysisRequest = {
        symbol: values.stockCode.toUpperCase(),
        market_type: values.marketType === 'A股' ? 'CN' : values.marketType === '美股' ? 'US' : 'HK',
        analysis_type: 'comprehensive',
        analysts: ['market', 'news', 'fundamentals', 'market_sentiment'], // 固定的分析师团队
        research_depth: values.researchDepth,
      };

      await startAnalysis(analysisRequest);
      // 自动回调：开始分析后触发（用于切换到“实时进度”或关闭抽屉）
      onStarted?.();
    } catch (error) {
      console.error('Failed to start analysis:', error);
    }
  };

  return (
    <Card className="analysis-form-card analysis-form-container">
      <div className="form-header">
        <Title level={4}>
          <SettingOutlined /> 分析配置
        </Title>
        <Text type="secondary">配置股票分析参数</Text>
      </div>

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          marketType: 'A股',
          analysisDate: dayjs(),
          researchDepth: 3,
        }}
        className="analysis-form"
      >
        <Row gutter={16}>
          <Col xs={24} sm={24} md={12}>
            <Form.Item
              name="marketType"
              label={
                <Space>
                  <StockOutlined />
                  选择市场
                </Space>
              }
              rules={[{ required: true, message: '请选择市场类型' }]}
            >
              <Select
                placeholder="选择要分析的股票市场"
                onChange={handleMarketChange}
                size="large"
              >
                {marketOptions.map((option) => (
                  <Option key={option.value} value={option.value}>
                    {option.label}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Col>

          <Col xs={24} sm={24} md={12}>
            <Form.Item
              name="stockCode"
              label={
                <Space>
                  <SearchOutlined />
                  股票代码
                </Space>
              }
              rules={[
                { required: true, message: '请输入股票代码' },
                {
                  validator: (_, value) => {
                    if (!value) return Promise.resolve();
                    
                    const market = form.getFieldValue('marketType');
                    if (validateStockCode(market, value)) {
                      return Promise.resolve();
                    }
                    
                    return Promise.reject(new Error('股票代码格式不正确'));
                  },
                },
              ]}
            >
              <Input
                placeholder={getStockCodePlaceholder(selectedMarket)}
                size="large"
                style={{ textTransform: 'uppercase' }}
              />
            </Form.Item>
          </Col>

          <Col span={24}>
            <Form.Item
              name="analysisDate"
              label={
                <Space>
                  <CalendarOutlined />
                  分析日期
                </Space>
              }
              rules={[{ required: true, message: '请选择分析日期' }]}
            >
              <DatePicker
                size="large"
                style={{ width: '100%' }}
                disabledDate={(current) => current && current > dayjs().endOf('day')}
              />
            </Form.Item>
          </Col>

          <Col span={24}>
            <Form.Item
              name="researchDepth"
              label={
                <Space>
                  <InfoCircleOutlined />
                  研究深度
                  <Tooltip title="级别越高分析越详细但耗时更长">
                    <InfoCircleOutlined style={{ color: 'var(--info-color)' }} />
                  </Tooltip>
                </Space>
              }
            >
              <Slider
                marks={researchDepthMarks}
                min={1}
                max={5}
                step={1}
                tooltip={{ formatter: (value) => `${value}级 - ${researchDepthMarks[value as keyof typeof researchDepthMarks]}` }}
              />
            </Form.Item>
          </Col>

          <Col span={24}>
            <div className="analyst-team-display">
              <div className="analyst-team-header">
                <Space>
                  <TeamOutlined />
                  <Text strong>分析师团队</Text>
                </Space>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  系统将自动调用以下专业分析师团队进行全面分析
                </Text>
              </div>
              <Row gutter={[16, 16]} style={{ marginTop: 12 }}>
                {analystTeam.map((analyst) => (
                  <Col span={12} key={analyst.value}>
                    <Card 
                      size="small" 
                      className="analyst-card"
                      style={{ 
                        background: 'var(--card-bg)',
                        border: '1px solid var(--border-color)',
                      }}
                    >
                      <Space direction="vertical" size={4} style={{ width: '100%' }}>
                        <Text strong style={{ fontSize: '14px' }}>
                          {analyst.icon} {analyst.label}
                        </Text>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          {analyst.description}
                        </Text>
                      </Space>
                    </Card>
                  </Col>
                ))}
              </Row>
            </div>
          </Col>

          <Col span={24}>
            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={isLoading}
                size="large"
                block
                icon={<SearchOutlined />}
              >
                {isLoading ? '分析中...' : '开始分析'}
              </Button>
            </Form.Item>
          </Col>
        </Row>
      </Form>
    </Card>
  );
};

export default AnalysisForm;
