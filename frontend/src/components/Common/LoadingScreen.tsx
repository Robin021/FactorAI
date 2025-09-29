import React from 'react';
import { Spin, Typography } from 'antd';
import './LoadingScreen.css';

const { Text } = Typography;

interface LoadingScreenProps {
  tip?: string;
  size?: 'small' | 'default' | 'large';
}

const LoadingScreen: React.FC<LoadingScreenProps> = ({ 
  tip = '加载中...', 
  size = 'large' 
}) => {
  return (
    <div className="loading-screen">
      <div className="loading-content">
        <Spin size={size} />
        <Text className="loading-text">{tip}</Text>
      </div>
    </div>
  );
};

export default LoadingScreen;