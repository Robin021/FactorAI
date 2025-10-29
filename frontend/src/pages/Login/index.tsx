import React from 'react';
import { Button, Card, Typography, message } from 'antd';
import { SafetyCertificateOutlined } from '@ant-design/icons';
import './Login.css';
import { BRAND_NAME, BRAND_TAGLINE } from '@/constants/brand';

const { Title, Paragraph } = Typography;

const Login: React.FC = () => {

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

        <div className="login-footer">
          <p>© 2024 {BRAND_NAME}</p>
        </div>
      </Card>
    </div>
  );
};

export default Login;
