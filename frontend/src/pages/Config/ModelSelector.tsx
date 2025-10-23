import React, { useState, useEffect } from 'react';
import {
  Card,
  Select,
  Button,
  Space,
  Alert,
  Typography,
  Spin,
  message,
  Descriptions,
  Tag,
} from 'antd';
import {
  SaveOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import apiClient from '@/services/api';

const { Title, Text } = Typography;
const { Option } = Select;

interface ModelInfo {
  provider: string;
  model_name: string;
  enabled: boolean;
  max_tokens: number;
  temperature: number;
}

interface DefaultModelConfig {
  default_provider: string;
  default_model: string;
  available_models: ModelInfo[];
}

const ModelSelector: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [config, setConfig] = useState<DefaultModelConfig | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [error, setError] = useState<string>('');

  const loadConfig = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await apiClient.get('/config/default-model');
      // 兼容两种响应格式: { success: true, data: {...} } 或 { status: "success", data: {...} }
      const isSuccess = response.success || response.status === 'success';
      const configData = response.data;
      
      if (isSuccess && configData) {
        setConfig(configData as DefaultModelConfig);
        setSelectedProvider(configData.default_provider);
        setSelectedModel(configData.default_model);
      }
    } catch (err: any) {
      setError(err.message || '加载配置失败');
      message.error('加载配置失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConfig();
  }, []);

  const handleSave = async () => {
    if (!selectedProvider || !selectedModel) {
      message.warning('请选择提供商和模型');
      return;
    }

    setSaving(true);
    try {
      const response = await apiClient.put('/config/default-model', {
        provider: selectedProvider,
        model_name: selectedModel,
      });
      
      // 兼容两种响应格式
      const isSuccess = response.success || response.status === 'success';
      if (isSuccess) {
        message.success('默认模型已更新');
        loadConfig();
      }
    } catch (err: any) {
      message.error(err.message || '保存失败');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    if (config) {
      setSelectedProvider(config.default_provider);
      setSelectedModel(config.default_model);
      message.info('已重置为当前配置');
    }
  };

  const getProviderName = (provider: string): string => {
    const names: Record<string, string> = {
      dashscope: '阿里百炼 (通义千问)',
      deepseek: 'DeepSeek',
      openai: 'OpenAI',
      google: 'Google Gemini',
      qianfan: '百度千帆',
    };
    return names[provider] || provider;
  };

  const getAvailableProviders = (): string[] => {
    if (!config) return [];
    const providers = new Set(config.available_models.map(m => m.provider));
    return Array.from(providers);
  };

  const getModelsForProvider = (provider: string): ModelInfo[] => {
    if (!config) return [];
    return config.available_models.filter(m => m.provider === provider);
  };

  const currentModel = config?.available_models.find(
    m => m.provider === selectedProvider && m.model_name === selectedModel
  );

  const hasChanges = config && (
    selectedProvider !== config.default_provider ||
    selectedModel !== config.default_model
  );

  return (
    <div className="model-selector">
      <Card>
        <div style={{ marginBottom: 16 }}>
          <Title level={3}>默认模型选择</Title>
          <Text type="secondary">
            选择系统默认使用的大语言模型，修改后立即生效
          </Text>
        </div>

        {error && (
          <Alert
            message="加载错误"
            description={error}
            type="error"
            showIcon
            closable
            onClose={() => setError('')}
            style={{ marginBottom: 16 }}
          />
        )}

        <Spin spinning={loading}>
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            {/* 当前配置 */}
            {config && (
              <Alert
                message={
                  <Space>
                    <CheckCircleOutlined />
                    <span>
                      当前默认模型: <strong>{getProviderName(config.default_provider)}</strong> / <strong>{config.default_model}</strong>
                    </span>
                  </Space>
                }
                type="info"
                showIcon={false}
              />
            )}

            {/* 模型选择 */}
            <Space size="large" style={{ width: '100%' }}>
              <div style={{ flex: 1 }}>
                <div style={{ marginBottom: 8 }}>
                  <Text strong>提供商</Text>
                </div>
                <Select
                  style={{ width: '100%' }}
                  value={selectedProvider}
                  onChange={(value) => {
                    setSelectedProvider(value);
                    // 自动选择该提供商的第一个模型
                    const models = getModelsForProvider(value);
                    if (models.length > 0) {
                      setSelectedModel(models[0].model_name);
                    }
                  }}
                  placeholder="选择提供商"
                >
                  {getAvailableProviders().map(provider => (
                    <Option key={provider} value={provider}>
                      {getProviderName(provider)}
                    </Option>
                  ))}
                </Select>
              </div>

              <div style={{ flex: 1 }}>
                <div style={{ marginBottom: 8 }}>
                  <Text strong>模型</Text>
                </div>
                <Select
                  style={{ width: '100%' }}
                  value={selectedModel}
                  onChange={setSelectedModel}
                  placeholder="选择模型"
                  disabled={!selectedProvider}
                >
                  {getModelsForProvider(selectedProvider).map(model => (
                    <Option key={model.model_name} value={model.model_name}>
                      <Space>
                        {model.model_name}
                        {model.enabled && <Tag color="green">已启用</Tag>}
                      </Space>
                    </Option>
                  ))}
                </Select>
              </div>
            </Space>

            {/* 模型详情 */}
            {currentModel && (
              <Card size="small" title="模型参数">
                <Descriptions column={2} size="small">
                  <Descriptions.Item label="提供商">
                    {getProviderName(currentModel.provider)}
                  </Descriptions.Item>
                  <Descriptions.Item label="模型名称">
                    {currentModel.model_name}
                  </Descriptions.Item>
                  <Descriptions.Item label="最大 Tokens">
                    {currentModel.max_tokens}
                  </Descriptions.Item>
                  <Descriptions.Item label="Temperature">
                    {currentModel.temperature}
                  </Descriptions.Item>
                  <Descriptions.Item label="状态">
                    <Tag color={currentModel.enabled ? 'green' : 'red'}>
                      {currentModel.enabled ? '已启用' : '未启用'}
                    </Tag>
                  </Descriptions.Item>
                </Descriptions>
              </Card>
            )}

            {/* 操作按钮 */}
            <Space>
              <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={handleSave}
                loading={saving}
                disabled={!hasChanges}
              >
                保存更改
              </Button>
              <Button
                icon={<ReloadOutlined />}
                onClick={handleReset}
                disabled={!hasChanges}
              >
                重置
              </Button>
              <Button onClick={loadConfig}>
                刷新
              </Button>
            </Space>

            {/* 提示信息 */}
            <Alert
              message="提示"
              description={
                <ul style={{ margin: 0, paddingLeft: 20 }}>
                  <li>只显示已启用且配置了 API 密钥的模型</li>
                  <li>修改默认模型后，新的分析任务将使用新模型</li>
                  <li>如需添加新模型，请在 .env 文件中配置对应的 API 密钥</li>
                </ul>
              }
              type="info"
              showIcon
            />
          </Space>
        </Spin>
      </Card>
    </div>
  );
};

export default ModelSelector;
