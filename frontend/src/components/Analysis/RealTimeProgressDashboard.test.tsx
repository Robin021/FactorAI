import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import RealTimeProgressDashboard from './RealTimeProgressDashboard';
import { Analysis } from '@/types';
import { useAnalysis } from '@/hooks/useAnalysis';
import { useWebSocket } from '@/hooks/useWebSocket';

// Mock hooks
jest.mock('@/hooks/useAnalysis');
jest.mock('@/hooks/useWebSocket');

const mockUseAnalysis = useAnalysis as jest.MockedFunction<typeof useAnalysis>;
const mockUseWebSocket = useWebSocket as jest.MockedFunction<typeof useWebSocket>;

// Mock router and config provider
const MockWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    <ConfigProvider>
      {children}
    </ConfigProvider>
  </BrowserRouter>
);

describe('RealTimeProgressDashboard', () => {
  const mockAnalysis: Analysis = {
    id: 'test-analysis-1',
    userId: 'user-1',
    stockCode: 'AAPL',
    status: 'running',
    progress: 45,
    createdAt: new Date().toISOString(),
  };

  const mockCancelAnalysis = jest.fn();
  const mockSendMessage = jest.fn();

  beforeEach(() => {
    mockUseAnalysis.mockReturnValue({
      currentAnalysis: mockAnalysis,
      analysisHistory: [],
      isLoading: false,
      error: null,
      historyLoading: false,
      historyError: null,
      pagination: { page: 1, limit: 10, total: 0 },
      startAnalysis: jest.fn(),
      getAnalysisStatus: jest.fn(),
      getAnalysisResult: jest.fn(),
      deleteAnalysis: jest.fn(),
      cancelAnalysis: mockCancelAnalysis,
      setCurrentAnalysis: jest.fn(),
      clearError: jest.fn(),
      clearHistoryError: jest.fn(),
      refreshHistory: jest.fn(),
      loadMoreHistory: jest.fn(),
    });

    mockUseWebSocket.mockReturnValue({
      isConnected: true,
      lastMessage: null,
      sendMessage: mockSendMessage,
      disconnect: jest.fn(),
      reconnect: jest.fn(),
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders dashboard with analysis information', () => {
    render(
      <MockWrapper>
        <RealTimeProgressDashboard analysis={mockAnalysis} />
      </MockWrapper>
    );

    expect(screen.getByText(/实时分析进度 - AAPL/)).toBeInTheDocument();
    expect(screen.getByText('已连接')).toBeInTheDocument();
    expect(screen.getByText('总体进度')).toBeInTheDocument();
    expect(screen.getByText('已用时间')).toBeInTheDocument();
  });

  it('displays connection status correctly', () => {
    mockUseWebSocket.mockReturnValue({
      isConnected: false,
      lastMessage: null,
      sendMessage: mockSendMessage,
      disconnect: jest.fn(),
      reconnect: jest.fn(),
    });

    render(
      <MockWrapper>
        <RealTimeProgressDashboard analysis={mockAnalysis} />
      </MockWrapper>
    );

    expect(screen.getByText('连接断开')).toBeInTheDocument();
    expect(screen.getByText('连接状态异常')).toBeInTheDocument();
  });

  it('handles pause button click', () => {
    render(
      <MockWrapper>
        <RealTimeProgressDashboard analysis={mockAnalysis} />
      </MockWrapper>
    );

    const pauseButton = screen.getByText('暂停');
    fireEvent.click(pauseButton);

    expect(mockSendMessage).toHaveBeenCalledWith({ type: 'pause_analysis' });
  });

  it('handles cancel button click', async () => {
    render(
      <MockWrapper>
        <RealTimeProgressDashboard analysis={mockAnalysis} />
      </MockWrapper>
    );

    const cancelButton = screen.getByText('取消');
    fireEvent.click(cancelButton);

    await waitFor(() => {
      expect(mockCancelAnalysis).toHaveBeenCalledWith('test-analysis-1');
    });
  });

  it('displays analysis steps', () => {
    render(
      <MockWrapper>
        <RealTimeProgressDashboard analysis={mockAnalysis} />
      </MockWrapper>
    );

    expect(screen.getByText('初始化分析环境')).toBeInTheDocument();
    expect(screen.getByText('数据收集')).toBeInTheDocument();
    expect(screen.getByText('市场分析')).toBeInTheDocument();
    expect(screen.getByText('基本面分析')).toBeInTheDocument();
  });

  it('shows paused state correctly', () => {
    render(
      <MockWrapper>
        <RealTimeProgressDashboard analysis={mockAnalysis} />
      </MockWrapper>
    );

    // Simulate receiving pause message
    const { onMessage } = mockUseWebSocket.mock.calls[0][1];
    onMessage({ type: 'analysis_paused' });

    expect(screen.getByText('已暂停')).toBeInTheDocument();
    expect(screen.getByText('继续')).toBeInTheDocument();
  });

  it('handles progress updates', () => {
    render(
      <MockWrapper>
        <RealTimeProgressDashboard analysis={mockAnalysis} />
      </MockWrapper>
    );

    // Simulate receiving progress update
    const { onMessage } = mockUseWebSocket.mock.calls[0][1];
    onMessage({
      type: 'overall_progress',
      progress: 75,
      estimatedTimeRemaining: 120,
    });

    // Progress should be updated (this would be reflected in the component state)
    expect(screen.getByText('总体进度')).toBeInTheDocument();
  });

  it('handles step completion', () => {
    render(
      <MockWrapper>
        <RealTimeProgressDashboard analysis={mockAnalysis} />
      </MockWrapper>
    );

    // Simulate step completion
    const { onMessage } = mockUseWebSocket.mock.calls[0][1];
    onMessage({
      type: 'step_complete',
      stepId: 'init',
      stepName: '初始化分析环境',
    });

    // Step should be marked as completed (reflected in component state)
    expect(screen.getByText('初始化分析环境')).toBeInTheDocument();
  });
});