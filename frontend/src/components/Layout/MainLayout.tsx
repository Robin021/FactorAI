import React, { useState } from 'react';
import { Layout, Menu, Button, Avatar, Dropdown, Typography, Badge } from 'antd';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DashboardOutlined,
  BarChartOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  BellOutlined,
  SunOutlined,
  MoonOutlined,
} from '@ant-design/icons';
import type { MenuProps } from 'antd';
import { useAuth } from '@/hooks/useAuth';
import { useNotificationStore } from '@/stores/notificationStore';
import { useNotificationCenter } from '@/components/Common/NotificationCenter';
import { useTheme } from '@/components/Common/ThemeProvider';
import './MainLayout.css';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

const MainLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const { unreadCount } = useNotificationStore();
  const { showNotificationCenter, NotificationCenter } = useNotificationCenter();
  const { themeMode, toggleTheme } = useTheme();

  const menuItems: MenuProps['items'] = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表板',
    },
    {
      key: '/analysis',
      icon: <BarChartOutlined />,
      label: '股票分析',
    },
    {
      key: '/config',
      icon: <SettingOutlined />,
      label: '系统配置',
    },
  ];

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      danger: true,
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  const handleUserMenuClick = async ({ key }: { key: string }) => {
    if (key === 'logout') {
      await logout();
      navigate('/login');
    }
  };

  return (
    <Layout className="main-layout">
      <Sider 
        trigger={null} 
        collapsible 
        collapsed={collapsed}
        className="main-sider"
      >
        <div className="logo">
          <Text strong style={{ color: 'white', fontSize: collapsed ? '14px' : '16px' }}>
            {collapsed ? 'TA' : 'TradingAgents'}
          </Text>
        </div>
        
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      
      <Layout>
        <Header className="main-header">
          <div className="header-left">
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              className="trigger"
            />
          </div>
          
          <div className="header-right">
            <Button
              type="text"
              icon={themeMode === 'dark' ? <SunOutlined /> : <MoonOutlined />}
              onClick={toggleTheme}
              style={{ color: 'white', marginRight: 8 }}
              title={themeMode === 'dark' ? '切换到浅色主题' : '切换到深色主题'}
            />
            
            <Button
              type="text"
              icon={
                <Badge count={unreadCount} size="small">
                  <BellOutlined style={{ color: 'white', fontSize: '16px' }} />
                </Badge>
              }
              onClick={showNotificationCenter}
              style={{ marginRight: 16 }}
            />
            
            <Dropdown
              menu={{ items: userMenuItems, onClick: handleUserMenuClick }}
              placement="bottomRight"
            >
              <div className="user-info">
                <Avatar size="small" icon={<UserOutlined />} />
                <Text style={{ marginLeft: 8, color: 'white' }}>
                  {user?.username || '用户'}
                </Text>
              </div>
            </Dropdown>
          </div>
        </Header>
        
        <Content className="main-content">
          <div className="content-wrapper">
            <Outlet />
          </div>
        </Content>
      </Layout>
      
      <NotificationCenter />
    </Layout>
  );
};

export default MainLayout;