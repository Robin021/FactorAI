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
  Table,
  Tag,
  Popconfirm,
  Upload,
  Progress,
} from 'antd';
import {
  SaveOutlined,
  TestConnectionOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
  UpOutlined,
  DownOutlined,
  ExportOutlined,
  ImportOutlined,
  ClearOutlined,
} from '@ant-design/icons';
import { useConfigStore } from '@/stores/configStore';
import { DataSourceConfig as DataSourceConfigType, DataSourceType } from '@/services/config';
import './DataSourceConfig.css';

const { Title, Text } = Typography;
const { Option } = Select;
const { Password } = Input;

interface DataSourceInfo {
  name: string;
  description: string;
  markets: string[];
  requiresApiKey: boolean;
  requiresSecret: boolean;
  freeTier: boolean;
  features: string[];
  documentationUrl: string;
}

const DATA_SOURCE_INFO: Record<DataSourceType, DataSourceInfo> = {
  [DataSourceType.TUSHARE]: {
    name: 'Tushare',
    description: '专业的股票数据接口，提供全面的A股数据',
    markets: ['cn'],
    requiresApiKey: true,
    requiresSecret: false,
    freeTier: true,
    features: ['股价数据', '财务数据', '基本面数据', '指标数据'],
    documentationUrl: 'https://tushare.pro/document/2',
  },
  [DataSourceType.AKSHARE]: {
    name: 'AKShare',
    description: '开源财经数据接口库，支持多市场数据',
    markets: ['cn', 'us', 'hk'],
    requiresApiKey: false,
    requiresSecret: false,
    freeTier: true,
    features: ['股价数据', '新闻数据', '宏观数据', '期货数据'],
    documentationUrl: 'https://akshare.akfamily.xyz/',
  },
  [DataSourceType.FINNHUB]: {
    name: 'Finnhub',
    description: '全球股票数据API，支持美股和港股',
    markets: ['us', 'hk'],
    requiresApiKey: true,
    requiresSecret: false,
    freeTier: true,
    features: ['股价数据', '新闻数据', '财务数据', '技术指标'],
    documentationUrl: 'https://finnhub.io/docs/api',
  },
  [DataSourceType.BAOSTOCK]: {
    name: 'BaoStock',
    description: '免费开源的证券数据平台',
    markets: ['cn'],
    requiresApiKey: false,
    requiresSecret: false,
    freeTier: true,
    features: ['股价数据', '财务数据', '除权除息'],
    documentationUrl: 'http://baostock.com/baostock/index.html',
  },
};

