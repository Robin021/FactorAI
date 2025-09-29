import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import AnalysisReport from './AnalysisReport';
import { useAnalysisStore } from '@/stores/analysisStore';
import { Analysis } from '@/types';

// Mock the analysis store
vi.mock('@/stores/analysisStore');
const mockUseAnalysisStore = vi.mocked(useAnalysisStore);

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ id: 'test-analysis-id' }),
    useNavigate: () => vi.fn(),
  };
});

// Mock ChartViewer component
vi.mock('@/components/Charts/ChartViewer', () => ({
  default: function MockChartViewer({ charts }: { charts: any }) {
    return <div data-testid="chart-viewer">Chart Viewer: {JSON.stringify(charts)}</div>;
  },
}));

const mockAnalysis: Analysis = {
  id: 'test-analysis-id',
  userId: 'test-user-id',
  stockCode: '000001',
  status: 'completed',
  progress: 100,
  createdAt: '2024-01-01T00:00:00Z',
  completedAt: '2024-01-01T01:00:00Z',
  resultData: {
    overallScore: 8.5,
    targetPrice: 15.50,
    recommendation: '买入',
    summary: '这是一个测试分析摘要',
    fundamentalAnalysis: {
      summary: '基本面分析摘要',
      keyMetrics: {
        pe: 15.2,
        pb: 1.8,
        roe: 12.5,
      },
      keyPoints: ['关键点1', '关键点2'],
      recommendations: ['建议1', '建议2'],
    },
    technicalAnalysis: {
      summary: '技术分析摘要',
      keyPoints: ['技术点1', '技术点2'],
    },
    charts: {
      priceChart: { type: 'line', data: [] },
      volumeChart: { type: 'bar', data: [] },
    },
  },
};

const mockAnalysisHistory: Analysis[] = [
  mockAnalysis,
  {
    ...mockAnalysis,
    id: 'test-analysis-id-2',
    stockCode: '000002',
    createdAt: '2024-01-02T00:00:00Z',
  },
];

const defaultMockStore = {
  currentAnalysis: mockAnalysis,
  analysisHistory: mockAnalysisHistory,
  isLoading: false,
  error: null,
  getAnalysisResult: vi.fn(),
  loadAnalysisHistory: vi.fn(),
};

const renderComponent = (storeOverrides = {}) => {
  mockUseAnalysisStore.mockReturnValue({
    ...defaultMockStore,
    ...storeOverrides,
  });

  return render(
    <BrowserRouter>
      <ConfigProvider>
        <AnalysisReport />
      </ConfigProvider>
    </BrowserRouter>
  );
};

