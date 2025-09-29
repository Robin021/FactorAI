import React from 'react';
import { Layout } from 'antd';
import './AuthLayout.css';

interface AuthLayoutProps {
  children: React.ReactNode;
}

const AuthLayout: React.FC<AuthLayoutProps> = ({ children }) => {
  return (
    <Layout className="auth-layout">
      <Layout.Content className="auth-content">
        {children}
      </Layout.Content>
    </Layout>
  );
};

export default AuthLayout;