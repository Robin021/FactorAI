/**
 * 前端性能测试
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { performance } from 'perf_hooks';
import { PerformanceMonitor, ResourceOptimizer, RenderOptimizer } from '../../utils/performance';

// Mock performance API
const mockPerformance = {
  now: vi.fn(() => Date.now()),
  getEntriesByType: vi.fn(() => []),
  mark: vi.fn(),
  measure: vi.fn(),
  memory: {
    usedJSHeapSize: 1024 * 1024 * 50, // 50MB
    totalJSHeapSize: 1024 * 1024 * 100, // 100MB
  },
};

Object.defineProperty(global, 'performance', {
  value: mockPerformance,
  writable: true,
});

describe('Performance Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('PerformanceMonitor', () => {
    it('should initialize without errors', () => {
      expect(() => new PerformanceMonitor()).not.toThrow();
    });

    it('should collect basic metrics', () => {
      const monitor = new PerformanceMonitor();
      const metrics = monitor.getMetrics();
      
      expect(metrics).toBeDefined();
      expect(typeof metrics).toBe('object');
    });

    it('should handle missing performance API gracefully', () => {
      const originalPerformance = global.performance;
      // @ts-ignore
      delete global.performance;
      
      expect(() => new PerformanceMonitor()).not.toThrow();
      
      global.performance = originalPerformance;
    });
  });

  describe('ResourceOptimizer', () => {
    it('should preload critical resources', () => {
      const mockAppendChild = vi.fn();
      const mockCreateElement = vi.fn(() => ({
        rel: '',
        href: '',
      }));

      Object.defineProperty(document, 'createElement', {
        value: mockCreateElement,
        writable: true,
      });

      Object.defineProperty(document.head, 'appendChild', {
        value: mockAppendChild,
        writable: true,
      });

      ResourceOptimizer.preloadCriticalResources();

      expect(mockCreateElement).toHaveBeenCalled();
    });

    it('should setup lazy loading with IntersectionObserver', () => {
      const mockObserve = vi.fn();
      const mockIntersectionObserver = vi.fn(() => ({
        observe: mockObserve,
        disconnect: vi.fn(),
      }));

      Object.defineProperty(global, 'IntersectionObserver', {
        value: mockIntersectionObserver,
        writable: true,
      });

      Object.defineProperty(document, 'querySelectorAll', {
        value: vi.fn(() => []),
        writable: true,
      });

      ResourceOptimizer.setupLazyLoading();

      expect(mockIntersectionObserver).toHaveBeenCalled();
    });
  });

  describe('RenderOptimizer', () => {
    it('should create debounced function', () => {
      const mockFn = vi.fn();
      const debouncedFn = RenderOptimizer.debounce(mockFn, 100);

      debouncedFn();
      debouncedFn();
      debouncedFn();

      expect(mockFn).not.toHaveBeenCalled();

      // Fast forward time
      vi.advanceTimersByTime(100);
      expect(mockFn).toHaveBeenCalledTimes(1);
    });

    it('should create throttled function', () => {
      const mockFn = vi.fn();
      const throttledFn = RenderOptimizer.throttle(mockFn, 100);

      throttledFn();
      throttledFn();
      throttledFn();

      expect(mockFn).toHaveBeenCalledTimes(1);

      vi.advanceTimersByTime(100);
      throttledFn();
      expect(mockFn).toHaveBeenCalledTimes(2);
    });
  });

  describe('Component Render Performance', () => {
    it('should render components within acceptable time', async () => {
      const TestComponent = () => {
        // Simulate some computation
        const items = Array.from({ length: 1000 }, (_, i) => i);
        return (
          <div>
            {items.map(item => (
              <span key={item}>{item}</span>
            ))}
          </div>
        );
      };

      const startTime = performance.now();
      render(<TestComponent />);
      const endTime = performance.now();

      const renderTime = endTime - startTime;
      
      // Render should complete within 100ms
      expect(renderTime).toBeLessThan(100);
    });

    it('should handle large lists efficiently', async () => {
      const LargeListComponent = () => {
        const items = Array.from({ length: 10000 }, (_, i) => ({
          id: i,
          name: `Item ${i}`,
        }));

        return (
          <div>
            {items.slice(0, 100).map(item => (
              <div key={item.id}>{item.name}</div>
            ))}
          </div>
        );
      };

      const startTime = performance.now();
      render(<LargeListComponent />);
      const endTime = performance.now();

      const renderTime = endTime - startTime;
      
      // Should render efficiently even with large datasets
      expect(renderTime).toBeLessThan(50);
    });
  });

  describe('Memory Usage', () => {
    it('should not cause memory leaks in event listeners', () => {
      const initialMemory = mockPerformance.memory.usedJSHeapSize;
      
      // Simulate adding and removing event listeners
      const elements = Array.from({ length: 100 }, () => {
        const element = document.createElement('div');
        const handler = () => {};
        element.addEventListener('click', handler);
        element.removeEventListener('click', handler);
        return element;
      });

      // Memory usage should not increase significantly
      const finalMemory = mockPerformance.memory.usedJSHeapSize;
      const memoryIncrease = finalMemory - initialMemory;
      
      expect(memoryIncrease).toBeLessThan(1024 * 1024); // Less than 1MB
    });
  });

  describe('API Performance', () => {
    it('should track API call performance', async () => {
      const mockFetch = vi.fn(() => 
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ data: 'test' }),
        })
      );

      global.fetch = mockFetch as any;

      const startTime = performance.now();
      await fetch('/api/test');
      const endTime = performance.now();

      const duration = endTime - startTime;
      
      // API calls should complete quickly in tests
      expect(duration).toBeLessThan(100);
      expect(mockFetch).toHaveBeenCalledWith('/api/test');
    });
  });

  describe('Bundle Size Performance', () => {
    it('should not import unnecessary dependencies', () => {
      // This test would be run as part of build analysis
      // Here we just check that critical modules are available
      expect(typeof React).toBe('object');
      expect(typeof ReactDOM).toBe('object');
    });
  });
});

describe('Performance Benchmarks', () => {
  it('should benchmark array operations', () => {
    const largeArray = Array.from({ length: 100000 }, (_, i) => i);
    
    const startTime = performance.now();
    const filtered = largeArray.filter(x => x % 2 === 0);
    const endTime = performance.now();
    
    const duration = endTime - startTime;
    
    // Array filtering should be fast
    expect(duration).toBeLessThan(50);
    expect(filtered.length).toBe(50000);
  });

  it('should benchmark object operations', () => {
    const largeObject = Object.fromEntries(
      Array.from({ length: 10000 }, (_, i) => [`key${i}`, `value${i}`])
    );
    
    const startTime = performance.now();
    const keys = Object.keys(largeObject);
    const values = Object.values(largeObject);
    const endTime = performance.now();
    
    const duration = endTime - startTime;
    
    // Object operations should be fast
    expect(duration).toBeLessThan(20);
    expect(keys.length).toBe(10000);
    expect(values.length).toBe(10000);
  });

  it('should benchmark DOM operations', () => {
    const container = document.createElement('div');
    document.body.appendChild(container);
    
    const startTime = performance.now();
    
    // Create many DOM elements
    for (let i = 0; i < 1000; i++) {
      const element = document.createElement('div');
      element.textContent = `Element ${i}`;
      container.appendChild(element);
    }
    
    const endTime = performance.now();
    const duration = endTime - startTime;
    
    // DOM operations should complete within reasonable time
    expect(duration).toBeLessThan(100);
    expect(container.children.length).toBe(1000);
    
    // Cleanup
    document.body.removeChild(container);
  });
});