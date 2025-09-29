import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Select,
  InputNumber,
  Switch,
  Button,
  Space,
  Alert,
  Divider,
  Typography,
  Tooltip,
  Modal,
  message,
  Spin,
  Row,
  Col,
} from 'antd';
import {
  SaveOutlined,
  TestConnectionOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  EyeInvisibleOutlined,
  EyeTwoTone,
} from '@ant-design/icons';
import { useConfigStore } from '@/stores/configStore';
import { LLMConfig as LLMConfigType, LLMProvider } from '@/services/config';
import './LLMConfig.css';

const { Title, Text } = Typography;
const { Option } = Select;
const { Password } = Input;

interface LLMProviderInfo {
  name: string;
  description: string;
  defaultModel: string;
  models: string[];
  apiKeyLabel: string;
  apiKeyPlaceholder: string;
  baseUrlRequired: boolean;
  baseUrlPlaceholder?: string;
  documentationUrl: string;
}

const LLM_PROVIDERS: Record<LLMProvider, LLMProviderInfo> = {
  [LLMProvider.OPENAI]: {
    name: 'OpenAI',
    description: 'OpenAI GPT models including GPT-3.5 and GPT-4',
    defaultModel: 'gpt-3.5-turbo',
    models: ['gpt-3.5-turbo', 'gpt-3.5-turbo-16k', 'gpt-4', 'gpt-4-turbo', 'gpt-4o'],
    apiKeyLabel: 'API Key',
    apiKeyPlaceholder: 'sk-...',
    baseUrlRequired: false,
    baseUrlPlaceholder: 'https://api.openai.com/v1',
    documentationUrl: 'https://platform.openai.com/docs',
  },
  [LLMProvider.DASHSCOPE]: {
    name: 'DashScope (阿里云)',
    description: '阿里云通义千问大语言模型服务',
    defaultModel: 'qwen-turbo',
    models: ['qwen-turbo', 'qwen-plus', 'qwen-max', 'qwen-max-longcontext'],
    apiKeyLabel: 'API Key',
    apiKeyPlaceholder: 'sk-...',
    baseUrlRequired: false,
    documentationUrl: 'https://help.aliyun.com/zh/dashscope/',
  },
  [LLMProvider.DEEPSEEK]: {
    name: 'DeepSeek',
    description: 'DeepSeek AI language models',
    defaultModel: 'deepseek-chat',
    models: ['deepseek-chat', 'deepseek-coder'],
    apiKeyLabel: 'API Key',
    apiKeyPlaceholder: 'sk-...',
    baseUrlRequired: true,
    baseUrlPlaceholder: 'https://api.deepseek.com',
    documentationUrl: 'https://platform.deepseek.com/api-docs/',
  },
  [LLMProvider.GEMINI]: {
    name: 'Google Gemini',
    description: 'Google Gemini AI models',
    defaultModel: 'gemini-pro',
    models: ['gemini-pro', 'gemini-pro-vision', 'gemini-1.5-pro'],
    apiKeyLabel: 'API Key',
    apiKeyPlaceholder: 'AIza...',
    baseUrlRequired: false,
    documentationUrl: 'https://ai.google.dev/docs',
  },
  [LLMProvider.QIANFAN]: {
    name: '百度千帆',
    description: '百度千帆大模型平台',
    defaultModel: 'ERNIE-Bot-turbo',
    models: ['ERNIE-Bot', 'ERNIE-Bot-turbo', 'ERNIE-Bot-4', 'ChatGLM2-6B-32K'],
    apiKeyLabel: 'API Key',
    apiKeyPlaceholder: 'your-api-key',
    baseUrlRequired: false,
    documentationUrl: 'https://cloud.baidu.com/doc/WENXINWORKSHOP/',
  },
};

