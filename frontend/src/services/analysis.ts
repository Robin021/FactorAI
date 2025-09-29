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
      const response = await apiClient.get(`/analysis/${id}/result`);
      
      // 适配后端返回格式
      return {
        id: response.id,
        userId: response.user_id,
        stockCode: response.stock_code,
        status: response.status,
        progress: response.progress,
        resultData: response.result_data,
        createdAt: response.created_at,
        completedAt: response.completed_at,
      } as Analysis;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error(error.message || 'Failed to get analysis result');
    }
  }

  // Download analysis PDF
  async downloadAnalysisPDF(id: string): Promise<Blob> {
    try {
      const response = await apiClient.request({
        url: `/analysis/${id}/download/pdf`,
        method: 'GET',
        responseType: 'blob',
      });
      return response;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error(error.message || 'Failed to download PDF');
    }
  }

  // Get analysis files
  async getAnalysisFiles(id: string): Promise<{files: Array<{name: string, type: string, size: number, url: string}>}> {
    try {
      const response = await apiClient.get(`/analysis/${id}/files`);
      return response;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error(error.message || 'Failed to get analysis files');
    }
  }

  // Download analysis file
  async downloadAnalysisFile(id: string, filename: string): Promise<Blob> {
    try {
      const response = await apiClient.request({
        url: `/analysis/${id}/download/${filename}`,
        method: 'GET',
        responseType: 'blob',
      });
      return response;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error(error.message || 'Failed to download file');
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
      const response = await apiClient.get(`/analysis/history?page=${page}&page_size=${limit}`);
      
      // 转换后端数据格式为前端格式
      const analyses: Analysis[] = (response.analyses || []).map((item: any) => ({
        id: item.id,
        userId: item.user_id,
        stockCode: item.stock_code,
        status: item.status,
        progress: item.progress || 0,
        createdAt: item.created_at,
        startedAt: item.started_at,
        completedAt: item.completed_at,
        marketType: item.market_type,
        analysisType: 'comprehensive', // 默认值，如果后端没有这个字段
        config: item.config || {},
        resultData: item.result_data,
        errorMessage: item.error_message
      }));
      
      return {
        analyses,
        total: response.total || 0,
        page: response.page || page,
        limit: response.page_size || limit,
      };
    } catch (error: any) {
      console.error('Failed to get analysis history:', error);
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
      const response = await fetch(`/api/v1/analysis/${id}/cancel`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to cancel analysis');
      }

      console.log(`Analysis ${id} cancelled successfully`);
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