import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';

// Custom render function that includes providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <BrowserRouter>
      <ConfigProvider locale={zhCN}>
        {children}
      </ConfigProvider>
    </BrowserRouter>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

// Re-export everything
export * from '@testing-library/react';

// Override render method
export { customRender as render };

// Test data factories
export const createMockUser = (overrides = {}) => ({
  id: '1',
  username: 'testuser',
  email: 'test@example.com',
  role: 'user',
  permissions: ['read'],
  created_at: new Date().toISOString(),
  last_login: new Date().toISOString(),
  ...overrides,
});

export const createMockAnalysis = (overrides = {}) => ({
  id: 'analysis-1',
  user_id: 'user-1',
  stock_code: '000001',
  market_type: 'CN',
  status: 'completed',
  progress: 100,
  config: {
    stock_code: '000001',
    market_type: 'CN',
    analysis_date: '2024-01-01',
    analysts: ['fundamentals'],
    llm_config: { model: 'gpt-4' },
  },
  result_data: {
    summary: 'Analysis complete',
    recommendations: ['买入'],
  },
  created_at: new Date().toISOString(),
  started_at: new Date().toISOString(),
  completed_at: new Date().toISOString(),
  error_message: null,
  ...overrides,
});

export const createMockAnalysisRequest = (overrides = {}) => ({
  stock_code: '000001',
  market_type: 'CN',
  analysis_date: '2024-01-01',
  analysts: ['fundamentals'],
  llm_config: { model: 'gpt-4' },
  ...overrides,
});

// Mock API response helpers
export const mockApiSuccess = (data: any) => ({
  status: 200,
  data,
});

export const mockApiError = (message: string, status = 400) => ({
  status,
  response: {
    status,
    data: { message },
  },
  message,
});

// Wait for async operations
export const waitForAsync = () => new Promise(resolve => setTimeout(resolve, 0));

// Mock localStorage
export const mockLocalStorage = () => {
  const store: Record<string, string> = {};
  
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      Object.keys(store).forEach(key => delete store[key]);
    }),
    get store() {
      return { ...store };
    },
  };
};

// Mock window.matchMedia
export const mockMatchMedia = () => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation(query => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
};

// Mock ResizeObserver
export const mockResizeObserver = () => {
  global.ResizeObserver = vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
  }));
};

// Mock IntersectionObserver
export const mockIntersectionObserver = () => {
  global.IntersectionObserver = vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
  }));
};

// Setup all mocks
export const setupTestMocks = () => {
  mockMatchMedia();
  mockResizeObserver();
  mockIntersectionObserver();
  
  // Mock HTMLCanvasElement.getContext
  HTMLCanvasElement.prototype.getContext = vi.fn();
  
  // Mock URL methods
  global.URL.createObjectURL = vi.fn();
  global.URL.revokeObjectURL = vi.fn();
};

// Cleanup function
export const cleanupTests = () => {
  vi.clearAllMocks();
  localStorage.clear();
};