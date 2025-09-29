import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import Analysis from '../index';
import { useAnalysis } from '@/hooks/useAnalysis';
import { Analysis as AnalysisType } from '@/types';

// Mock the useAnalysis hook
vi.mock('@/hooks/useAnalysis');
const mockUseAnalysis = useAnalysis as any;

// Mock child components
vi.mock('@/components/Analysis/AnalysisForm', () => ({
  default: () => <div data-testid="analysis-form">Analysis Form</div>
}));

vi.mock('@/components/Analysis/RealTimeProgressDashboard', () => ({
  default: ({ analysis, onComplete, onError, onCancel }: any) => (
    <div data-testid="progress-dashboard">
      <div>Progress Dashboard</div>
      <div>Analysis ID: {analysis?.id}</div>
      <button onClick={onComplete}>Complete</button>
      <button onClick={() => onError('Test error')}>Error</button>
      <button onClick={onCancel}>Cancel</button>
    </div>
  )
}));

vi.mock('@/components/Analysis/AnalysisResults', () => ({
  default: ({ analysis }: { analysis: AnalysisType | null }) => (
    <div data-testid="analysis-results">
      {analysis ? `Analysis Results: ${analysis.id}` : 'No Analysis'}
    </div>
  )
}));

// Mock router wrapper
const MockRouter = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    <ConfigProvider>
      {children}
    </ConfigProvider>
  </BrowserRouter>
);

