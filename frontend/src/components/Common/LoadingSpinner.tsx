import React from 'react';
import { Spin, Typography } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';
import './LoadingSpinner.css';

const { Text } = Typography;

interface LoadingSpinnerProps {
  size?: 'small' | 'default' | 'large';
  message?: string;
  spinning?: boolean;
  children?: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'default',
  message,
  spinning = true,
  children,
  className,
  style,
}) => {
  const antIcon = <LoadingOutlined style={{ fontSize: getSizeValue(size) }} spin />;

  if (children) {
    return (
      <Spin
        spinning={spinning}
        indicator={antIcon}
        tip={message}
        className={className}
        style={style}
      >
        {children}
      </Spin>
    );
  }

  return (
    <div className={`loading-spinner ${className || ''}`} style={style}>
      <Spin
        spinning={spinning}
        indicator={antIcon}
        size={size}
      />
      {message && (
        <Text className="loading-message" type="secondary">
          {message}
        </Text>
      )}
    </div>
  );
};

function getSizeValue(size: 'small' | 'default' | 'large'): number {
  switch (size) {
    case 'small':
      return 14;
    case 'large':
      return 32;
    default:
      return 24;
  }
}

export default LoadingSpinner;