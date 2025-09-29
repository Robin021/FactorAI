import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import LLMConfig from './LLMConfig';
import { useConfigStore } from '@/stores/configStore';
import { LLMProvider } from '@/services/config';

// Mock the config store
vi.mock('@/stores/configStore');

// Mock antd message
vi.mock('antd', async () => {
  const actual = await vi.importActual('antd');
  return {
    ...actual,
    message: {
      success: vi.fn(),
      error: vi.fn(),
    },
  };
});

const mockConfigStore = {
  llmConfig: null,
  isLoading: false,
  error: null,
  testResults: {
    llm: null,
    dataSource: null,
  },
  loadLLMConfig: vi.fn(),
  updateLLMConfig: vi.fn(),
  testLLMConnection: vi.fn(),
  clearError: vi.fn(),
  clearTestResults: vi.fn(),
};

describe('LLMConfig', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useConfigStore as any).mockReturnValue(mockConfigStore);
  });

  it('renders LLM configuration form', () => {
    render(<LLMConfig />);
    
    expect(screen.getByText('LLM 配置管理')).toBeInTheDocument();
    expect(screen.getByText('配置大语言模型提供商和参数设置')).toBeInTheDocument();
    expect(screen.getByLabelText('LLM 提供商')).toBeInTheDocument();
    expect(screen.getByLabelText('模型名称')).toBeInTheDocument();
  });

  it('loads LLM config on mount', () => {
    render(<LLMConfig />);
    
    expect(mockConfigStore.loadLLMConfig).toHaveBeenCalledTimes(1);
  });

  it('displays existing config when loaded', () => {
    const mockConfig = {
      provider: LLMProvider.OPENAI,
      model_name: 'gpt-4',
      api_key: 'sk-test123',
      temperature: 0.7,
      timeout: 30,
      retry_attempts: 3,
      enabled: true,
    };

    (useConfigStore as any).mockReturnValue({
      ...mockConfigStore,
      llmConfig: mockConfig,
    });

    render(<LLMConfig />);
    
    expect(screen.getByDisplayValue('gpt-4')).toBeInTheDocument();
  });

  it('shows error message when there is an error', () => {
    (useConfigStore as any).mockReturnValue({
      ...mockConfigStore,
      error: 'Failed to load config',
    });

    render(<LLMConfig />);
    
    expect(screen.getByText('配置错误')).toBeInTheDocument();
    expect(screen.getByText('Failed to load config')).toBeInTheDocument();
  });

  it('updates provider and model when provider changes', async () => {
    render(<LLMConfig />);
    
    const providerSelect = screen.getByLabelText('LLM 提供商');
    fireEvent.mouseDown(providerSelect);
    
    await waitFor(() => {
      const dashscopeOption = screen.getByText('DashScope (阿里云)');
      fireEvent.click(dashscopeOption);
    });

    // Should update model to default for DashScope
    await waitFor(() => {
      expect(screen.getByDisplayValue('qwen-turbo')).toBeInTheDocument();
    });
  });

  it('validates required fields before saving', async () => {
    render(<LLMConfig />);
    
    const saveButton = screen.getByText('保存配置');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('请选择 LLM 提供商')).toBeInTheDocument();
    });
  });

  it('calls updateLLMConfig when form is submitted', async () => {
    const mockUpdate = vi.fn().mockResolvedValue({});
    (useConfigStore as any).mockReturnValue({
      ...mockConfigStore,
      updateLLMConfig: mockUpdate,
    });

    render(<LLMConfig />);
    
    // Fill in required fields
    const providerSelect = screen.getByLabelText('LLM 提供商');
    fireEvent.mouseDown(providerSelect);
    
    await waitFor(() => {
      const openaiOption = screen.getByText('OpenAI');
      fireEvent.click(openaiOption);
    });

    const modelSelect = screen.getByLabelText('模型名称');
    fireEvent.mouseDown(modelSelect);
    
    await waitFor(() => {
      const gpt4Option = screen.getByText('gpt-4');
      fireEvent.click(gpt4Option);
    });

    const apiKeyInput = screen.getByLabelText(/API Key/);
    fireEvent.change(apiKeyInput, { target: { value: 'sk-test123' } });

    const saveButton = screen.getByText('保存配置');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockUpdate).toHaveBeenCalledWith(
        expect.objectContaining({
          provider: 'openai',
          model_name: 'gpt-4',
          api_key: 'sk-test123',
        })
      );
    });
  });

  it('calls testLLMConnection when test button is clicked', async () => {
    const mockTest = vi.fn().mockResolvedValue({});
    (useConfigStore as any).mockReturnValue({
      ...mockConfigStore,
      testLLMConnection: mockTest,
    });

    render(<LLMConfig />);
    
    // Fill in required fields first
    const providerSelect = screen.getByLabelText('LLM 提供商');
    fireEvent.mouseDown(providerSelect);
    
    await waitFor(() => {
      const openaiOption = screen.getByText('OpenAI');
      fireEvent.click(openaiOption);
    });

    const modelSelect = screen.getByLabelText('模型名称');
    fireEvent.mouseDown(modelSelect);
    
    await waitFor(() => {
      const gpt4Option = screen.getByText('gpt-4');
      fireEvent.click(gpt4Option);
    });

    const apiKeyInput = screen.getByLabelText(/API Key/);
    fireEvent.change(apiKeyInput, { target: { value: 'sk-test123' } });

    const testButton = screen.getByText('测试连接');
    fireEvent.click(testButton);

    await waitFor(() => {
      expect(mockTest).toHaveBeenCalledWith(
        expect.objectContaining({
          provider: 'openai',
          model_name: 'gpt-4',
          api_key: 'sk-test123',
        })
      );
    });
  });

  it('shows test results modal when test completes', async () => {
    (useConfigStore as any).mockReturnValue({
      ...mockConfigStore,
      testResults: {
        llm: { success: true, message: 'Connection successful' },
        dataSource: null,
      },
    });

    render(<LLMConfig />);
    
    // Simulate test completion by clicking test button
    const testButton = screen.getByText('测试连接');
    fireEvent.click(testButton);

    await waitFor(() => {
      expect(screen.getByText('连接测试结果')).toBeInTheDocument();
      expect(screen.getByText('连接成功')).toBeInTheDocument();
      expect(screen.getByText('Connection successful')).toBeInTheDocument();
    });
  });

  it('shows loading state when isLoading is true', () => {
    (useConfigStore as any).mockReturnValue({
      ...mockConfigStore,
      isLoading: true,
    });

    render(<LLMConfig />);
    
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('resets form when reset button is clicked', async () => {
    render(<LLMConfig />);
    
    const resetButton = screen.getByText('重置配置');
    fireEvent.click(resetButton);

    // Should show confirmation modal
    await waitFor(() => {
      expect(screen.getByText('重置配置')).toBeInTheDocument();
      expect(screen.getByText('确定要重置为默认配置吗？这将清除当前所有设置。')).toBeInTheDocument();
    });

    const confirmButton = screen.getByText('确定');
    fireEvent.click(confirmButton);

    // Form should be reset to default values
    await waitFor(() => {
      expect(screen.getByDisplayValue('0.7')).toBeInTheDocument(); // temperature
      expect(screen.getByDisplayValue('30')).toBeInTheDocument(); // timeout
      expect(screen.getByDisplayValue('3')).toBeInTheDocument(); // retry_attempts
    });
  });

  it('opens documentation link when clicked', () => {
    render(<LLMConfig />);
    
    const docLink = screen.getByText('查看文档');
    expect(docLink).toHaveAttribute('href');
    expect(docLink).toHaveAttribute('target', '_blank');
  });
});