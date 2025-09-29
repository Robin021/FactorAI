import React, { useEffect } from 'react';
import { Spin, Result, Button } from 'antd';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';

const AuthCallback: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login } = useAuth();
  const [status, setStatus] = React.useState<'loading' | 'success' | 'error'>('loading');
  const [errorMessage, setErrorMessage] = React.useState('');

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        const code = searchParams.get('code');
        const state = searchParams.get('state');
        
        if (!code) {
          throw new Error('授权码缺失');
        }

        // 调用后端处理 Authing 回调
        const response = await fetch(`/api/v1/auth/authing/callback?code=${code}&state=${state || ''}`);
        const data = await response.json();
        
        if (response.ok) {
          // 保存 token 并跳转
          localStorage.setItem('auth_token', data.access_token);
          setStatus('success');
          
          // 延迟跳转到首页
          setTimeout(() => {
            navigate('/dashboard');
          }, 2000);
        } else {
          throw new Error(data.detail || 'SSO 登录失败');
        }
      } catch (error: any) {
        console.error('Authing callback error:', error);
        setErrorMessage(error.message || 'SSO 登录处理失败');
        setStatus('error');
      }
    };

    handleAuthCallback();
  }, [searchParams, navigate]);

  if (status === 'loading') {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '100vh',
        flexDirection: 'column',
        gap: '20px'
      }}>
        <Spin size="large" />
        <div style={{ textAlign: 'center' }}>
          <h3>正在处理 SSO 登录...</h3>
          <p>请稍候，我们正在验证您的身份</p>
        </div>
      </div>
    );
  }

  if (status === 'success') {
    return (
      <Result
        status="success"
        title="SSO 登录成功！"
        subTitle="正在跳转到系统首页..."
        extra={[
          <Button type="primary" key="dashboard" onClick={() => navigate('/dashboard')}>
            立即进入系统
          </Button>
        ]}
      />
    );
  }

  return (
    <Result
      status="error"
      title="SSO 登录失败"
      subTitle={errorMessage}
      extra={[
        <Button type="primary" key="retry" onClick={() => navigate('/login')}>
          返回登录页面
        </Button>
      ]}
    />
  );
};

export default AuthCallback;