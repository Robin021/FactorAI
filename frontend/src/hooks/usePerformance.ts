/**
 * 性能监控 Hook
 */
import { useEffect, useRef, useState } from 'react';
import { PerformanceMetrics, performanceMonitor } from '../utils/performance';

export interface UsePerformanceOptions {
  reportInterval?: number;
  enableMemoryMonitoring?: boolean;
  enableRenderTracking?: boolean;
}

export const usePerformance = (options: UsePerformanceOptions = {}) => {
  const {
    reportInterval = 30000, // 30秒
    enableMemoryMonitoring = true,
    enableRenderTracking = true,
  } = options;

  const [metrics, setMetrics] = useState<Partial<PerformanceMetrics>>({});
  const [renderCount, setRenderCount] = useState(0);
  const renderStartTime = useRef<number>(0);
  const intervalRef = useRef<NodeJS.Timeout>();

  // 跟踪组件渲染性能
  useEffect(() => {
    if (enableRenderTracking) {
      renderStartTime.current = performance.now();
      setRenderCount(prev => prev + 1);
    }
  });

  // 定期更新性能指标
  useEffect(() => {
    const updateMetrics = () => {
      const currentMetrics = performanceMonitor.getMetrics();
      setMetrics(currentMetrics);
    };

    // 立即更新一次
    updateMetrics();

    // 设置定期更新
    intervalRef.current = setInterval(updateMetrics, reportInterval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [reportInterval]);

  // 内存监控
  useEffect(() => {
    if (!enableMemoryMonitoring) return;

    const checkMemory = () => {
      if ('memory' in performance) {
        const memory = (performance as any).memory;
        const used = memory.usedJSHeapSize / 1024 / 1024;
        
        setMetrics(prev => ({
          ...prev,
          memoryUsage: used,
        }));

        // 内存泄漏警告
        if (used > 150) { // 150MB
          console.warn('Potential memory leak detected:', used.toFixed(2), 'MB');
        }
      }
    };

    const memoryInterval = setInterval(checkMemory, 10000); // 每10秒检查

    return () => clearInterval(memoryInterval);
  }, [enableMemoryMonitoring]);

  return {
    metrics,
    renderCount,
    reportMetrics: () => performanceMonitor.reportMetrics(),
  };
};

/**
 * 组件渲染时间测量 Hook
 */
export const useRenderTime = (componentName: string) => {
  const startTime = useRef<number>(0);
  const [renderTime, setRenderTime] = useState<number>(0);

  useEffect(() => {
    startTime.current = performance.now();
  });

  useEffect(() => {
    const endTime = performance.now();
    const duration = endTime - startTime.current;
    setRenderTime(duration);

    // 慢渲染警告
    if (duration > 16) { // 超过一帧时间 (60fps)
      console.warn(`Slow render detected in ${componentName}:`, duration.toFixed(2), 'ms');
    }
  });

  return renderTime;
};

/**
 * API 请求性能监控 Hook
 */
export const useApiPerformance = () => {
  const [apiMetrics, setApiMetrics] = useState<{
    [key: string]: {
      count: number;
      totalTime: number;
      averageTime: number;
      errors: number;
    };
  }>({});

  const trackApiCall = (url: string, startTime: number, success: boolean) => {
    const duration = performance.now() - startTime;
    
    setApiMetrics(prev => {
      const current = prev[url] || { count: 0, totalTime: 0, averageTime: 0, errors: 0 };
      const newCount = current.count + 1;
      const newTotalTime = current.totalTime + duration;
      const newErrors = success ? current.errors : current.errors + 1;
      
      return {
        ...prev,
        [url]: {
          count: newCount,
          totalTime: newTotalTime,
          averageTime: newTotalTime / newCount,
          errors: newErrors,
        },
      };
    });

    // 慢API警告
    if (duration > 3000) { // 超过3秒
      console.warn(`Slow API call detected: ${url}`, duration.toFixed(2), 'ms');
    }
  };

  return {
    apiMetrics,
    trackApiCall,
  };
};

/**
 * 虚拟列表性能优化 Hook
 */
export const useVirtualList = <T>(
  items: T[],
  itemHeight: number,
  containerHeight: number
) => {
  const [scrollTop, setScrollTop] = useState(0);
  
  const visibleCount = Math.ceil(containerHeight / itemHeight) + 2;
  const startIndex = Math.floor(scrollTop / itemHeight);
  const endIndex = Math.min(startIndex + visibleCount, items.length);
  
  const visibleItems = items.slice(startIndex, endIndex).map((item, index) => ({
    item,
    index: startIndex + index,
  }));

  const totalHeight = items.length * itemHeight;
  const offsetY = startIndex * itemHeight;

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  };

  return {
    visibleItems,
    totalHeight,
    offsetY,
    handleScroll,
  };
};

/**
 * 图片懒加载 Hook
 */
export const useLazyImage = (src: string, placeholder?: string) => {
  const [imageSrc, setImageSrc] = useState(placeholder || '');
  const [isLoaded, setIsLoaded] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setImageSrc(src);
          observer.disconnect();
        }
      },
      { threshold: 0.1 }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => observer.disconnect();
  }, [src]);

  const handleLoad = () => {
    setIsLoaded(true);
  };

  return {
    imgRef,
    imageSrc,
    isLoaded,
    handleLoad,
  };
};