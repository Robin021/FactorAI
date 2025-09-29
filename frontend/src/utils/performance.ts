/**
 * 前端性能监控和优化工具
 */

// 性能指标接口
export interface PerformanceMetrics {
  loadTime: number;
  domContentLoaded: number;
  firstContentfulPaint: number;
  largestContentfulPaint: number;
  firstInputDelay: number;
  cumulativeLayoutShift: number;
  memoryUsage?: number;
}

// 性能监控类
export class PerformanceMonitor {
  private metrics: Partial<PerformanceMetrics> = {};
  private observers: PerformanceObserver[] = [];

  constructor() {
    this.initializeObservers();
    this.measureBasicMetrics();
  }

  /**
   * 初始化性能观察器
   */
  private initializeObservers(): void {
    // 观察 LCP (Largest Contentful Paint)
    if ('PerformanceObserver' in window) {
      try {
        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1] as any;
          this.metrics.largestContentfulPaint = lastEntry.startTime;
        });
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
        this.observers.push(lcpObserver);
      } catch (e) {
        console.warn('LCP observer not supported');
      }

      // 观察 FID (First Input Delay)
      try {
        const fidObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry: any) => {
            this.metrics.firstInputDelay = entry.processingStart - entry.startTime;
          });
        });
        fidObserver.observe({ entryTypes: ['first-input'] });
        this.observers.push(fidObserver);
      } catch (e) {
        console.warn('FID observer not supported');
      }

      // 观察 CLS (Cumulative Layout Shift)
      try {
        let clsValue = 0;
        const clsObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry: any) => {
            if (!entry.hadRecentInput) {
              clsValue += entry.value;
            }
          });
          this.metrics.cumulativeLayoutShift = clsValue;
        });
        clsObserver.observe({ entryTypes: ['layout-shift'] });
        this.observers.push(clsObserver);
      } catch (e) {
        console.warn('CLS observer not supported');
      }
    }
  }

  /**
   * 测量基础性能指标
   */
  private measureBasicMetrics(): void {
    // 等待页面加载完成
    if (document.readyState === 'complete') {
      this.collectBasicMetrics();
    } else {
      window.addEventListener('load', () => {
        this.collectBasicMetrics();
      });
    }
  }

  /**
   * 收集基础性能指标
   */
  private collectBasicMetrics(): void {
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    
    if (navigation) {
      this.metrics.loadTime = navigation.loadEventEnd - navigation.fetchStart;
      this.metrics.domContentLoaded = navigation.domContentLoadedEventEnd - navigation.fetchStart;
    }

    // FCP (First Contentful Paint)
    const paintEntries = performance.getEntriesByType('paint');
    const fcpEntry = paintEntries.find(entry => entry.name === 'first-contentful-paint');
    if (fcpEntry) {
      this.metrics.firstContentfulPaint = fcpEntry.startTime;
    }

    // 内存使用情况 (如果支持)
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      this.metrics.memoryUsage = memory.usedJSHeapSize / 1024 / 1024; // MB
    }
  }

  /**
   * 获取性能指标
   */
  public getMetrics(): PerformanceMetrics {
    return this.metrics as PerformanceMetrics;
  }

  /**
   * 发送性能数据到后端
   */
  public async reportMetrics(): Promise<void> {
    try {
      const metrics = this.getMetrics();
      
      // 发送到后端API
      await fetch('/api/v1/performance/metrics', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...metrics,
          timestamp: Date.now(),
          userAgent: navigator.userAgent,
          url: window.location.href,
        }),
      });
    } catch (error) {
      console.warn('Failed to report performance metrics:', error);
    }
  }

  /**
   * 清理观察器
   */
  public cleanup(): void {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
  }
}

// 资源加载优化工具
export class ResourceOptimizer {
  /**
   * 预加载关键资源
   */
  public static preloadCriticalResources(): void {
    const criticalResources = [
      '/api/v1/config/llm',
      '/api/v1/auth/me',
    ];

    criticalResources.forEach(url => {
      const link = document.createElement('link');
      link.rel = 'prefetch';
      link.href = url;
      document.head.appendChild(link);
    });
  }

