import React from 'react';
import { Card, Row, Col, Statistic, Typography } from 'antd';
import { 
  BarChartOutlined, 
  TrophyOutlined, 
  ClockCircleOutlined,
  UserOutlined 
} from '@ant-design/icons';

const { Title } = Typography;

const Dashboard: React.FC = () => {
  return (
    <div className="dashboard">
      <Title level={2}>仪表板</Title>
      
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总分析次数"
              value={156}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="成功分析"
              value={142}
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="进行中"
              value={3}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="活跃用户"
              value={28}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card title="最近分析" size="small">
            <p>这里将显示最近的分析记录...</p>
          </Card>
        </Col>
        
        <Col xs={24} lg={8}>
          <Card title="系统状态" size="small">
            <p>这里将显示系统运行状态...</p>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;