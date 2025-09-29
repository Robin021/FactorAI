import { create } from 'zustand';
import { Analysis, AnalysisRequest } from '@/types';
import { analysisService } from '@/services/analysis';

interface AnalysisState {
  // State
  currentAnalysis: Analysis | null;
  analysisHistory: Analysis[];
  isLoading: boolean;
  error: string | null;
  historyLoading: boolean;
  historyError: string | null;
  pagination: {
    page: number;
    limit: number;
    total: number;
  };

  // Actions
  startAnalysis: (request: AnalysisRequest) => Promise<Analysis>;
  getAnalysisStatus: (id: string) => Promise<void>;
  getAnalysisResult: (id: string) => Promise<void>;
  loadAnalysisHistory: (page?: number, limit?: number) => Promise<void>;
  deleteAnalysis: (id: string) => Promise<void>;
  cancelAnalysis: (id: string) => Promise<void>;
  setCurrentAnalysis: (analysis: Analysis | null) => void;
  clearError: () => void;
  clearHistoryError: () => void;
  updateAnalysisProgress: (id: string, progress: number, status?: string) => void;
}

export const useAnalysisStore = create<AnalysisState>((set, get) => ({
  // Initial state
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

  // Actions
  startAnalysis: async (request: AnalysisRequest) => {
    set({ isLoading: true, error: null });
    
    try {
      const analysis = await analysisService.startAnalysis(request);
      set({
        currentAnalysis: analysis,
        isLoading: false,
        error: null,
      });
      return analysis;
    } catch (error: any) {
      set({
        isLoading: false,
        error: error.message || 'Failed to start analysis',
      });
      throw error;
    }
  },

  getAnalysisStatus: async (id: string) => {
    try {
      const analysis = await analysisService.getAnalysisStatus(id);
      const { currentAnalysis } = get();
      
      if (currentAnalysis?.id === id) {
        set({ currentAnalysis: analysis });
      }
      
      // Update in history if exists
      set((state) => ({
        analysisHistory: state.analysisHistory.map((item) =>
          item.id === id ? analysis : item
        ),
      }));
    } catch (error: any) {
      set({ error: error.message || 'Failed to get analysis status' });
    }
  },

  getAnalysisResult: async (id: string) => {
    set({ isLoading: true, error: null });
    
    try {
      const analysis = await analysisService.getAnalysisResult(id);
      set({
        currentAnalysis: analysis,
        isLoading: false,
        error: null,
      });
    } catch (error: any) {
      set({
        isLoading: false,
        error: error.message || 'Failed to get analysis result',
      });
    }
  },

  loadAnalysisHistory: async (page = 1, limit = 20) => {
    set({ historyLoading: true, historyError: null });
    
    try {
      const result = await analysisService.getAnalysisHistory(page, limit);
      set({
        analysisHistory: result.analyses,
        pagination: {
          page: result.page,
          limit: result.limit,
          total: result.total,
        },
        historyLoading: false,
        historyError: null,
      });
    } catch (error: any) {
      console.error('Failed to load analysis history:', error);
      set({
        historyLoading: false,
        historyError: error.message || 'Failed to load analysis history',
      });
    }
  },

  deleteAnalysis: async (id: string) => {
    try {
      await analysisService.deleteAnalysis(id);
      
      // Remove from history
      set((state) => ({
        analysisHistory: state.analysisHistory.filter((item) => item.id !== id),
        pagination: {
          ...state.pagination,
          total: Math.max(0, state.pagination.total - 1),
        },
      }));
      
      // Clear current analysis if it's the deleted one
      const { currentAnalysis } = get();
      if (currentAnalysis?.id === id) {
        set({ currentAnalysis: null });
      }
    } catch (error: any) {
      set({ error: error.message || 'Failed to delete analysis' });
      throw error;
    }
  },

  cancelAnalysis: async (id: string) => {
    try {
      await analysisService.cancelAnalysis(id);
      
      // Update status in current analysis
      const { currentAnalysis } = get();
      if (currentAnalysis?.id === id) {
        set({
          currentAnalysis: {
            ...currentAnalysis,
            status: 'failed',
          },
        });
      }
      
      // Update in history
      set((state) => ({
        analysisHistory: state.analysisHistory.map((item) =>
          item.id === id ? { ...item, status: 'failed' as const } : item
        ),
      }));
    } catch (error: any) {
      set({ error: error.message || 'Failed to cancel analysis' });
      throw error;
    }
  },

  setCurrentAnalysis: (analysis: Analysis | null) => {
    set({ currentAnalysis: analysis });
  },

  clearError: () => {
    set({ error: null });
  },

  clearHistoryError: () => {
    set({ historyError: null });
  },

  updateAnalysisProgress: (id: string, progress: number, status?: string) => {
    const { currentAnalysis } = get();
    
    if (currentAnalysis?.id === id) {
      set({
        currentAnalysis: {
          ...currentAnalysis,
          progress,
          ...(status && { status: status as any }),
        },
      });
    }
    
    // Update in history
    set((state) => ({
      analysisHistory: state.analysisHistory.map((item) =>
        item.id === id
          ? {
              ...item,
              progress,
              ...(status && { status: status as any }),
            }
          : item
      ),
    }));
  },
}));