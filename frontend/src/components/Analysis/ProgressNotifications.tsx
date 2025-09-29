import React from 'react';
import { notification, Progress } from 'antd';
import { 
  CheckCircleOutlined, 
  ExclamationCircleOutlined, 
  LoadingOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { Analysis } from '@/types';
import { usePolling } from '@/hooks/usePolling';

interface ProgressNotificationsProps {
  analysis: Analysis;
  enabled?: boolean;
}

const ProgressNotifications: React.FC<ProgressNotificationsProps> = ({ 
  analysis, 
  enabled = true 
}) => {
  const [notificationApi, contextHolder] = notification.useNotification();
  const [lastProgress, setLastProgress] = React.useState(0);
  const [progressNotificationKey, setProgressNotificationKey] = React.useState<string | null>(null);

  // 不再独立轮询，通过props接收进度数据
  // usePolling 已移除，避免重复请求
  const handleProgressData = (data: any) => {
    if (!enabled) return;
    handleProgressNotification(data);
  };

  const handleProgressNotification = (data: any) => {
    switch (data.type) {
      case 'analysis_started':
        showStartNotification();
        break;

      case 'progress':
        updateProgressNotification(data.progress, data.message);
        break;

      case 'step_complete':
        showStepCompleteNotification(data.stepName);
        break;

      case 'analysis_complete':
        showCompleteNotification();
        break;

      case 'analysis_error':
        showErrorNotification(data.error);
        break;

      case 'milestone_reached':
        showMilestoneNotification(data.milestone, data.progress);
        break;

      default:
        break;
    }
  };

  const showStartNotification = () => {
    const key = `analysis-start-${analysis.id}`;
    
    notificationApi.info({
      key,
      message: '分析已开始',
      description: `正在分析 ${analysis.stockCode}，请耐心等待...`,
      icon: <LoadingOutlined spin style={{ color: '#1890ff' }} />,
      duration: 3,
    });
  };

  const updateProgressNotification = (progress: number, message: string) => {
    // Only show progress notifications at significant intervals
    if (progress - lastProgress < 10 && progress < 100) {
      return;
    }

    const key = `analysis-progress-${analysis.id}`;
    setProgressNotificationKey(key);
    setLastProgress(progress);

    notificationApi.open({
      key,
      message: `分析进度 ${Math.round(progress)}%`,
      description: (
        <div>
          <div style={{ marginBottom: 8 }}>{message}</div>
          <Progress 
            percent={Math.round(progress)} 
            size="small" 
            showInfo={false}
            strokeColor="#1890ff"
          />
        </div>
      ),
      icon: <LoadingOutlined spin style={{ color: '#1890ff' }} />,
      duration: 0, // Keep open until manually closed
      placement: 'bottomRight',
    });
  };

  const showStepCompleteNotification = (stepName: string) => {
    const key = `step-complete-${analysis.id}-${Date.now()}`;
    
    notificationApi.success({
      key,
      message: '步骤完成',
      description: `${stepName} 已完成`,
      icon: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
      duration: 2,
      placement: 'bottomRight',
    });
  };

  const showCompleteNotification = () => {
    // Close progress notification
    if (progressNotificationKey) {
      notificationApi.destroy(progressNotificationKey);
    }

    const key = `analysis-complete-${analysis.id}`;
    
    notificationApi.success({
      key,
      message: '分析完成',
      description: `${analysis.stockCode} 的分析已成功完成，点击查看结果`,
      icon: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
      duration: 0,
      placement: 'topRight',
      onClick: () => {
        // Navigate to results or trigger callback
        window.location.hash = `#analysis-result-${analysis.id}`;
      },
    });

    // Show browser notification if permission granted
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('TradingAgents - 分析完成', {
        body: `${analysis.stockCode} 的股票分析已完成`,
        icon: '/favicon.ico',
        tag: `analysis-${analysis.id}`,
      });
    }
  };

  const showErrorNotification = (error: string) => {
    // Close progress notification
    if (progressNotificationKey) {
      notificationApi.destroy(progressNotificationKey);
    }

    const key = `analysis-error-${analysis.id}`;
    
    notificationApi.error({
      key,
      message: '分析失败',
      description: error || '分析过程中出现错误，请重试',
      icon: <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />,
      duration: 0,
      placement: 'topRight',
    });

    // Show browser notification if permission granted
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('TradingAgents - 分析失败', {
        body: `${analysis.stockCode} 的股票分析失败`,
        icon: '/favicon.ico',
        tag: `analysis-error-${analysis.id}`,
      });
    }
  };

  const showMilestoneNotification = (milestone: string, progress: number) => {
    const key = `milestone-${analysis.id}-${Date.now()}`;
    
    notificationApi.info({
      key,
      message: '里程碑达成',
      description: `${milestone} (${Math.round(progress)}%)`,
      icon: <ClockCircleOutlined style={{ color: '#faad14' }} />,
      duration: 3,
      placement: 'bottomRight',
    });
  };

  // Request notification permission on mount
  React.useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  // Cleanup notifications on unmount
  React.useEffect(() => {
    return () => {
      notificationApi.destroy();
    };
  }, [notificationApi]);

  return <>{contextHolder}</>;
};

export default ProgressNotifications;