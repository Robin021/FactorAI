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
      
      console.log('📊 [Store] 收到历史数据:', result);
      console.log('📊 [Store] analyses数组:', result.analyses);
      
      // 🔧 新增：自动检测运行中的任务
      const runningAnalysis = result.analyses.find(
        (item) => item.status === 'running' || item.status === 'pending'
      );

      // 🔧 新增：如果没有运行中的任务，自动选中最新的完成任务作为当前分析，避免需要来回切换标签
      let selectedAnalysis = runningAnalysis;
      if (!selectedAnalysis && result.analyses.length > 0) {
        // 选择最近的一个（按createdAt倒序），若无createdAt则取第一个
        const sorted = [...result.analyses].sort((a, b) => {
          const ta = a.createdAt ? Date.parse(a.createdAt) : 0;
          const tb = b.createdAt ? Date.parse(b.createdAt) : 0;
          return tb - ta;
        });
        selectedAnalysis = sorted[0];
      }
      
      if (runningAnalysis) {
        console.log('✅ [Store] 发现运行中的任务:', runningAnalysis);
        console.log('✅ [Store] 任务ID:', runningAnalysis.id);
        console.log('✅ [Store] 股票代码:', runningAnalysis.stockCode);
        console.log('✅ [Store] 状态:', runningAnalysis.status);
        console.log('✅ [Store] 进度:', runningAnalysis.progress);
      } else {
        console.log('ℹ️ [Store] 没有运行中的任务');
      }
      
      set({
        analysisHistory: result.analyses,
        // ✅ 自动设置currentAnalysis：优先运行中的任务，否则最新一条
        currentAnalysis: selectedAnalysis || get().currentAnalysis,
        pagination: {
          page: result.page,
          limit: result.limit,
          total: result.total,
        },
        historyLoading: false,
        historyError: null,
      });
      
      console.log('✅ [Store] 状态已更新，currentAnalysis:', get().currentAnalysis);
    } catch (error: any) {
      console.error('❌ [Store] 加载历史失败:', error);
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