import { useEffect } from 'react';
import { useAnalysisStore } from '@/stores/analysisStore';
import { AnalysisRequest } from '@/types';

export const useAnalysis = () => {
  const {
    currentAnalysis,
    analysisHistory,
    isLoading,
    error,
    historyLoading,
    historyError,
    pagination,
    startAnalysis,
    getAnalysisStatus,
    getAnalysisResult,
    loadAnalysisHistory,
    deleteAnalysis,
    cancelAnalysis,
    setCurrentAnalysis,
    clearError,
    clearHistoryError,
  } = useAnalysisStore();

  // Load analysis history on mount
  useEffect(() => {
    // 总是尝试加载最新的历史记录，不依赖本地缓存
    loadAnalysisHistory();
  }, []); // 只在组件挂载时执行一次

  const handleStartAnalysis = async (request: AnalysisRequest) => {
    try {
      const analysis = await startAnalysis(request);
      return analysis;
    } catch (error) {
      throw error;
    }
  };

  const handleDeleteAnalysis = async (id: string) => {
    try {
      await deleteAnalysis(id);
    } catch (error) {
      throw error;
    }
  };

  const handleCancelAnalysis = async (id: string) => {
    try {
      await cancelAnalysis(id);
    } catch (error) {
      throw error;
    }
  };

  const refreshHistory = () => {
    loadAnalysisHistory(pagination.page, pagination.limit);
  };

  const loadMoreHistory = () => {
    if (pagination.page * pagination.limit < pagination.total) {
      loadAnalysisHistory(pagination.page + 1, pagination.limit);
    }
  };

  return {
    currentAnalysis,
    analysisHistory,
    isLoading,
    error,
    historyLoading,
    historyError,
    pagination,
    startAnalysis: handleStartAnalysis,
    getAnalysisStatus,
    getAnalysisResult,
    deleteAnalysis: handleDeleteAnalysis,
    cancelAnalysis: handleCancelAnalysis,
    setCurrentAnalysis,
    clearError,
    clearHistoryError,
    refreshHistory,
    loadMoreHistory,
  };
};