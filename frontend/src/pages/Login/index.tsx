import React from 'react';
import { Form, Input, Button, Card, Typography, message, Checkbox, Alert, Divider } from 'antd';
import { UserOutlined, LockOutlined, SafetyCertificateOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { LoginCredentials } from '@/types';
import './Login.css';
import { BRAND_NAME, BRAND_TAGLINE } from '@/constants/brand';

const { Title } = Typography;

interface LoginFormValues extends LoginCredentials {
  remember: boolean;
}

const Login: React.FC = () => {
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const { login, isLoading, error, clearError } = useAuth();
  const [loginAttempts, setLoginAttempts] = React.useState(0);
  const [isBlocked, setIsBlocked] = React.useState(false);
  const [blockTimeRemaining, setBlockTimeRemaining] = React.useState(0);

  // Auto-login check on component mount
  React.useEffect(() => {
    const savedCredentials = localStorage.getItem('saved_credentials');
    const rememberMe = localStorage.getItem('remember_me') === 'true';

    if (savedCredentials && rememberMe) {
      try {
        const credentials = JSON.parse(savedCredentials);
        form.setFieldsValue({
          username: credentials.username,
          remember: true,
        });
      } catch (error) {
        console.warn('Failed to load saved credentials:', error);
        localStorage.removeItem('saved_credentials');
        localStorage.removeItem('remember_me');
      }
    }
  }, [form]);

  // Handle login attempt blocking
  React.useEffect(() => {
    if (loginAttempts >= 5) {
      setIsBlocked(true);
      setBlockTimeRemaining(300); // 5 minutes block

      const timer = setInterval(() => {
        setBlockTimeRemaining(prev => {
          if (prev <= 1) {
            setIsBlocked(false);
            setLoginAttempts(0);
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearInterval(timer);
    }
  }, [loginAttempts]);

  const handleSubmit = async (values: LoginFormValues) => {
    if (isBlocked) {
      message.error(`登录已被锁定，请等待 ${Math.ceil(blockTimeRemaining / 60)} 分钟后重试`);
      return;
    }

    try {
      await login({
        username: values.username,
        password: values.password,
      });

      // Handle remember me functionality
      if (values.remember) {
        localStorage.setItem(
          'saved_credentials',
          JSON.stringify({
            username: values.username,
          })
        );
        localStorage.setItem('remember_me', 'true');
      } else {
        localStorage.removeItem('saved_credentials');
        localStorage.removeItem('remember_me');
      }

      // Reset login attempts on successful login
      setLoginAttempts(0);
      message.success('登录成功，正在跳转...');

      // 延迟跳转到仪表板
      setTimeout(() => {
        navigate('/dashboard');
      }, 1000);
    } catch (error: any) {
      setLoginAttempts(prev => prev + 1);

      // Enhanced error handling with specific messages
      let errorMessage = '登录失败';

      if (error.response?.status === 401) {
        errorMessage = '用户名或密码错误';
      } else if (error.response?.status === 403) {
        errorMessage = '账户已被禁用，请联系管理员';
      } else if (error.response?.status === 429) {
        errorMessage = '登录请求过于频繁，请稍后重试';
      } else if (error.message) {
        errorMessage = error.message;
      }

      message.error(errorMessage);

      // Show remaining attempts warning
      const remainingAttempts = 5 - (loginAttempts + 1);
      if (remainingAttempts > 0 && remainingAttempts <= 2) {
        message.warning(`还有 ${remainingAttempts} 次尝试机会`);
      }
    }
  };

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  // Authing SSO 登录
  const handleAuthingLogin = () => {
    // Authing 配置 - 从环境变量读取
    const origin = window.location.origin;
    const authingConfig = {
      appId: import.meta.env.VITE_AUTHING_APP_ID || '68d3879e03d9b1907f220731',
      appHost: import.meta.env.VITE_AUTHING_APP_HOST || 'https://sxkc6t59wbj9-demo.authing.cn',
      // 确保与后续 exchange 请求中的 redirect_uri 完全一致
      redirectUri: import.meta.env.VITE_AUTHING_REDIRECT_URI || `${origin}/auth/callback`,
    };

    // 构建 Authing 登录 URL
    // 使用完整的 scope 来确保获取稳定的用户信息
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

    // 记录本次使用的 redirect_uri，确保与 token 交换阶段完全一致
    try {
      localStorage.setItem('authing_redirect_uri', authingConfig.redirectUri);
    } catch {}

    message.info('正在跳转到 Authing SSO 登录...');
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

        {/* Error Alert */}
        {error && (
          <Alert
            message="登录失败"
            description={error}
            type="error"
            showIcon
            closable
            onClose={clearError}
            style={{ marginBottom: 16 }}
          />
        )}

        {/* Block Alert */}
        {isBlocked && (
          <Alert
            message="账户已锁定"
            description={`由于多次登录失败，账户已被临时锁定。请等待 ${formatTime(blockTimeRemaining)} 后重试。`}
            type="warning"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        {/* Login Attempts Warning */}
        {loginAttempts > 0 && loginAttempts < 5 && !isBlocked && (
          <Alert
            message={`登录失败 ${loginAttempts} 次`}
            description={`还有 ${5 - loginAttempts} 次尝试机会，超过限制将锁定账户 5 分钟。`}
            type="warning"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        <Form
          form={form}
          name="login"
          onFinish={handleSubmit}
          autoComplete="off"
          size="large"
          initialValues={{ remember: false }}
        >
          <Form.Item
            name="username"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 3, message: '用户名至少3个字符' },
              { max: 50, message: '用户名不能超过50个字符' },
              { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线' },
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="用户名"
              disabled={isBlocked}
              autoComplete="username"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6个字符' },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
              disabled={isBlocked}
              autoComplete="current-password"
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Checkbox disabled={isBlocked}>记住用户名</Checkbox>
              <Button type="link" size="small" disabled={isBlocked} style={{ padding: 0 }}>
                忘记密码？
              </Button>
            </div>
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={isLoading} disabled={isBlocked} block>
              {isBlocked ? `锁定中 (${formatTime(blockTimeRemaining)})` : '登录'}
            </Button>
          </Form.Item>
        </Form>

        {/* 分隔线 */}
        <Divider>或</Divider>

        {/* Authing SSO 登录 */}
        <Button
          icon={<SafetyCertificateOutlined />}
          onClick={handleAuthingLogin}
          disabled={isBlocked}
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