describe('Analysis Component', () => {
  const mockRunningAnalysis: AnalysisType = {
    id: 'analysis-1',
    user_id: 'user-1',
    stock_code: '000001',
    market_type: 'CN',
    status: 'running',
    progress: 50,
    config: {
      stock_code: '000001',
      market_type: 'CN',
      analysis_date: '2024-01-01',
      analysts: ['fundamentals'],
      llm_config: { model: 'gpt-4' },
    },
    result_data: null,
    created_at: new Date().toISOString(),
    started_at: new Date().toISOString(),
    completed_at: null,
    error_message: null,
  };

  const mockCompletedAnalysis: AnalysisType = {
    ...mockRunningAnalysis,
    id: 'analysis-2',
    status: 'completed',
    progress: 100,
    completed_at: new Date().toISOString(),
    result_data: { summary: 'Analysis complete' },
  };

  beforeEach(() => {
    mockUseAnalysis.mockReturnValue({
      currentAnalysis: null,
      analysisHistory: [],
      isLoading: false,
      error: null,
      startAnalysis: vi.fn(),
      getAnalysisStatus: vi.fn(),
      loadAnalysisHistory: vi.fn(),
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders analysis page with correct title', () => {
    render(
      <MockRouter>
        <Analysis />
      </MockRouter>
    );

    expect(screen.getByText('股票分析平台')).toBeInTheDocument();
  });

  it('renders all tabs correctly', () => {
    render(
      <MockRouter>
        <Analysis />
      </MockRouter>
    );

    expect(screen.getByText('分析与结果')).toBeInTheDocument();
    expect(screen.getByText('实时进度')).toBeInTheDocument();
    expect(screen.getByText('历史记录')).toBeInTheDocument();
  });

  it('shows analysis form and results in analysis tab', () => {
    render(
      <MockRouter>
        <Analysis />
      </MockRouter>
    );

    expect(screen.getByTestId('analysis-form')).toBeInTheDocument();
    expect(screen.getByTestId('analysis-results')).toBeInTheDocument();
  });

  it('switches to progress tab when analysis starts', async () => {
    const { rerender } = render(
      <MockRouter>
        <Analysis />
      </MockRouter>
    );

    // Initially on analysis tab
    expect(screen.getByTestId('analysis-form')).toBeInTheDocument();

    // Update with running analysis
    mockUseAnalysis.mockReturnValue({
      currentAnalysis: mockRunningAnalysis,
      analysisHistory: [],
      isLoading: false,
      error: null,
      startAnalysis: vi.fn(),
      getAnalysisStatus: vi.fn(),
      loadAnalysisHistory: vi.fn(),
    });

    rerender(
      <MockRouter>
        <Analysis />
      </MockRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('progress-dashboard')).toBeInTheDocument();
    });
  });

  it('shows progress indicator when analysis is running', () => {
    mockUseAnalysis.mockReturnValue({
      currentAnalysis: mockRunningAnalysis,
      analysisHistory: [],
      isLoading: false,
      error: null,
      startAnalysis: vi.fn(),
      getAnalysisStatus: vi.fn(),
      loadAnalysisHistory: vi.fn(),
    });

    render(
      <MockRouter>
        <Analysis />
      </MockRouter>
    );

    const progressIndicator = document.querySelector('.progress-indicator');
    expect(progressIndicator).toBeInTheDocument();
  });

  it('shows no progress message when no analysis is running', () => {
    render(
      <MockRouter>
        <Analysis />
      </MockRouter>
    );

    // Click on progress tab
    fireEvent.click(screen.getByText('实时进度'));

    expect(screen.getByText('暂无进行中的分析任务')).toBeInTheDocument();
    expect(screen.getByText('请先在分析页面开始一个新的分析任务')).toBeInTheDocument();
  });

  it('shows progress dashboard when analysis is running', () => {
    mockUseAnalysis.mockReturnValue({
      currentAnalysis: mockRunningAnalysis,
      analysisHistory: [],
      isLoading: false,
      error: null,
      startAnalysis: vi.fn(),
      getAnalysisStatus: vi.fn(),
      loadAnalysisHistory: vi.fn(),
    });

    render(
      <MockRouter>
        <Analysis />
      </MockRouter>
    );

    // Should auto-switch to progress tab
    expect(screen.getByTestId('progress-dashboard')).toBeInTheDocument();
    expect(screen.getByText('Analysis ID: analysis-1')).toBeInTheDocument();
  });

  it('handles progress dashboard callbacks', async () => {
    mockUseAnalysis.mockReturnValue({
      currentAnalysis: mockRunningAnalysis,
      analysisHistory: [],
      isLoading: false,
      error: null,
      startAnalysis: vi.fn(),
      getAnalysisStatus: vi.fn(),
      loadAnalysisHistory: vi.fn(),
    });

    render(
      <MockRouter>
        <Analysis />
      </MockRouter>
    );

    // Should be on progress tab initially
    expect(screen.getByTestId('progress-dashboard')).toBeInTheDocument();

    // Test complete callback
    fireEvent.click(screen.getByText('Complete'));
    await waitFor(() => {
      expect(screen.getByTestId('analysis-form')).toBeInTheDocument();
    });

    // Switch back to progress tab to test other callbacks
    fireEvent.click(screen.getByText('实时进度'));
    
    // Test error callback
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    fireEvent.click(screen.getByText('Error'));
    expect(consoleSpy).toHaveBeenCalledWith('Analysis error:', 'Test error');
    
    // Test cancel callback
    fireEvent.click(screen.getByText('Cancel'));
    await waitFor(() => {
      expect(screen.getByTestId('analysis-form')).toBeInTheDocument();
    });

    consoleSpy.mockRestore();
  });

  it('shows analysis history when available', () => {
    mockUseAnalysis.mockReturnValue({
      currentAnalysis: null,
      analysisHistory: [mockCompletedAnalysis],
      isLoading: false,
      error: null,
      startAnalysis: vi.fn(),
      getAnalysisStatus: vi.fn(),
      loadAnalysisHistory: vi.fn(),
    });

    render(
      <MockRouter>
        <Analysis />
      </MockRouter>
    );

    // Click on history tab
    fireEvent.click(screen.getByText('历史记录'));

    expect(screen.getByText('分析历史')).toBeInTheDocument();
    expect(screen.getByText('Analysis Results: analysis-2')).toBeInTheDocument();
  });

  it('shows no history message when history is empty', () => {
    render(
      <MockRouter>
        <Analysis />
      </MockRouter>
    );

    // Click on history tab
    fireEvent.click(screen.getByText('历史记录'));

    expect(screen.getByText('暂无历史分析记录')).toBeInTheDocument();
  });

  it('allows manual tab switching', () => {
    render(
      <MockRouter>
        <Analysis />
      </MockRouter>
    );

    // Start on analysis tab
    expect(screen.getByTestId('analysis-form')).toBeInTheDocument();

    // Switch to progress tab
    fireEvent.click(screen.getByText('实时进度'));
    expect(screen.getByText('暂无进行中的分析任务')).toBeInTheDocument();

    // Switch to history tab
    fireEvent.click(screen.getByText('历史记录'));
    expect(screen.getByText('分析历史')).toBeInTheDocument();

    // Switch back to analysis tab
    fireEvent.click(screen.getByText('分析与结果'));
    expect(screen.getByTestId('analysis-form')).toBeInTheDocument();
  });
});