describe('AnalysisReport', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state correctly', () => {
    renderComponent({ isLoading: true, currentAnalysis: null });
    
    expect(screen.getByText('正在加载分析报告...')).toBeInTheDocument();
  });

  it('renders error state correctly', () => {
    renderComponent({ 
      isLoading: false, 
      currentAnalysis: null, 
      error: '加载失败' 
    });
    
    expect(screen.getByText('加载失败')).toBeInTheDocument();
    expect(screen.getByText('重试')).toBeInTheDocument();
  });

  it('renders empty state when no analysis found', () => {
    renderComponent({ currentAnalysis: null, error: null });
    
    expect(screen.getByText('未找到分析报告')).toBeInTheDocument();
    expect(screen.getByText('返回分析页面')).toBeInTheDocument();
  });

  it('renders analysis report correctly', () => {
    renderComponent();
    
    // Check header
    expect(screen.getByText('000001 分析报告')).toBeInTheDocument();
    
    // Check overview stats
    expect(screen.getByText('8.5/10')).toBeInTheDocument();
    expect(screen.getByText('¥15.50')).toBeInTheDocument();
    expect(screen.getByText('买入')).toBeInTheDocument();
    
    // Check summary
    expect(screen.getByText('这是一个测试分析摘要')).toBeInTheDocument();
    
    // Check basic info
    expect(screen.getByText('000001')).toBeInTheDocument();
    expect(screen.getByText('已完成')).toBeInTheDocument();
  });

  it('switches between tabs correctly', async () => {
    renderComponent();
    
    // Initially on overview tab
    expect(screen.getByText('综合评分')).toBeInTheDocument();
    
    // Click on fundamental analysis tab
    const fundamentalTab = screen.getByText('基本面分析');
    fireEvent.click(fundamentalTab);
    
    await waitFor(() => {
      expect(screen.getByText('基本面分析摘要')).toBeInTheDocument();
      expect(screen.getByText('关键点1')).toBeInTheDocument();
    });
  });

  it('handles print functionality', () => {
    const mockPrint = vi.fn();
    Object.defineProperty(window, 'print', {
      value: mockPrint,
      writable: true,
    });

    renderComponent();
    
    const printButton = screen.getByText('打印');
    fireEvent.click(printButton);
    
    expect(mockPrint).toHaveBeenCalled();
  });

  it('opens history modal correctly', async () => {
    renderComponent();
    
    const historyButton = screen.getByText('历史记录');
    fireEvent.click(historyButton);
    
    await waitFor(() => {
      expect(screen.getByText('历史分析记录')).toBeInTheDocument();
      expect(screen.getByText('000002')).toBeInTheDocument();
    });
  });

  it('handles export functionality', async () => {
    renderComponent();
    
    // Click export dropdown
    const exportButton = screen.getByText('导出');
    fireEvent.click(exportButton);
    
    // Should show export options in dropdown
    // Note: This would require more complex testing for dropdown menus
  });

  it('handles share functionality', async () => {
    renderComponent();
    
    // Click share dropdown
    const shareButton = screen.getByText('分享');
    fireEvent.click(shareButton);
    
    // Should show share options in dropdown
    // Note: This would require more complex testing for dropdown menus
  });

  it('calls getAnalysisResult on mount', () => {
    const mockGetAnalysisResult = vi.fn();
    renderComponent({ getAnalysisResult: mockGetAnalysisResult });
    
    expect(mockGetAnalysisResult).toHaveBeenCalledWith('test-analysis-id');
  });

  it('calls loadAnalysisHistory on mount', () => {
    const mockLoadAnalysisHistory = vi.fn();
    renderComponent({ loadAnalysisHistory: mockLoadAnalysisHistory });
    
    expect(mockLoadAnalysisHistory).toHaveBeenCalled();
  });

  it('renders chart viewer when charts data is available', () => {
    renderComponent();
    
    // Switch to technical analysis tab which should have charts
    const technicalTab = screen.getByText('技术分析');
    fireEvent.click(technicalTab);
    
    // Chart viewer should be rendered (mocked)
    expect(screen.getByTestId('chart-viewer')).toBeInTheDocument();
  });

  it('handles back navigation correctly', () => {
    const mockNavigate = vi.fn();
    vi.doMock('react-router-dom', async () => {
      const actual = await vi.importActual('react-router-dom');
      return {
        ...actual,
        useNavigate: () => mockNavigate,
        useParams: () => ({ id: 'test-analysis-id' }),
      };
    });

    renderComponent();
    
    const backButton = screen.getByText('返回');
    fireEvent.click(backButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('/analysis');
  });

  it('displays correct status colors and texts', () => {
    renderComponent();
    
    // Check that completed status shows with success color
    const statusTag = screen.getByText('已完成');
    expect(statusTag).toBeInTheDocument();
    expect(statusTag.closest('.ant-tag')).toHaveClass('ant-tag-success');
  });

  it('handles missing result data gracefully', () => {
    const analysisWithoutResult = {
      ...mockAnalysis,
      resultData: undefined,
    };
    
    renderComponent({ currentAnalysis: analysisWithoutResult });
    
    // Should still render basic info
    expect(screen.getByText('000001 分析报告')).toBeInTheDocument();
    
    // Should show N/A for missing data
    expect(screen.getAllByText('N/A')).toHaveLength(3); // Score, price, recommendation
  });
});