import { apiClient } from './api';
import { AnalysisRequest, Analysis } from '@/types';

export class AnalysisService {
  // Start new analysis
  async startAnalysis(request: AnalysisRequest): Promise<Analysis> {
    try {
      console.log('🚀 [startAnalysis] 发送请求:', request);
      const response = await apiClient.post('/analysis/start', request);
      console.log('📥 [startAnalysis] 收到响应:', response);
      
      // 检查响应格式
      if (typeof response === 'string') {
        console.error('❌ [startAnalysis] API返回了字符串而不是JSON对象:', response);
        throw new Error('服务器返回了无效的响应格式');
      }
      
      if (!response.analysis_id) {
        console.error('❌ [startAnalysis] API响应中缺少analysis_id:', response);
        throw new Error('服务器响应中缺少分析ID');
      }
      
      // 适配后端返回格式，转换为前端期望的 Analysis 格式
      const analysis = {
        id: response.analysis_id,
        userId: 'current_user', // 从认证状态获取
        stockCode: response.symbol,
        status: response.status === 'started' ? 'running' : response.status,
        progress: 0,
        createdAt: new Date().toISOString(),
        marketType: request.market_type,
        analysisType: request.analysis_type,
        resultData: null
      } as Analysis;
      
      console.log('✅ [startAnalysis] 转换后的Analysis对象:', analysis);
      return analysis;
    } catch (error: any) {
      console.error('❌ [startAnalysis] 错误:', error);
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error(error.message || 'Failed to start analysis');
    }
  }

  // Get analysis status
  async getAnalysisStatus(id: string): Promise<Analysis> {
    try {
      const response = await apiClient.get(`/analysis/${id}/status`);
      
      // 适配后端返回格式
      return {
        id: response.analysis_id,
        userId: response.user || 'current_user',
        stockCode: 'UNKNOWN', // 后端没有返回，使用默认值
        status: response.status === 'completed' ? 'completed' : 'running',
        progress: response.progress || 100,
        createdAt: response.created_at || new Date().toISOString(),
        completedAt: response.completed_at,
      } as Analysis;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error(error.message || 'Failed to get analysis status');
    }
  }

  // Get analysis result
  async getAnalysisResult(id: string): Promise<Analysis> {
    try {
      const response = await apiClient.get(`/analysis/${id}/results`);
      
      // 适配后端返回格式
      return {
        id: response.analysis_id,
        userId: response.user || 'current_user',
        stockCode: response.symbol,
        status: 'completed',
        progress: 100,
        resultData: response.results,
        createdAt: response.created_at || new Date().toISOString(),
        completedAt: response.completed_at || new Date().toISOString(),
      } as Analysis;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error(error.message || 'Failed to get analysis result');
    }
  }

  // Get analysis history
  async getAnalysisHistory(page = 1, limit = 20): Promise<{
    analyses: Analysis[];
    total: number;
    page: number;
    limit: number;
  }> {
    try {
      const response = await apiClient.get(`/analysis/history?page=${page}&limit=${limit}`);
      
      // 转换后端数据格式为前端格式
      const analyses: Analysis[] = (response.analyses || []).map((item: any) => ({
        id: item.analysis_id,
        userId: 'current_user',
        stockCode: item.symbol,
        status: item.status === 'completed' ? 'completed' : item.status === 'failed' ? 'failed' : 'running',
        progress: item.progress_percentage || 0,
        createdAt: item.created_at || new Date().toISOString(),
        marketType: item.market_type || 'CN',
        analysisType: item.analysis_type || 'comprehensive',
        resultData: item.status === 'completed' ? {} : null  // 已完成的分析标记为有结果数据
      }));
      
      return {
        analyses,
        total: response.total || 0,
        page,
        limit,
      };
    } catch (error: any) {
      throw new Error(error.message || 'Failed to get analysis history');
    }
  }

  // Delete analysis
  async deleteAnalysis(id: string): Promise<void> {
    try {
      // 目前后端没有删除接口，模拟成功
      console.log(`Delete analysis ${id} - not implemented`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to delete analysis');
    }
  }

  // Cancel running analysis
  async cancelAnalysis(id: string): Promise<void> {
    try {
      // 目前后端没有取消接口，模拟成功
      console.log(`Cancel analysis ${id} - not implemented`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to cancel analysis');
    }
  }

  // Export analysis report
  async exportAnalysis(id: string, format: 'pdf' | 'excel' | 'word' | 'json'): Promise<Blob> {
    const response = await fetch(`/api/v1/analysis/${id}/export?format=${format}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to export analysis');
    }

    return response.blob();
  }

  // Share analysis report
  async shareAnalysis(id: string, method: 'email' | 'link' | 'wechat', options?: {
    email?: string;
    message?: string;
    expiresIn?: number;
  }): Promise<{ shareUrl?: string; message: string }> {
    const response = await apiClient.post(`/analysis/${id}/share`, {
      method,
      ...options,
    });
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new Error(response.error || 'Failed to share analysis');
  }

  // Compare multiple analyses
  async compareAnalyses(analysisIds: string[]): Promise<{
    analyses: Analysis[];
    comparison: Record<string, any>;
  }> {
    const response = await apiClient.post('/analysis/compare', {
      analysisIds,
    });
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new Error(response.error || 'Failed to compare analyses');
  }

  // Get analysis history with filters
  async getFilteredAnalysisHistory(filters: {
    stockCode?: string;
    status?: string;
    dateRange?: [string, string];
    page?: number;
    limit?: number;
  }): Promise<{
    analyses: Analysis[];
    total: number;
    page: number;
    limit: number;
  }> {
    const response = await apiClient.get('/analysis/history', {
      params: filters,
    });
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new Error(response.error || 'Failed to get filtered analysis history');
  }

  // Duplicate analysis with new parameters
  async duplicateAnalysis(id: string, newRequest?: Partial<AnalysisRequest>): Promise<Analysis> {
    const response = await apiClient.post(`/analysis/${id}/duplicate`, newRequest || {});
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new Error(response.error || 'Failed to duplicate analysis');
  }
}

export const analysisService = new AnalysisService();
export default analysisService;