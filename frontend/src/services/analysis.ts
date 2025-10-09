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
      const analysis: Analysis = {
        id: response.analysis_id,
        userId: 'current_user', // 从认证状态获取
        stockCode: response.symbol,
        status: response.status === 'started' ? 'running' : response.status,
        progress: 0,
        createdAt: new Date().toISOString(),
        marketType: request.market_type,
        analysisType: request.analysis_type,
        resultData: undefined
      };
      
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
        id: response.id || response.analysis_id || response._id,
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
      const results = response.results || response.result_data;
      return {
        id: response.id || response.analysis_id || response._id,
        userId: response.user_id || 'current_user',
        stockCode: response.stock_code || response.symbol,
        status: response.status,
        progress: response.progress || 100,
        resultData: results ? {
          // 从state字段中提取分析结果
          trader_investment_plan: results.state?.trader_investment_plan || '',
          market_report: results.state?.market_report || '',
          sentiment_report: results.state?.sentiment_report || '',
          fundamentals_report: results.state?.fundamentals_report || '',
          risk_assessment: results.state?.risk_assessment || '',
          investment_plan: results.state?.investment_plan || '',
          final_trade_decision: results.state?.final_trade_decision || '',
          decision: results.decision || {},
          // 保留原始数据
          ...results
        } : undefined,
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
      
      console.log('📊 [getAnalysisHistory] 后端响应:', response);
      console.log('📊 [getAnalysisHistory] analyses数量:', response.analyses?.length);
      
      // 🔧 修复：转换后端数据格式为前端格式（字段名映射）
      const analyses: Analysis[] = (response.analyses || []).map((item: any) => {
        console.log('🔍 [getAnalysisHistory] 原始item:', item);
        
        // ✅ 修复字段映射
        const mapped = {
          id: item.id || item.analysis_id || item._id,  // 后端返回 id 字段
          userId: item.user_id || 'current_user',
          stockCode: item.stock_code || item.symbol,  // 后端返回 stock_code
          status: item.status,
          progress: item.progress_percentage !== undefined 
            ? item.progress_percentage * 100  // 后端返回 0-1，转换为 0-100
            : (item.progress || 0),
          createdAt: item.created_at,
          startedAt: item.started_at,
          completedAt: item.completed_at,
          marketType: item.market_type,
          analysisType: item.analysis_type || 'comprehensive',
          config: item.config || {},
          resultData: item.result_data,
          errorMessage: item.error_message
        };
        
        console.log('✅ [getAnalysisHistory] 映射后的Analysis:', mapped);
        return mapped;
      });
      
      console.log('✅ [getAnalysisHistory] 最终返回:', { 
        总数: analyses.length, 
        第一个: analyses[0] 
      });
      
      return {
        analyses,
        total: response.total || 0,
        page: response.page || page,
        limit: response.page_size || limit,
      };
    } catch (error: any) {
      console.error('❌ [getAnalysisHistory] 失败:', error);
      throw new Error(error.message || 'Failed to get analysis history');
    }
  }

  // Delete analysis
  async deleteAnalysis(id: string): Promise<void> {
    try {
      console.log(`🗑️ [deleteAnalysis] 删除分析记录: ${id}`);
      await apiClient.delete(`/analysis/${id}`);
      console.log(`✅ [deleteAnalysis] 删除成功: ${id}`);
    } catch (error: any) {
      console.error(`❌ [deleteAnalysis] 删除失败: ${id}`, error);
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
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