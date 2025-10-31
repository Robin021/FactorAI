import React, { useState } from 'react';
import { Button, Card, Typography, message, Form, Input, Divider, Space } from 'antd';
import { SafetyCertificateOutlined, UserOutlined, LockOutlined, CodeOutlined } from '@ant-design/icons';
import './Login.css';
import { BRAND_NAME, BRAND_TAGLINE } from '@/constants/brand';
import { useAuth } from '@/hooks/useAuth';

// 开发模式检测
const isDevelopment = import.meta.env.MODE === 'development';
const enableDevLogin = isDevelopment && import.meta.env.VITE_ENABLE_DEV_LOGIN === 'true';

const { Title, Paragraph } = Typography;

const Login: React.FC = () => {
  const [showDevLogin, setShowDevLogin] = useState(false);
  const [form] = Form.useForm();
  const { login, isLoading } = useAuth();

  // 开发模式普通登录
  const handleDevLogin = async (values: { username: string; password: string }) => {
    try {
      await login(values);
      message.success('登录成功！');
    } catch (error: any) {
      message.error(error.message || '登录失败');
    }
  };

  // Authing SSO 登录
  const handleAuthingLogin = () => {
    const origin = window.location.origin;
    const authingConfig = {
      appId: import.meta.env.VITE_AUTHING_APP_ID || '68d3879e03d9b1907f220731',
      appHost: import.meta.env.VITE_AUTHING_APP_HOST || 'https://sxkc6t59wbj9-demo.authing.cn',
      redirectUri: import.meta.env.VITE_AUTHING_REDIRECT_URI || `${origin}/auth/callback`,
    };

    const scope = 'openid profile email phone username roles unionid external_id extended_fields';

    const authUrl =
      `${authingConfig.appHost}/oidc/auth?` +
      new URLSearchParams({
        client_id: authingConfig.appId,
        response_type: 'code',
        scope: scope,
        redirect_uri: authingConfig.redirectUri,
        state: Math.random().toString(36).substring(7),
      });

    try {
      localStorage.setItem('authing_redirect_uri', authingConfig.redirectUri);
    } catch { }

    message.info('正在跳转到企业 SSO 登录...');
    window.location.href = authUrl;
  };

  return (
    <div className="login-container">
      <Card className="login-card">
        <div className="login-header">
          <div className="logo-container">
            <img src="/logo.svg" alt="Factor AI Logo" className="logo-icon" />
          </div>
          <Title level={2} className="brand-title">
            {BRAND_NAME}
          </Title>
          <p className="brand-subtitle">{BRAND_TAGLINE}</p>
        </div>

        <div style={{ textAlign: 'center', margin: '32px 0' }}>
          <Paragraph type="secondary">
            使用企业账号登录以访问系统
          </Paragraph>
        </div>

        {/* 开发模式：显示普通登录表单 */}
        {enableDevLogin && showDevLogin ? (
          <div>
            <Form
              form={form}
              onFinish={handleDevLogin}
              layout="vertical"
              size="large"
            >
              <Form.Item
                name="username"
                rules={[{ required: true, message: '请输入用户名' }]}
              >
                <Input
                  prefix={<UserOutlined />}
                  placeholder="用户名 (dev)"
                />
              </Form.Item>
              
              <Form.Item
                name="password"
                rules={[{ required: true, message: '请输入密码' }]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="密码 (dev123456)"
                />
              </Form.Item>
              
              <Form.Item>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Button
                    type="primary"
                    htmlType="submit"
                    loading={isLoading}
                    block
                    size="large"
                  >
                    开发登录
                  </Button>
                  
                  <Button
                    type="link"
                    onClick={() => setShowDevLogin(false)}
                    block
                  >
                    返回 SSO 登录
                  </Button>
                </Space>
              </Form.Item>
            </Form>
            
            <div style={{ marginTop: 16, padding: 12, background: '#f6f8fa', borderRadius: 6 }}>
              <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                💡 开发模式测试账号：<br/>
                管理员: dev / dev123456<br/>
                用户: test / test123456
              </Typography.Text>
            </div>
          </div>
        ) : (
          <div>
            <Button
              type="primary"
              icon={<SafetyCertificateOutlined />}
              onClick={handleAuthingLogin}
              block
              size="large"
              className="sso-button"
            >
              企业 SSO 登录
            </Button>
            
            {/* 开发模式：显示开发登录入口 */}
            {enableDevLogin && (
              <>
                <Divider>或</Divider>
                <Button
                  type="dashed"
                  icon={<CodeOutlined />}
                  onClick={() => setShowDevLogin(true)}
                  block
                  size="large"
                  style={{ borderColor: '#1890ff', color: '#1890ff' }}
                >
                  开发模式登录
                </Button>
              </>
            )}
          </div>
        )}

        <div className="login-footer">
          <p>© 2024 {BRAND_NAME}</p>
        </div>
      </Card>
    </div>
  );
};

export default Login;
