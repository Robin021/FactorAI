import { renderHook, act } from '@testing-library/react';
import { useAnalysisStore } from '../analysisStore';
import { analysisService } from '@/services/analysis';
import { Analysis, AnalysisRequest } from '@/types';
import { vi } from 'vitest';
import { vi } from 'vitest';

// Mock the analysis service
vi.mock('@/services/analysis');
const mockAnalysisService = analysisService as any;

describe('AnalysisStore', () => {
  const mockAnalysisRequest: AnalysisRequest = {
    stock_code: '000001',
    market_type: 'CN',
    analysis_date: '2024-01-01',
    analysts: ['fundamentals', 'technical'],
    llm_config: { model: 'gpt-4' },
  };

  const mockAnalysis: Analysis = {
    id: 'analysis-1',
    user_id: 'user-1',
    stock_code: '000001',
    market_type: 'CN',
    status: 'running',
    progress: 50,
    config: mockAnalysisRequest,
    result_data: null,
    created_at: new Date().toISOString(),
    started_at: new Date().toISOString(),
    completed_at: null,
    error_message: null,
  };

  const mockAnalysisHistory = [
    { ...mockAnalysis, id: 'analysis-1', status: 'completed' as const },
    { ...mockAnalysis, id: 'analysis-2', status: 'failed' as const },
  ];

  beforeEach(() => {
    // Reset store state
    useAnalysisStore.setState({
      currentAnalysis: null,
      analysisHistory: [],
      isLoading: false,
      error: null,
      historyLoading: false,
      historyError: null,
      pagination: {
        page: 1,
        limit: 20,
        total: 0,
      },
    });

    // Reset mocks
    vi.clearAllMocks();
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const { result } = renderHook(() => useAnalysisStore());

      expect(result.current.currentAnalysis).toBeNull();
      expect(result.current.analysisHistory).toEqual([]);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.historyLoading).toBe(false);
      expect(result.current.historyError).toBeNull();
      expect(result.current.pagination).toEqual({
        page: 1,
        limit: 20,
        total: 0,
      });
    });
  });

  describe('Start Analysis', () => {
    it('should start analysis successfully', async () => {
      mockAnalysisService.startAnalysis.mockResolvedValue(mockAnalysis);
      
      const { result } = renderHook(() => useAnalysisStore());

      let returnedAnalysis: Analysis;
      await act(async () => {
        returnedAnalysis = await result.current.startAnalysis(mockAnalysisRequest);
      });

      expect(result.current.currentAnalysis).toEqual(mockAnalysis);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(returnedAnalysis!).toEqual(mockAnalysis);
      expect(mockAnalysisService.startAnalysis).toHaveBeenCalledWith(mockAnalysisRequest);
    });

    it('should handle start analysis failure', async () => {
      const errorMessage = 'Failed to start analysis';
      mockAnalysisService.startAnalysis.mockRejectedValue(new Error(errorMessage));
      
      const { result } = renderHook(() => useAnalysisStore());

      await act(async () => {
        try {
          await result.current.startAnalysis(mockAnalysisRequest);
        } catch (error) {
          // Expected to throw
        }
      });

      expect(result.current.currentAnalysis).toBeNull();
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBe(errorMessage);
    });

    it('should set loading state during analysis start', async () => {
      let resolveAnalysis: (value: any) => void;
      const analysisPromise = new Promise((resolve) => {
        resolveAnalysis = resolve;
      });
      mockAnalysisService.startAnalysis.mockReturnValue(analysisPromise);
      
      const { result } = renderHook(() => useAnalysisStore());

      act(() => {
        result.current.startAnalysis(mockAnalysisRequest);
      });

      expect(result.current.isLoading).toBe(true);

      await act(async () => {
        resolveAnalysis!(mockAnalysis);
        await analysisPromise;
      });

      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('Get Analysis Status', () => {
    it('should update current analysis status', async () => {
      const updatedAnalysis = { ...mockAnalysis, progress: 75 };
      mockAnalysisService.getAnalysisStatus.mockResolvedValue(updatedAnalysis);
      
      const { result } = renderHook(() => useAnalysisStore());

      // Set current analysis
      act(() => {
        result.current.setCurrentAnalysis(mockAnalysis);
      });

      await act(async () => {
        await result.current.getAnalysisStatus(mockAnalysis.id);
      });

      expect(result.current.currentAnalysis).toEqual(updatedAnalysis);
      expect(mockAnalysisService.getAnalysisStatus).toHaveBeenCalledWith(mockAnalysis.id);
    });

    it('should update analysis in history', async () => {
      const updatedAnalysis = { ...mockAnalysis, progress: 75 };
      mockAnalysisService.getAnalysisStatus.mockResolvedValue(updatedAnalysis);
      
      const { result } = renderHook(() => useAnalysisStore());

      // Set analysis history
      act(() => {
        useAnalysisStore.setState({
          analysisHistory: [mockAnalysis],
        });
      });

      await act(async () => {
        await result.current.getAnalysisStatus(mockAnalysis.id);
      });

      expect(result.current.analysisHistory[0]).toEqual(updatedAnalysis);
    });

    it('should handle get status error', async () => {
      const errorMessage = 'Failed to get status';
      mockAnalysisService.getAnalysisStatus.mockRejectedValue(new Error(errorMessage));
      
      const { result } = renderHook(() => useAnalysisStore());

      await act(async () => {
        await result.current.getAnalysisStatus(mockAnalysis.id);
      });

      expect(result.current.error).toBe(errorMessage);
    });
  });

  describe('Get Analysis Result', () => {
    it('should get analysis result successfully', async () => {
      const completedAnalysis = {
        ...mockAnalysis,
        status: 'completed' as const,
        result_data: { summary: 'Analysis complete' },
      };
      mockAnalysisService.getAnalysisResult.mockResolvedValue(completedAnalysis);
      
      const { result } = renderHook(() => useAnalysisStore());

      await act(async () => {
        await result.current.getAnalysisResult(mockAnalysis.id);
      });

      expect(result.current.currentAnalysis).toEqual(completedAnalysis);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('should handle get result error', async () => {
      const errorMessage = 'Failed to get result';
      mockAnalysisService.getAnalysisResult.mockRejectedValue(new Error(errorMessage));
      
      const { result } = renderHook(() => useAnalysisStore());

      await act(async () => {
        await result.current.getAnalysisResult(mockAnalysis.id);
      });

      expect(result.current.currentAnalysis).toBeNull();
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBe(errorMessage);
    });
  });

  describe('Load Analysis History', () => {
    it('should load analysis history successfully', async () => {
      const historyResult = {
        analyses: mockAnalysisHistory,
        page: 1,
        limit: 20,
        total: 2,
      };
      mockAnalysisService.getAnalysisHistory.mockResolvedValue(historyResult);
      
      const { result } = renderHook(() => useAnalysisStore());

      await act(async () => {
        await result.current.loadAnalysisHistory();
      });

      expect(result.current.analysisHistory).toEqual(mockAnalysisHistory);
      expect(result.current.pagination).toEqual({
        page: 1,
        limit: 20,
        total: 2,
      });
      expect(result.current.historyLoading).toBe(false);
      expect(result.current.historyError).toBeNull();
    });

    it('should load history with custom pagination', async () => {
      const historyResult = {
        analyses: mockAnalysisHistory,
        page: 2,
        limit: 10,
        total: 2,
      };
      mockAnalysisService.getAnalysisHistory.mockResolvedValue(historyResult);
      
      const { result } = renderHook(() => useAnalysisStore());

      await act(async () => {
        await result.current.loadAnalysisHistory(2, 10);
      });

      expect(mockAnalysisService.getAnalysisHistory).toHaveBeenCalledWith(2, 10);
      expect(result.current.pagination.page).toBe(2);
      expect(result.current.pagination.limit).toBe(10);
    });

    it('should handle load history error', async () => {
      const errorMessage = 'Failed to load history';
      mockAnalysisService.getAnalysisHistory.mockRejectedValue(new Error(errorMessage));
      
      const { result } = renderHook(() => useAnalysisStore());

      await act(async () => {
        await result.current.loadAnalysisHistory();
      });

      expect(result.current.analysisHistory).toEqual([]);
      expect(result.current.historyLoading).toBe(false);
      expect(result.current.historyError).toBe(errorMessage);
    });
  });

  describe('Delete Analysis', () => {
    it('should delete analysis successfully', async () => {
      mockAnalysisService.deleteAnalysis.mockResolvedValue(undefined);
      
      const { result } = renderHook(() => useAnalysisStore());

      // Set initial state with analysis in history
      act(() => {
        useAnalysisStore.setState({
          analysisHistory: mockAnalysisHistory,
          currentAnalysis: mockAnalysisHistory[0],
          pagination: { page: 1, limit: 20, total: 2 },
        });
      });

      await act(async () => {
        await result.current.deleteAnalysis('analysis-1');
      });

      expect(result.current.analysisHistory).toHaveLength(1);
      expect(result.current.analysisHistory[0].id).toBe('analysis-2');
      expect(result.current.currentAnalysis).toBeNull();
      expect(result.current.pagination.total).toBe(1);
      expect(mockAnalysisService.deleteAnalysis).toHaveBeenCalledWith('analysis-1');
    });

    it('should handle delete error', async () => {
      const errorMessage = 'Failed to delete analysis';
      mockAnalysisService.deleteAnalysis.mockRejectedValue(new Error(errorMessage));
      
      const { result } = renderHook(() => useAnalysisStore());

      await act(async () => {
        try {
          await result.current.deleteAnalysis('analysis-1');
        } catch (error) {
          // Expected to throw
        }
      });

      expect(result.current.error).toBe(errorMessage);
    });
  });

  describe('Cancel Analysis', () => {
    it('should cancel analysis successfully', async () => {
      mockAnalysisService.cancelAnalysis.mockResolvedValue(undefined);
      
      const { result } = renderHook(() => useAnalysisStore());

      // Set initial state
      act(() => {
        useAnalysisStore.setState({
          currentAnalysis: mockAnalysis,
          analysisHistory: [mockAnalysis],
        });
      });

      await act(async () => {
        await result.current.cancelAnalysis(mockAnalysis.id);
      });

      expect(result.current.currentAnalysis?.status).toBe('failed');
      expect(result.current.analysisHistory[0].status).toBe('failed');
      expect(mockAnalysisService.cancelAnalysis).toHaveBeenCalledWith(mockAnalysis.id);
    });

    it('should handle cancel error', async () => {
      const errorMessage = 'Failed to cancel analysis';
      mockAnalysisService.cancelAnalysis.mockRejectedValue(new Error(errorMessage));
      
      const { result } = renderHook(() => useAnalysisStore());

      await act(async () => {
        await result.current.cancelAnalysis(mockAnalysis.id);
      });

      expect(result.current.error).toBe(errorMessage);
    });
  });

  describe('Utility Actions', () => {
    it('should set current analysis', () => {
      const { result } = renderHook(() => useAnalysisStore());

      act(() => {
        result.current.setCurrentAnalysis(mockAnalysis);
      });

      expect(result.current.currentAnalysis).toEqual(mockAnalysis);

      act(() => {
        result.current.setCurrentAnalysis(null);
      });

      expect(result.current.currentAnalysis).toBeNull();
    });

    it('should clear error', () => {
      const { result } = renderHook(() => useAnalysisStore());

      act(() => {
        useAnalysisStore.setState({ error: 'Some error' });
      });

      expect(result.current.error).toBe('Some error');

      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBeNull();
    });

    it('should clear history error', () => {
      const { result } = renderHook(() => useAnalysisStore());

      act(() => {
        useAnalysisStore.setState({ historyError: 'History error' });
      });

      expect(result.current.historyError).toBe('History error');

      act(() => {
        result.current.clearHistoryError();
      });

      expect(result.current.historyError).toBeNull();
    });

    it('should update analysis progress', () => {
      const { result } = renderHook(() => useAnalysisStore());

      // Set initial state
      act(() => {
        useAnalysisStore.setState({
          currentAnalysis: mockAnalysis,
          analysisHistory: [mockAnalysis],
        });
      });

      act(() => {
        result.current.updateAnalysisProgress(mockAnalysis.id, 80, 'running');
      });

      expect(result.current.currentAnalysis?.progress).toBe(80);
      expect(result.current.currentAnalysis?.status).toBe('running');
      expect(result.current.analysisHistory[0].progress).toBe(80);
      expect(result.current.analysisHistory[0].status).toBe('running');
    });
  });
});