import React, { useEffect } from 'react';
import { Spin, Result, Button } from 'antd';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';

const AuthCallback: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { getCurrentUser } = useAuthStore();
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

        // 调用后端交换 code 为应用访问令牌
        const storedRedirect = localStorage.getItem('authing_redirect_uri');
        const redirectUri = storedRedirect || `${window.location.origin}/auth/callback`;
        const response = await fetch(`/api/v1/auth/authing/exchange`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ code, state, redirect_uri: redirectUri }),
        });
        const data = await response.json();
        
        if (response.ok) {
          // 保存 token
          localStorage.setItem('auth_token', data.access_token);
          if (data.refresh_token) {
            localStorage.setItem('refresh_token', data.refresh_token);
          }
          
          // 更新认证状态
          await getCurrentUser();
          
          // 直接跳转，不需要等待
          navigate('/dashboard', { replace: true });
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
  }, [searchParams, navigate, getCurrentUser]);

  if (status === 'loading') {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '100vh',
        flexDirection: 'column',
        gap: '20px',
        background: 'var(--primary-bg)',
        color: 'var(--text-primary)'
      }}>
        <Spin size="large" />
        <div style={{ textAlign: 'center' }}>
          <h3 style={{ color: 'var(--text-primary)' }}>正在处理 SSO 登录...</h3>
          <p style={{ color: 'var(--text-secondary)' }}>请稍候，我们正在验证您的身份</p>
        </div>
      </div>
    );
  }



  return (
    <div style={{ 
      minHeight: '100vh', 
      background: 'var(--primary-bg)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
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
    </div>
  );
};

export default AuthCallback;
