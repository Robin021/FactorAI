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
        stockCode: response.symbol || request.stock_code,
        status: response.status === 'started' ? 'running' : response.status,
        progress: 0,
        createdAt: response.created_at || new Date().toISOString(), // 优先使用后端返回的时间
        completedAt: response.completed_at, // 添加完成时间
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
        userId: response.user || response.user_id || 'current_user',
        stockCode: response.stock_code || response.symbol || 'UNKNOWN',
        status: response.status === 'completed' ? 'completed' : 'running',
        progress: response.progress || 100,
        createdAt: response.created_at, // 使用后端返回的时间
        completedAt: response.completed_at,
      } as Analysis;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error(error.message || 'Failed to get analysis status');
    }
  }

  // Get analysis result（带宽限/最终一致性容忍，自动重试）
  async getAnalysisResult(id: string): Promise<Analysis> {
    const maxRetries = 6; // 最多重试6次（约10秒）
    const baseDelayMs = 800; // 首次延迟

    const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const response = await apiClient.get(`/analysis/${id}/results`);

        // 适配后端返回格式
        const results = response.results || response.result_data;
        const hasContent = results && (Array.isArray(results) ? results.length > 0 : Object.keys(results).length > 0);
        return {
          id: response.id || response.analysis_id || response._id,
          userId: response.user_id || 'current_user',
          stockCode: response.stock_code || response.symbol,
          status: response.status,
          progress: response.progress || 100,
          resultData: hasContent
            ? {
                // 从state字段中提取分析结果
                trader_investment_plan: results.state?.trader_investment_plan || '',
                market_report: results.state?.market_report || '',
                sentiment_report: results.state?.sentiment_report || '',
                fundamentals_report: results.state?.fundamentals_report || '',
                risk_assessment: results.state?.risk_assessment || '',
                investment_plan: results.state?.investment_plan || '',
                final_trade_decision: results.state?.final_trade_decision || '',
                // 研究团队辩论与风险管理辩论状态（用于详细报告展示）
                investment_debate_state: results.state?.investment_debate_state || null,
                risk_debate_state: results.state?.risk_debate_state || null,
                decision: results.decision || {},
                // 保留原始数据
                ...results,
              }
            : undefined,
          createdAt: response.created_at,
          completedAt: response.completed_at,
        } as Analysis;
      } catch (error: any) {
        // 可容忍错误：结果尚未可读（404 未找到 / 400 未完成）→ 自动重试
        const status = error?.response?.status;
        const detail: string | undefined = error?.response?.data?.detail || error?.message;
        const isTransient404 = status === 404 && (/(分析结果未找到|分析未找到)/.test(detail || ''));
        const isNotReady400 = status === 400 && /(未完成|尚未完成)/.test(detail || '');

        if ((isTransient404 || isNotReady400) && attempt < maxRetries) {
          const delay = Math.round(baseDelayMs * Math.pow(1.4, attempt));
          console.log(`⏳ [getAnalysisResult] 结果暂不可用，${delay}ms后重试 (${attempt + 1}/${maxRetries})`);
          await sleep(delay);
          continue;
        }

        // 其他错误或已达最大重试次数
        if (detail) throw new Error(detail);
        throw new Error(error.message || 'Failed to get analysis result');
      }
    }

    // 兜底：尝试读取状态并返回占位对象，避免让UI显示硬错误
    try {
      const statusResp = await apiClient.get(`/analysis/${id}/status`);
      return {
        id: statusResp.id || id,
        userId: statusResp.user || 'current_user',
        stockCode: statusResp.symbol || statusResp.stock_code || 'UNKNOWN',
        status: statusResp.status || 'running',
        progress: statusResp.progress || Math.round((statusResp.progress_percentage || 0) * 100) || 0,
        resultData: undefined,
        createdAt: statusResp.created_at || new Date().toISOString(),
        completedAt: statusResp.completed_at,
      } as Analysis;
    } catch {
      // 最终失败才抛错
      throw new Error('分析结果暂不可用，请稍后重试');
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
      await apiClient.post(`/analysis/${id}/cancel`);
      console.log(`Analysis ${id} cancelled successfully`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to cancel analysis');
    }
  }

  // Export analysis report
  async exportAnalysis(id: string, format: 'pdf' | 'excel' | 'word' | 'json'): Promise<Blob> {
    // 使用 apiClient，自动携带 Authorization
    const response = await apiClient.request({
      url: `/analysis/${id}/export?format=${format}`,
      method: 'GET',
      responseType: 'blob',
    });
    return response as unknown as Blob;
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
