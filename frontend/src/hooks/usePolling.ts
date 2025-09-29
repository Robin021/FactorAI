import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuthStore } from '@/stores/authStore';

interface UsePollingOptions {
  onData?: (data: any) => void;
  onError?: (error: Error) => void;
  interval?: number;
  enabled?: boolean;
}

interface UsePollingReturn {
  isPolling: boolean;
  lastData: any;
  error: Error | null;
  startPolling: () => void;
  stopPolling: () => void;
}

export const usePolling = (
  url: string,
  options: UsePollingOptions = {}
): UsePollingReturn => {
  const {
    onData,
    onError,
    interval = 60000, // 默认60秒（1分钟）轮询一次，适合长时间分析任务
    enabled = false, // 默认禁用轮询，避免疯狂刷新
  } = options;

  const [isPolling, setIsPolling] = useState(false);
  const [lastData, setLastData] = useState<any>(null);
  const [error, setError] = useState<Error | null>(null);
  
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const { isAuthenticated } = useAuthStore();

  const fetchData = useCallback(async () => {
    if (!isAuthenticated) {
      return;
    }

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/v1${url}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 404) {
          // 分析不存在，停止轮询
          setIsPolling(false);
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          return;
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setLastData(data);
      setError(null);
      onData?.(data);

      // 智能轮询：根据状态调整频率
      if (data.status === 'completed' || data.status === 'failed') {
        console.log(`分析已${data.status === 'completed' ? '完成' : '失败'}，停止轮询`);
        setIsPolling(false);
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      } else if (data.status === 'running' && data.progress > 80) {
        // 接近完成时，稍微提高频率（从60秒减少到30秒）
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = setInterval(fetchData, Math.max(interval * 0.5, 30000));
        }
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
      onError?.(error);
      console.error('Polling error:', error);
    }
  }, [url, isAuthenticated, onData, onError, interval]);

  const startPolling = useCallback(() => {
    if (!enabled || !isAuthenticated) {
      return;
    }

    setIsPolling(true);
    setError(null);
    
    // 立即执行一次
    fetchData();
    
    // 设置定时器
    intervalRef.current = setInterval(fetchData, interval);
  }, [enabled, isAuthenticated, fetchData, interval]);

  const stopPolling = useCallback(() => {
    setIsPolling(false);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (enabled && isAuthenticated) {
      startPolling();
    } else {
      stopPolling();
    }

    return () => {
      stopPolling();
    };
  }, [enabled, isAuthenticated, startPolling, stopPolling]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return {
    isPolling,
    lastData,
    error,
    startPolling,
    stopPolling,
  };
};