  /**
   * 懒加载图片
   */
  public static setupLazyLoading(): void {
    if ('IntersectionObserver' in window) {
      const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const img = entry.target as HTMLImageElement;
            if (img.dataset.src) {
              img.src = img.dataset.src;
              img.removeAttribute('data-src');
              imageObserver.unobserve(img);
            }
          }
        });
      });

      // 观察所有带有 data-src 的图片
      document.querySelectorAll('img[data-src]').forEach(img => {
        imageObserver.observe(img);
      });
    }
  }

  /**
   * 优化字体加载
   */
  public static optimizeFontLoading(): void {
    // 预加载关键字体
    const fontLink = document.createElement('link');
    fontLink.rel = 'preload';
    fontLink.href = '/fonts/main.woff2';
    fontLink.as = 'font';
    fontLink.type = 'font/woff2';
    fontLink.crossOrigin = 'anonymous';
    document.head.appendChild(fontLink);
  }
}

// 渲染性能优化
export class RenderOptimizer {
  /**
   * 防抖函数
   */
  public static debounce<T extends (...args: any[]) => any>(
    func: T,
    wait: number
  ): (...args: Parameters<T>) => void {
    let timeout: NodeJS.Timeout;
    return (...args: Parameters<T>) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(this, args), wait);
    };
  }

  /**
   * 节流函数
   */
  public static throttle<T extends (...args: any[]) => any>(
    func: T,
    limit: number
  ): (...args: Parameters<T>) => void {
    let inThrottle: boolean;
    return (...args: Parameters<T>) => {
      if (!inThrottle) {
        func.apply(this, args);
        inThrottle = true;
        setTimeout(() => (inThrottle = false), limit);
      }
    };
  }

  /**
   * 虚拟滚动优化
   */
  public static createVirtualScroller(
    container: HTMLElement,
    itemHeight: number,
    items: any[],
    renderItem: (item: any, index: number) => HTMLElement
  ): void {
    const containerHeight = container.clientHeight;
    const visibleCount = Math.ceil(containerHeight / itemHeight) + 2;
    let scrollTop = 0;

    const updateVisibleItems = () => {
      const startIndex = Math.floor(scrollTop / itemHeight);
      const endIndex = Math.min(startIndex + visibleCount, items.length);

      // 清空容器
      container.innerHTML = '';

      // 创建占位符
      const spacerTop = document.createElement('div');
      spacerTop.style.height = `${startIndex * itemHeight}px`;
      container.appendChild(spacerTop);

      // 渲染可见项
      for (let i = startIndex; i < endIndex; i++) {
        const itemElement = renderItem(items[i], i);
        container.appendChild(itemElement);
      }

      // 创建底部占位符
      const spacerBottom = document.createElement('div');
      spacerBottom.style.height = `${(items.length - endIndex) * itemHeight}px`;
      container.appendChild(spacerBottom);
    };

    // 监听滚动事件
    const handleScroll = this.throttle(() => {
      scrollTop = container.scrollTop;
      updateVisibleItems();
    }, 16); // 60fps

    container.addEventListener('scroll', handleScroll);
    updateVisibleItems();
  }
}

// 内存优化工具
export class MemoryOptimizer {
  private static weakMapCache = new WeakMap();

  /**
   * 使用 WeakMap 缓存
   */
  public static cacheWithWeakMap<T extends object, U>(
    key: T,
    factory: () => U
  ): U {
    if (this.weakMapCache.has(key)) {
      return this.weakMapCache.get(key);
    }
    
    const value = factory();
    this.weakMapCache.set(key, value);
    return value;
  }

  /**
   * 清理未使用的事件监听器
   */
  public static cleanupEventListeners(element: HTMLElement): void {
    const clone = element.cloneNode(true);
    element.parentNode?.replaceChild(clone, element);
  }

  /**
   * 监控内存使用情况
   */
  public static monitorMemoryUsage(): void {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      const used = memory.usedJSHeapSize / 1024 / 1024;
      const total = memory.totalJSHeapSize / 1024 / 1024;
      
      console.log(`Memory usage: ${used.toFixed(2)}MB / ${total.toFixed(2)}MB`);
      
      // 如果内存使用超过阈值，触发警告
      if (used > 100) { // 100MB
        console.warn('High memory usage detected');
      }
    }
  }
}

// 全局性能监控实例
export const performanceMonitor = new PerformanceMonitor();

// 页面卸载时清理和报告
window.addEventListener('beforeunload', () => {
  performanceMonitor.reportMetrics();
  performanceMonitor.cleanup();
});

// 初始化优化
document.addEventListener('DOMContentLoaded', () => {
  ResourceOptimizer.preloadCriticalResources();
  ResourceOptimizer.setupLazyLoading();
  ResourceOptimizer.optimizeFontLoading();
});

// 定期监控内存使用
setInterval(() => {
  MemoryOptimizer.monitorMemoryUsage();
}, 30000); // 每30秒检查一次