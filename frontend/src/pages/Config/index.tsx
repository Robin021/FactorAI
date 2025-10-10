import React from 'react';
import { Card, Tabs } from 'antd';
import { SettingOutlined, ApiOutlined, DatabaseOutlined } from '@ant-design/icons';
import PageHeader from '@/components/Common/PageHeader';
import '@/styles/themes.css';

const Config: React.FC = () => {
  return (
    <div className="config-page">
      <PageHeader title="系统配置" />
      
      <Card>
        <Tabs
          defaultActiveKey="llm"
          type="card"
          items={[
            {
              key: 'llm',
              label: (
                <span>
                  <ApiOutlined /> LLM 配置
                </span>
              ),
              children: <p>这里将显示 LLM 配置选项...</p>,
            },
            {
              key: 'datasource',
              label: (
                <span>
                  <DatabaseOutlined /> 数据源配置
                </span>
              ),
              children: <p>这里将显示数据源配置选项...</p>,
            },
            {
              key: 'system',
              label: (
                <span>
                  <SettingOutlined /> 系统设置
                </span>
              ),
              children: <p>这里将显示系统设置选项...</p>,
            },
          ]}
        />
      </Card>
    </div>
  );
};

export default Config;
