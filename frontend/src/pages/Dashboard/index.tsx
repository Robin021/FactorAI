import React from 'react';
import { Card, Row, Col, Statistic } from 'antd';
import { 
  BarChartOutlined, 
  TrophyOutlined, 
  ClockCircleOutlined,
  UserOutlined 
} from '@ant-design/icons';
import PageHeader from '@/components/Common/PageHeader';
import '@/styles/themes.css';
import './Dashboard.css';

const Dashboard: React.FC = () => {
  return (
    <div className="dashboard">
      <PageHeader title="仪表板" />
      
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={12} lg={6}>
          <Card className="dashboard-card">
            <Statistic
              title="总分析次数"
              value={156}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: 'var(--success-color)' }}
            />
          </Card>
        </Col>
        
        <Col xs={12} sm={12} lg={6}>
          <Card className="dashboard-card">
            <Statistic
              title="成功分析"
              value={142}
              prefix={<TrophyOutlined />}
              valueStyle={{ color: 'var(--info-color)' }}
            />
          </Card>
        </Col>
        
        <Col xs={12} sm={12} lg={6}>
          <Card className="dashboard-card">
            <Statistic
              title="进行中"
              value={3}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: 'var(--warning-color)' }}
            />
          </Card>
        </Col>
        
        <Col xs={12} sm={12} lg={6}>
          <Card className="dashboard-card">
            <Statistic
              title="活跃用户"
              value={28}
              prefix={<UserOutlined />}
              valueStyle={{ color: 'var(--purple-color)' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card title="最近分析" size="small" className="dashboard-content-card">
            <p>这里将显示最近的分析记录...</p>
          </Card>
        </Col>
        
        <Col xs={24} lg={8}>
          <Card title="系统状态" size="small" className="dashboard-content-card">
            <p>这里将显示系统运行状态...</p>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
