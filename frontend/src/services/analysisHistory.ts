import { Analysis } from '@/types';

export interface AnalysisHistoryItem {
  analysis_id: string;
  symbol: string;
  status: 'running' | 'completed' | 'failed';
  progress_percentage: number;
  created_at: string;
  last_update: number;
  current_step_name: string;
  elapsed_time: number;
}

export interface AnalysisHistoryResponse {
  analyses: AnalysisHistoryItem[];
  total: number;
}

class AnalysisHistoryService {
  private baseURL = '/api/v1';

  async getAnalysisHistory(): Promise<AnalysisHistoryResponse> {
    const token = localStorage.getItem('auth_token');
    
    const response = await fetch(`${this.baseURL}/analysis/history`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`获取分析历史失败: ${response.statusText}`);
    }

    return response.json();
  }

  async getAnalysisProgress(analysisId: string) {
    const token = localStorage.getItem('auth_token');
    
    const response = await fetch(`${this.baseURL}/analysis/${analysisId}/progress`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`获取分析进度失败: ${response.statusText}`);
    }

    return response.json();
  }

  async getAnalysisResults(analysisId: string) {
    const token = localStorage.getItem('auth_token');
    
    const response = await fetch(`${this.baseURL}/analysis/${analysisId}/results`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`获取分析结果失败: ${response.statusText}`);
    }

    return response.json();
  }
}

export const analysisHistoryService = new AnalysisHistoryService();