import { apiClient } from './api';

export enum LLMProvider {
  OPENAI = 'openai',
  DASHSCOPE = 'dashscope',
  DEEPSEEK = 'deepseek',
  GEMINI = 'gemini',
  QIANFAN = 'qianfan',
}

export enum DataSourceType {
  TUSHARE = 'tushare',
  AKSHARE = 'akshare',
  FINNHUB = 'finnhub',
  BAOSTOCK = 'baostock',
}

export interface LLMConfig {
  provider: LLMProvider;
  model_name: string;
  api_key: string;
  api_base?: string;
  temperature: number;
  max_tokens?: number;
  timeout: number;
  retry_attempts: number;
  enabled: boolean;
}

export interface DataSourceConfig {
  source_type: DataSourceType;
  api_key?: string;
  api_secret?: string;
  base_url?: string;
  priority: number;
  timeout: number;
  cache_ttl: number;
  enabled: boolean;
}

export interface SystemConfig {
  max_concurrent_analyses: number;
  default_analysis_timeout: number;
  cache_enabled: boolean;
  log_level: string;
  maintenance_mode: boolean;
}

export interface UserPreferenceConfig {
  default_market_type: string;
  preferred_analysts: string[];
  notification_enabled: boolean;
  theme: string;
  language: string;
}

export interface Config {
  id: string;
  user_id?: string;
  config_type: string;
  config_data: any;
  created_at: string;
  updated_at: string;
}

export class ConfigService {
  // LLM Configuration
  async getLLMConfig(): Promise<LLMConfig> {
    const response = await apiClient.get<Config>('/config/llm');
    
    if (response.success && response.data) {
      return response.data.config_data as LLMConfig;
    }
    
    throw new Error(response.error || 'Failed to get LLM config');
  }

  async updateLLMConfig(config: Partial<LLMConfig>): Promise<LLMConfig> {
    const response = await apiClient.put<Config>('/config/llm', { config_data: config });
    
    if (response.success && response.data) {
      return response.data.config_data as LLMConfig;
    }
    
    throw new Error(response.error || 'Failed to update LLM config');
  }

  // Data Source Configuration
  async getDataSourceConfig(): Promise<DataSourceConfig[]> {
    const response = await apiClient.get<Config[]>('/config/data-sources');
    
    if (response.success && response.data) {
      return response.data.map(config => config.config_data as DataSourceConfig);
    }
    
    throw new Error(response.error || 'Failed to get data source config');
  }

  async updateDataSourceConfig(configs: DataSourceConfig[]): Promise<DataSourceConfig[]> {
    const response = await apiClient.put<Config[]>('/config/data-sources', { configs });
    
    if (response.success && response.data) {
      return response.data.map(config => config.config_data as DataSourceConfig);
    }
    
    throw new Error(response.error || 'Failed to update data source config');
  }

  // System Configuration
  async getSystemConfig(): Promise<SystemConfig> {
    const response = await apiClient.get<Config>('/config/system');
    
    if (response.success && response.data) {
      return response.data.config_data as SystemConfig;
    }
    
    throw new Error(response.error || 'Failed to get system config');
  }

  async updateSystemConfig(config: Partial<SystemConfig>): Promise<SystemConfig> {
    const response = await apiClient.put<Config>('/config/system', { config_data: config });
    
    if (response.success && response.data) {
      return response.data.config_data as SystemConfig;
    }
    
    throw new Error(response.error || 'Failed to update system config');
  }

  // User Preferences
  async getUserPreferences(): Promise<UserPreferenceConfig> {
    const response = await apiClient.get<Config>('/config/preferences');
    
    if (response.success && response.data) {
      return response.data.config_data as UserPreferenceConfig;
    }
    
    throw new Error(response.error || 'Failed to get user preferences');
  }

  async updateUserPreferences(config: Partial<UserPreferenceConfig>): Promise<UserPreferenceConfig> {
    const response = await apiClient.put<Config>('/config/preferences', { config_data: config });
    
    if (response.success && response.data) {
      return response.data.config_data as UserPreferenceConfig;
    }
    
    throw new Error(response.error || 'Failed to update user preferences');
  }

  // Test configuration
  async testLLMConnection(config: Partial<LLMConfig>): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post('/config/llm/test', config);
    
    if (response.success && response.data) {
      return {
        success: response.data.test_successful || false,
        message: response.data.provider ? 
          `连接成功 - 提供商: ${response.data.provider}, 模型: ${response.data.model}` :
          response.data.error || '连接测试完成'
      };
    }
    
    throw new Error(response.error || 'Failed to test LLM connection');
  }

  async testDataSourceConnection(config: DataSourceConfig): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post('/config/data-sources/test', config);
    
    if (response.success && response.data) {
      return {
        success: response.data.test_successful || false,
        message: response.data.source ? 
          `连接成功 - 数据源: ${response.data.source}, 记录数: ${response.data.records_count || 0}` :
          response.data.error || '连接测试完成'
      };
    }
    
    throw new Error(response.error || 'Failed to test data source connection');
  }

  // Configuration export/import
  async exportConfigs(): Promise<any> {
    const response = await apiClient.get('/config/export');
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new Error(response.error || 'Failed to export configurations');
  }

  async importConfigs(configData: any): Promise<{ imported_count: number }> {
    const response = await apiClient.post('/config/import', configData);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new Error(response.error || 'Failed to import configurations');
  }

  // Reset configurations
  async resetConfigs(): Promise<{ created_count: number }> {
    const response = await apiClient.post('/config/reset');
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new Error(response.error || 'Failed to reset configurations');
  }
}

export const configService = new ConfigService();
export default configService;