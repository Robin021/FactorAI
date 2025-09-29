import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { 
  configService, 
  LLMConfig, 
  DataSourceConfig, 
  SystemConfig, 
  UserPreferenceConfig 
} from '@/services/config';

interface ConfigState {
  // State
  llmConfig: LLMConfig | null;
  dataSourceConfigs: DataSourceConfig[];
  systemConfig: SystemConfig | null;
  userPreferences: UserPreferenceConfig | null;
  isLoading: boolean;
  error: string | null;
  testResults: {
    llm: { success: boolean; message: string } | null;
    dataSource: { success: boolean; message: string } | null;
  };

  // Actions
  loadLLMConfig: () => Promise<void>;
  updateLLMConfig: (config: Partial<LLMConfig>) => Promise<void>;
  loadDataSourceConfigs: () => Promise<void>;
  updateDataSourceConfigs: (configs: DataSourceConfig[]) => Promise<void>;
  loadSystemConfig: () => Promise<void>;
  updateSystemConfig: (config: Partial<SystemConfig>) => Promise<void>;
  loadUserPreferences: () => Promise<void>;
  updateUserPreferences: (config: Partial<UserPreferenceConfig>) => Promise<void>;
  testLLMConnection: (config: Partial<LLMConfig>) => Promise<void>;
  testDataSourceConnection: (config: DataSourceConfig) => Promise<void>;
  exportConfigs: () => Promise<any>;
  importConfigs: (configData: any) => Promise<void>;
  resetConfigs: () => Promise<void>;
  clearError: () => void;
  clearTestResults: () => void;
}

export const useConfigStore = create<ConfigState>()(
  persist(
    (set, get) => ({
      // Initial state
      llmConfig: null,
      dataSourceConfigs: [],
      systemConfig: null,
      userPreferences: null,
      isLoading: false,
      error: null,
      testResults: {
        llm: null,
        dataSource: null,
      },

      // Actions
      loadLLMConfig: async () => {
        set({ isLoading: true, error: null });
        
        try {
          const config = await configService.getLLMConfig();
          set({
            llmConfig: config,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.message || 'Failed to load LLM config',
          });
        }
      },

      updateLLMConfig: async (config: Partial<LLMConfig>) => {
        set({ isLoading: true, error: null });
        
        try {
          const updatedConfig = await configService.updateLLMConfig(config);
          set({
            llmConfig: updatedConfig,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.message || 'Failed to update LLM config',
          });
          throw error;
        }
      },

      loadDataSourceConfigs: async () => {
        set({ isLoading: true, error: null });
        
        try {
          const configs = await configService.getDataSourceConfig();
          set({
            dataSourceConfigs: configs,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.message || 'Failed to load data source configs',
          });
        }
      },

      updateDataSourceConfigs: async (configs: DataSourceConfig[]) => {
        set({ isLoading: true, error: null });
        
        try {
          const updatedConfigs = await configService.updateDataSourceConfig(configs);
          set({
            dataSourceConfigs: updatedConfigs,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.message || 'Failed to update data source configs',
          });
          throw error;
        }
      },

      loadSystemConfig: async () => {
        set({ isLoading: true, error: null });
        
        try {
          const config = await configService.getSystemConfig();
          set({
            systemConfig: config,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.message || 'Failed to load system config',
          });
        }
      },

      updateSystemConfig: async (config: Partial<SystemConfig>) => {
        set({ isLoading: true, error: null });
        
        try {
          const updatedConfig = await configService.updateSystemConfig(config);
          set({
            systemConfig: updatedConfig,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.message || 'Failed to update system config',
          });
          throw error;
        }
      },

      loadUserPreferences: async () => {
        set({ isLoading: true, error: null });
        
        try {
          const config = await configService.getUserPreferences();
          set({
            userPreferences: config,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.message || 'Failed to load user preferences',
          });
        }
      },

      updateUserPreferences: async (config: Partial<UserPreferenceConfig>) => {
        set({ isLoading: true, error: null });
        
        try {
          const updatedConfig = await configService.updateUserPreferences(config);
          set({
            userPreferences: updatedConfig,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.message || 'Failed to update user preferences',
          });
          throw error;
        }
      },

      testLLMConnection: async (config: Partial<LLMConfig>) => {
        set({ isLoading: true, error: null });
        
        try {
          const result = await configService.testLLMConnection(config);
          set((state) => ({
            testResults: {
              ...state.testResults,
              llm: result,
            },
            isLoading: false,
            error: null,
          }));
        } catch (error: any) {
          set((state) => ({
            testResults: {
              ...state.testResults,
              llm: { success: false, message: error.message || 'Connection test failed' },
            },
            isLoading: false,
            error: error.message || 'Failed to test LLM connection',
          }));
        }
      },

      testDataSourceConnection: async (config: DataSourceConfig) => {
        set({ isLoading: true, error: null });
        
        try {
          const result = await configService.testDataSourceConnection(config);
          set((state) => ({
            testResults: {
              ...state.testResults,
              dataSource: result,
            },
            isLoading: false,
            error: null,
          }));
        } catch (error: any) {
          set((state) => ({
            testResults: {
              ...state.testResults,
              dataSource: { success: false, message: error.message || 'Connection test failed' },
            },
            isLoading: false,
            error: error.message || 'Failed to test data source connection',
          }));
        }
      },

      exportConfigs: async () => {
        set({ isLoading: true, error: null });
        
        try {
          const data = await configService.exportConfigs();
          set({ isLoading: false, error: null });
          return data;
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.message || 'Failed to export configurations',
          });
          throw error;
        }
      },

      importConfigs: async (configData: any) => {
        set({ isLoading: true, error: null });
        
        try {
          await configService.importConfigs(configData);
          // Reload all configs after import
          const state = get();
          await Promise.all([
            state.loadLLMConfig(),
            state.loadDataSourceConfigs(),
            state.loadSystemConfig(),
            state.loadUserPreferences(),
          ]);
          set({ isLoading: false, error: null });
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.message || 'Failed to import configurations',
          });
          throw error;
        }
      },

      resetConfigs: async () => {
        set({ isLoading: true, error: null });
        
        try {
          await configService.resetConfigs();
          // Reload all configs after reset
          const state = get();
          await Promise.all([
            state.loadLLMConfig(),
            state.loadDataSourceConfigs(),
            state.loadSystemConfig(),
            state.loadUserPreferences(),
          ]);
          set({ isLoading: false, error: null });
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.message || 'Failed to reset configurations',
          });
          throw error;
        }
      },

      clearError: () => {
        set({ error: null });
      },

      clearTestResults: () => {
        set({
          testResults: {
            llm: null,
            dataSource: null,
          },
        });
      },
    }),
    {
      name: 'config-store',
      partialize: (state) => ({
        llmConfig: state.llmConfig,
        dataSourceConfigs: state.dataSourceConfigs,
        systemConfig: state.systemConfig,
        userPreferences: state.userPreferences,
      }),
    }
  )
);