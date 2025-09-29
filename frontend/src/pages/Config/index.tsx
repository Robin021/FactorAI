import React from 'react';
import { Card, Typography, Tabs } from 'antd';
import { SettingOutlined, ApiOutlined, DatabaseOutlined } from '@ant-design/icons';

const { Title } = Typography;
const { TabPane } = Tabs;

const Config: React.FC = () => {
  return (
    <div className="config-page">
      <Title level={2}>系统配置</Title>
      
      <Card>
        <Tabs defaultActiveKey="llm" type="card">
          <TabPane 
            tab={
              <span>
                <ApiOutlined />
                LLM 配置
              </span>
            } 
            key="llm"
          >
            <p>这里将显示 LLM 配置选项...</p>
          </TabPane>
          
          <TabPane 
            tab={
              <span>
                <DatabaseOutlined />
                数据源配置
              </span>
            } 
            key="datasource"
          >
            <p>这里将显示数据源配置选项...</p>
          </TabPane>
          
          <TabPane 
            tab={
              <span>
                <SettingOutlined />
                系统设置
              </span>
            } 
            key="system"
          >
            <p>这里将显示系统设置选项...</p>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default Config;