const LLMConfig: React.FC = () => {
  const [form] = Form.useForm();
  const [testModalVisible, setTestModalVisible] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<LLMProvider>(LLMProvider.OPENAI);
  
  const {
    llmConfig,
    isLoading,
    error,
    testResults,
    loadLLMConfig,
    updateLLMConfig,
    testLLMConnection,
    clearError,
    clearTestResults,
  } = useConfigStore();

  useEffect(() => {
    loadLLMConfig();
  }, [loadLLMConfig]);

  useEffect(() => {
    if (llmConfig) {
      form.setFieldsValue(llmConfig);
      setSelectedProvider(llmConfig.provider);
    }
  }, [llmConfig, form]);

  const handleProviderChange = (provider: LLMProvider) => {
    setSelectedProvider(provider);
    const providerInfo = LLM_PROVIDERS[provider];
    
    // Update form with default values for the selected provider
    form.setFieldsValue({
      provider,
      model_name: providerInfo.defaultModel,
      api_base: providerInfo.baseUrlRequired ? providerInfo.baseUrlPlaceholder : undefined,
    });
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      await updateLLMConfig(values);
      message.success('LLM 配置已保存');
    } catch (error: any) {
      if (error.errorFields) {
        message.error('请检查表单输入');
      } else {
        message.error(error.message || '保存失败');
      }
    }
  };

  const handleTest = async () => {
    try {
      const values = await form.validateFields();
      setIsTesting(true);
      clearTestResults();
      await testLLMConnection(values);
      setTestModalVisible(true);
    } catch (error: any) {
      if (error.errorFields) {
        message.error('请检查表单输入');
      } else {
        message.error(error.message || '测试失败');
      }
    } finally {
      setIsTesting(false);
    }
  };

  const handleReset = () => {
    Modal.confirm({
      title: '重置配置',
      content: '确定要重置为默认配置吗？这将清除当前所有设置。',
      onOk: () => {
        const providerInfo = LLM_PROVIDERS[selectedProvider];
        form.setFieldsValue({
          provider: selectedProvider,
          model_name: providerInfo.defaultModel,
          api_key: '',
          api_base: providerInfo.baseUrlRequired ? providerInfo.baseUrlPlaceholder : undefined,
          temperature: 0.7,
          max_tokens: undefined,
          timeout: 30,
          retry_attempts: 3,
          enabled: true,
        });
        message.success('配置已重置');
      },
    });
  };

  const providerInfo = LLM_PROVIDERS[selectedProvider];

  return (
    <div className="llm-config">
      <Card>
        <div className="llm-config-header">
          <Title level={3}>LLM 配置管理</Title>
          <Text type="secondary">
            配置大语言模型提供商和参数设置
          </Text>
        </div>

        {error && (
          <Alert
            message="配置错误"
            description={error}
            type="error"
            showIcon
            closable
            onClose={clearError}
            style={{ marginBottom: 16 }}
          />
        )}

        <Spin spinning={isLoading}>
          <Form
            form={form}
            layout="vertical"
            initialValues={{
              temperature: 0.7,
              timeout: 30,
              retry_attempts: 3,
              enabled: true,
            }}
          >
            <Row gutter={24}>
              <Col span={12}>
                <Form.Item
                  label="LLM 提供商"
                  name="provider"
                  rules={[{ required: true, message: '请选择 LLM 提供商' }]}
                >
                  <Select
                    placeholder="选择 LLM 提供商"
                    onChange={handleProviderChange}
                  >
                    {Object.entries(LLM_PROVIDERS).map(([key, info]) => (
                      <Option key={key} value={key}>
                        <Space>
                          <span>{info.name}</span>
                          <Text type="secondary" style={{ fontSize: '12px' }}>
                            {info.description}
                          </Text>
                        </Space>
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>

              <Col span={12}>
                <Form.Item
                  label="模型名称"
                  name="model_name"
                  rules={[{ required: true, message: '请选择模型' }]}
                >
                  <Select placeholder="选择模型">
                    {providerInfo.models.map((model) => (
                      <Option key={model} value={model}>
                        {model}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={24}>
              <Col span={12}>
                <Form.Item
                  label={
                    <Space>
                      {providerInfo.apiKeyLabel}
                      <Tooltip title="API 密钥将被安全存储，不会在界面中明文显示">
                        <InfoCircleOutlined />
                      </Tooltip>
                    </Space>
                  }
                  name="api_key"
                  rules={[{ required: true, message: `请输入 ${providerInfo.apiKeyLabel}` }]}
                >
                  <Password
                    placeholder={providerInfo.apiKeyPlaceholder}
                    iconRender={(visible) => (visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />)}
                  />
                </Form.Item>
              </Col>

              {providerInfo.baseUrlRequired && (
                <Col span={12}>
                  <Form.Item
                    label="API Base URL"
                    name="api_base"
                    rules={[{ required: true, message: '请输入 API Base URL' }]}
                  >
                    <Input placeholder={providerInfo.baseUrlPlaceholder} />
                  </Form.Item>
                </Col>
              )}
            </Row>

            <Divider>高级参数</Divider>

            <Row gutter={24}>
              <Col span={8}>
                <Form.Item
                  label={
                    <Space>
                      Temperature
                      <Tooltip title="控制输出的随机性，0-2之间，值越高输出越随机">
                        <InfoCircleOutlined />
                      </Tooltip>
                    </Space>
                  }
                  name="temperature"
                  rules={[
                    { required: true, message: '请输入 Temperature' },
                    { type: 'number', min: 0, max: 2, message: 'Temperature 必须在 0-2 之间' },
                  ]}
                >
                  <InputNumber
                    min={0}
                    max={2}
                    step={0.1}
                    style={{ width: '100%' }}
                    placeholder="0.7"
                  />
                </Form.Item>
              </Col>

              <Col span={8}>
                <Form.Item
                  label={
                    <Space>
                      最大 Token 数
                      <Tooltip title="限制单次响应的最大 token 数量，留空使用模型默认值">
                        <InfoCircleOutlined />
                      </Tooltip>
                    </Space>
                  }
                  name="max_tokens"
                >
                  <InputNumber
                    min={1}
                    style={{ width: '100%' }}
                    placeholder="留空使用默认值"
                  />
                </Form.Item>
              </Col>

              <Col span={8}>
                <Form.Item
                  label={
                    <Space>
                      超时时间 (秒)
                      <Tooltip title="API 请求的超时时间">
                        <InfoCircleOutlined />
                      </Tooltip>
                    </Space>
                  }
                  name="timeout"
                  rules={[
                    { required: true, message: '请输入超时时间' },
                    { type: 'number', min: 1, message: '超时时间必须大于 0' },
                  ]}
                >
                  <InputNumber
                    min={1}
                    style={{ width: '100%' }}
                    placeholder="30"
                  />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={24}>
              <Col span={8}>
                <Form.Item
                  label={
                    <Space>
                      重试次数
                      <Tooltip title="API 请求失败时的重试次数">
                        <InfoCircleOutlined />
                      </Tooltip>
                    </Space>
                  }
                  name="retry_attempts"
                  rules={[
                    { required: true, message: '请输入重试次数' },
                    { type: 'number', min: 1, max: 10, message: '重试次数必须在 1-10 之间' },
                  ]}
                >
                  <InputNumber
                    min={1}
                    max={10}
                    style={{ width: '100%' }}
                    placeholder="3"
                  />
                </Form.Item>
              </Col>

              <Col span={8}>
                <Form.Item
                  label="启用状态"
                  name="enabled"
                  valuePropName="checked"
                >
                  <Switch checkedChildren="启用" unCheckedChildren="禁用" />
                </Form.Item>
              </Col>
            </Row>
          </Form>
        </Spin>

        <Divider />

        <div className="llm-config-actions">
          <Space>
            <Button
              type="primary"
              icon={<SaveOutlined />}
              onClick={handleSave}
              loading={isLoading}
            >
              保存配置
            </Button>
            <Button
              icon={<TestConnectionOutlined />}
              onClick={handleTest}
              loading={isTesting}
            >
              测试连接
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={handleReset}
            >
              重置配置
            </Button>
          </Space>

          <Space>
            <Button
              type="link"
              href={providerInfo.documentationUrl}
              target="_blank"
              icon={<InfoCircleOutlined />}
            >
              查看文档
            </Button>
          </Space>
        </div>
      </Card>

      {/* Test Connection Modal */}
      <Modal
        title="连接测试结果"
        open={testModalVisible}
        onCancel={() => setTestModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setTestModalVisible(false)}>
            关闭
          </Button>,
        ]}
      >
        {testResults.llm && (
          <Alert
            message={testResults.llm.success ? '连接成功' : '连接失败'}
            description={testResults.llm.message}
            type={testResults.llm.success ? 'success' : 'error'}
            showIcon
          />
        )}
      </Modal>
    </div>
  );
};

export default LLMConfig;