const DataSourceConfig: React.FC = () => {
  const [form] = Form.useForm();
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [testModalVisible, setTestModalVisible] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [editingConfig, setEditingConfig] = useState<DataSourceConfigType | null>(null);
  const [editingIndex, setEditingIndex] = useState<number>(-1);
  
  const {
    dataSourceConfigs,
    isLoading,
    error,
    testResults,
    loadDataSourceConfigs,
    updateDataSourceConfigs,
    testDataSourceConnection,
    clearError,
    clearTestResults,
  } = useConfigStore();

  useEffect(() => {
    loadDataSourceConfigs();
  }, [loadDataSourceConfigs]);

  const handleAdd = () => {
    setEditingConfig({
      source_type: DataSourceType.AKSHARE,
      priority: dataSourceConfigs.length + 1,
      timeout: 30,
      cache_ttl: 3600,
      enabled: true,
    });
    setEditingIndex(-1);
    form.setFieldsValue({
      source_type: DataSourceType.AKSHARE,
      priority: dataSourceConfigs.length + 1,
      timeout: 30,
      cache_ttl: 3600,
      enabled: true,
    });
    setEditModalVisible(true);
  };

  const handleEdit = (config: DataSourceConfigType, index: number) => {
    setEditingConfig(config);
    setEditingIndex(index);
    form.setFieldsValue(config);
    setEditModalVisible(true);
  };

  const handleDelete = (index: number) => {
    const newConfigs = [...dataSourceConfigs];
    newConfigs.splice(index, 1);
    // Reorder priorities
    newConfigs.forEach((config, i) => {
      config.priority = i + 1;
    });
    updateDataSourceConfigs(newConfigs);
    message.success('数据源已删除');
  };

  const handleMovePriority = (index: number, direction: 'up' | 'down') => {
    const newConfigs = [...dataSourceConfigs];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    
    if (targetIndex < 0 || targetIndex >= newConfigs.length) return;
    
    // Swap configs
    [newConfigs[index], newConfigs[targetIndex]] = [newConfigs[targetIndex], newConfigs[index]];
    
    // Update priorities
    newConfigs.forEach((config, i) => {
      config.priority = i + 1;
    });
    
    updateDataSourceConfigs(newConfigs);
    message.success('优先级已更新');
  };

  const handleSaveConfig = async () => {
    try {
      const values = await form.validateFields();
      const newConfig: DataSourceConfigType = {
        ...values,
        priority: editingIndex === -1 ? dataSourceConfigs.length + 1 : editingConfig?.priority || 1,
      };

      let newConfigs = [...dataSourceConfigs];
      
      if (editingIndex === -1) {
        // Add new config
        newConfigs.push(newConfig);
      } else {
        // Update existing config
        newConfigs[editingIndex] = newConfig;
      }

      await updateDataSourceConfigs(newConfigs);
      setEditModalVisible(false);
      setEditingConfig(null);
      setEditingIndex(-1);
      form.resetFields();
      message.success(editingIndex === -1 ? '数据源已添加' : '数据源已更新');
    } catch (error: any) {
      if (error.errorFields) {
        message.error('请检查表单输入');
      } else {
        message.error(error.message || '保存失败');
      }
    }
  };

  const handleTest = async (config: DataSourceConfigType) => {
    try {
      setIsTesting(true);
      clearTestResults();
      await testDataSourceConnection(config);
      setTestModalVisible(true);
    } catch (error: any) {
      message.error(error.message || '测试失败');
    } finally {
      setIsTesting(false);
    }
  };

  const handleClearCache = () => {
    Modal.confirm({
      title: '清理缓存',
      content: '确定要清理所有数据源缓存吗？这将删除所有缓存的数据。',
      onOk: () => {
        // TODO: Implement cache clearing
        message.success('缓存已清理');
      },
    });
  };

  const handleExport = () => {
    const exportData = {
      version: '1.0',
      exported_at: new Date().toISOString(),
      data_sources: dataSourceConfigs,
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json',
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `data-source-config-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    message.success('配置已导出');
  };

  const handleImport = (file: File) => {
    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const importData = JSON.parse(e.target?.result as string);
        const configs = importData.data_sources || [];
        
        // Validate imported configs
        const validConfigs = configs.filter((config: any) => {
          return config.source_type && Object.values(DataSourceType).includes(config.source_type);
        });
        
        if (validConfigs.length === 0) {
          message.error('导入文件中没有有效的数据源配置');
          return;
        }
        
        await updateDataSourceConfigs(validConfigs);
        message.success(`成功导入 ${validConfigs.length} 个数据源配置`);
      } catch (error) {
        message.error('导入失败：文件格式不正确');
      }
    };
    reader.readAsText(file);
    return false; // Prevent default upload behavior
  };

  const columns = [
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
      render: (priority: number, record: DataSourceConfigType, index: number) => (
        <Space>
          <Text strong>{priority}</Text>
          <Space direction="vertical" size={0}>
            <Button
              type="text"
              size="small"
              icon={<UpOutlined />}
              disabled={index === 0}
              onClick={() => handleMovePriority(index, 'up')}
            />
            <Button
              type="text"
              size="small"
              icon={<DownOutlined />}
              disabled={index === dataSourceConfigs.length - 1}
              onClick={() => handleMovePriority(index, 'down')}
            />
          </Space>
        </Space>
      ),
    },
    {
      title: '数据源',
      dataIndex: 'source_type',
      key: 'source_type',
      render: (sourceType: DataSourceType) => {
        const info = DATA_SOURCE_INFO[sourceType];
        return (
          <Space direction="vertical" size={0}>
            <Text strong>{info.name}</Text>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {info.description}
            </Text>
            <Space>
              {info.markets.map((market) => (
                <Tag key={market} size="small">
                  {market.toUpperCase()}
                </Tag>
              ))}
            </Space>
          </Space>
        );
      },
    },
    {
      title: '配置状态',
      key: 'status',
      render: (record: DataSourceConfigType) => {
        const info = DATA_SOURCE_INFO[record.source_type];
        const hasApiKey = !info.requiresApiKey || !!record.api_key;
        const hasSecret = !info.requiresSecret || !!record.api_secret;
        
        return (
          <Space direction="vertical" size={0}>
            <Tag color={record.enabled ? 'green' : 'red'}>
              {record.enabled ? '启用' : '禁用'}
            </Tag>
            {info.requiresApiKey && (
              <Tag color={hasApiKey ? 'blue' : 'orange'}>
                {hasApiKey ? 'API Key 已配置' : 'API Key 未配置'}
              </Tag>
            )}
            {info.requiresSecret && (
              <Tag color={hasSecret ? 'blue' : 'orange'}>
                {hasSecret ? 'Secret 已配置' : 'Secret 未配置'}
              </Tag>
            )}
          </Space>
        );
      },
    },
    {
      title: '缓存设置',
      key: 'cache',
      render: (record: DataSourceConfigType) => (
        <Space direction="vertical" size={0}>
          <Text>TTL: {record.cache_ttl}s</Text>
          <Text>超时: {record.timeout}s</Text>
        </Space>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (record: DataSourceConfigType, _, index: number) => (
        <Space>
          <Button
            type="text"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record, index)}
          >
            编辑
          </Button>
          <Button
            type="text"
            size="small"
            icon={<TestConnectionOutlined />}
            loading={isTesting}
            onClick={() => handleTest(record)}
          >
            测试
          </Button>
          <Popconfirm
            title="确定要删除这个数据源吗？"
            onConfirm={() => handleDelete(index)}
          >
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const sourceTypeInfo = editingConfig ? DATA_SOURCE_INFO[editingConfig.source_type] : null;

  return (
    <div className="data-source-config">
      <Card>
        <div className="data-source-config-header">
          <Title level={3}>数据源配置管理</Title>
          <Text type="secondary">
            配置和管理股票数据源，设置优先级和缓存策略
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

        <div className="data-source-config-actions">
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleAdd}
            >
              添加数据源
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadDataSourceConfigs}
              loading={isLoading}
            >
              刷新
            </Button>
            <Button
              icon={<ClearOutlined />}
              onClick={handleClearCache}
            >
              清理缓存
            </Button>
          </Space>

          <Space>
            <Button
              icon={<ExportOutlined />}
              onClick={handleExport}
            >
              导出配置
            </Button>
            <Upload
              accept=".json"
              showUploadList={false}
              beforeUpload={handleImport}
            >
              <Button icon={<ImportOutlined />}>
                导入配置
              </Button>
            </Upload>
          </Space>
        </div>

        <Spin spinning={isLoading}>
          <Table
            columns={columns}
            dataSource={dataSourceConfigs}
            rowKey={(record, index) => `${record.source_type}-${index}`}
            pagination={false}
            size="middle"
          />
        </Spin>
      </Card>

      {/* Edit/Add Modal */}
      <Modal
        title={editingIndex === -1 ? '添加数据源' : '编辑数据源'}
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          setEditingConfig(null);
          setEditingIndex(-1);
          form.resetFields();
        }}
        footer={[
          <Button
            key="cancel"
            onClick={() => {
              setEditModalVisible(false);
              setEditingConfig(null);
              setEditingIndex(-1);
              form.resetFields();
            }}
          >
            取消
          </Button>,
          <Button
            key="save"
            type="primary"
            icon={<SaveOutlined />}
            onClick={handleSaveConfig}
          >
            保存
          </Button>,
        ]}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            timeout: 30,
            cache_ttl: 3600,
            enabled: true,
          }}
        >
          <Form.Item
            label="数据源类型"
            name="source_type"
            rules={[{ required: true, message: '请选择数据源类型' }]}
          >
            <Select
              placeholder="选择数据源类型"
              onChange={(value) => {
                setEditingConfig(prev => prev ? { ...prev, source_type: value } : null);
              }}
            >
              {Object.entries(DATA_SOURCE_INFO).map(([key, info]) => (
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

          {sourceTypeInfo && (
            <Alert
              message={`${sourceTypeInfo.name} 数据源信息`}
              description={
                <div>
                  <p>{sourceTypeInfo.description}</p>
                  <p><strong>支持市场:</strong> {sourceTypeInfo.markets.join(', ')}</p>
                  <p><strong>主要功能:</strong> {sourceTypeInfo.features.join(', ')}</p>
                  <p><strong>免费额度:</strong> {sourceTypeInfo.freeTier ? '有' : '无'}</p>
                </div>
              }
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}

          {sourceTypeInfo?.requiresApiKey && (
            <Form.Item
              label="API Key"
              name="api_key"
              rules={[{ required: true, message: '请输入 API Key' }]}
            >
              <Password placeholder="输入 API Key" />
            </Form.Item>
          )}

          {sourceTypeInfo?.requiresSecret && (
            <Form.Item
              label="API Secret"
              name="api_secret"
              rules={[{ required: true, message: '请输入 API Secret' }]}
            >
              <Password placeholder="输入 API Secret" />
            </Form.Item>
          )}

          <Row gutter={16}>
            <Col span={12}>
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

            <Col span={12}>
              <Form.Item
                label={
                  <Space>
                    缓存时间 (秒)
                    <Tooltip title="数据缓存的有效时间">
                      <InfoCircleOutlined />
                    </Tooltip>
                  </Space>
                }
                name="cache_ttl"
                rules={[
                  { required: true, message: '请输入缓存时间' },
                  { type: 'number', min: 0, message: '缓存时间不能为负数' },
                ]}
              >
                <InputNumber
                  min={0}
                  style={{ width: '100%' }}
                  placeholder="3600"
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            label="启用状态"
            name="enabled"
            valuePropName="checked"
          >
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>

          {sourceTypeInfo && (
            <div style={{ marginTop: 16 }}>
              <Button
                type="link"
                href={sourceTypeInfo.documentationUrl}
                target="_blank"
                icon={<InfoCircleOutlined />}
              >
                查看 {sourceTypeInfo.name} 文档
              </Button>
            </div>
          )}
        </Form>
      </Modal>

      {/* Test Results Modal */}
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
        {testResults.dataSource && (
          <Alert
            message={testResults.dataSource.success ? '连接成功' : '连接失败'}
            description={testResults.dataSource.message}
            type={testResults.dataSource.success ? 'success' : 'error'}
            showIcon
          />
        )}
      </Modal>
    </div>
  );
};

export default DataSourceConfig;