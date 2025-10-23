import React, { useState, useEffect } from 'react';
import { Layout, Menu, Button, Avatar, Dropdown, Typography, Badge, Drawer } from 'antd';
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
import { BRAND_NAME, BRAND_SHORT } from '@/constants/brand';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

const MainLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const { unreadCount } = useNotificationStore();
  const { showNotificationCenter, NotificationCenter } = useNotificationCenter();
  const { themeMode, toggleTheme } = useTheme();

  // 检测是否为移动端
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth <= 768;
      setIsMobile(mobile);
      if (mobile) {
        setCollapsed(true);
      }
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

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

  const handleMenuItemClick = ({ key }: { key: string }) => {
    handleMenuClick({ key });
    // 移动端点击菜单后自动关闭侧边栏
    if (isMobile) {
      setCollapsed(true);
    }
  };

  const sidebarContent = (
    <>
      <div className="logo">
        <Text strong style={{ fontSize: collapsed && !isMobile ? '14px' : '16px' }}>
          {collapsed && !isMobile ? BRAND_SHORT : BRAND_NAME}
        </Text>
      </div>
      
      <Menu
        theme={themeMode}
        mode="inline"
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={handleMenuItemClick}
      />
    </>
  );

  return (
    <Layout className="main-layout">
      {/* 桌面端侧边栏 */}
      {!isMobile && (
        <Sider 
          trigger={null} 
          collapsible 
          collapsed={collapsed}
          className="main-sider"
          width={240}
          collapsedWidth={64}
        >
          {sidebarContent}
        </Sider>
      )}

      {/* 移动端抽屉式侧边栏 */}
      {isMobile && (
        <Drawer
          placement="left"
          onClose={() => setCollapsed(true)}
          open={!collapsed}
          closable={false}
          width={240}
          className="mobile-drawer"
          styles={{
            body: { padding: 0, background: 'var(--card-bg)' }
          }}
        >
          {sidebarContent}
        </Drawer>
      )}
      
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
              style={{ color: 'var(--text-primary)', marginRight: 8 }}
              title={themeMode === 'dark' ? '切换到白天模式' : '切换到黑夜模式'}
            />
            
            <Button
              type="text"
              icon={
                <Badge count={unreadCount} size="small">
                  <BellOutlined style={{ color: 'var(--text-primary)', fontSize: '16px' }} />
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
                <Text style={{ marginLeft: 8 }}>
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
