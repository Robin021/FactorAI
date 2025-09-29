import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import DataSourceConfig from './DataSourceConfig';
import { useConfigStore } from '@/stores/configStore';
import { DataSourceType } from '@/services/config';

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

const mockDataSourceConfigs = [
  {
    source_type: DataSourceType.AKSHARE,
    priority: 1,
    timeout: 30,
    cache_ttl: 3600,
    enabled: true,
  },
  {
    source_type: DataSourceType.TUSHARE,
    api_key: 'test-key',
    priority: 2,
    timeout: 30,
    cache_ttl: 3600,
    enabled: true,
  },
];

const mockConfigStore = {
  dataSourceConfigs: mockDataSourceConfigs,
  isLoading: false,
  error: null,
  testResults: {
    llm: null,
    dataSource: null,
  },
  loadDataSourceConfigs: vi.fn(),
  updateDataSourceConfigs: vi.fn(),
  testDataSourceConnection: vi.fn(),
  clearError: vi.fn(),
  clearTestResults: vi.fn(),
};

describe('DataSourceConfig', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useConfigStore as any).mockReturnValue(mockConfigStore);
  });

  it('renders data source configuration page', () => {
    render(<DataSourceConfig />);
    
    expect(screen.getByText('数据源配置管理')).toBeInTheDocument();
    expect(screen.getByText('配置和管理股票数据源，设置优先级和缓存策略')).toBeInTheDocument();
    expect(screen.getByText('添加数据源')).toBeInTheDocument();
  });

  it('loads data source configs on mount', () => {
    render(<DataSourceConfig />);
    
    expect(mockConfigStore.loadDataSourceConfigs).toHaveBeenCalledTimes(1);
  });

  it('displays existing data source configs in table', () => {
    render(<DataSourceConfig />);
    
    expect(screen.getByText('AKShare')).toBeInTheDocument();
    expect(screen.getByText('Tushare')).toBeInTheDocument();
    expect(screen.getByText('开源财经数据接口库，支持多市场数据')).toBeInTheDocument();
  });

  it('shows error message when there is an error', () => {
    (useConfigStore as any).mockReturnValue({
      ...mockConfigStore,
      error: 'Failed to load configs',
    });

    render(<DataSourceConfig />);
    
    expect(screen.getByText('配置错误')).toBeInTheDocument();
    expect(screen.getByText('Failed to load configs')).toBeInTheDocument();
  });

  it('opens add modal when add button is clicked', async () => {
    render(<DataSourceConfig />);
    
    const addButton = screen.getByText('添加数据源');
    fireEvent.click(addButton);

    await waitFor(() => {
      expect(screen.getByText('添加数据源')).toBeInTheDocument();
      expect(screen.getByLabelText('数据源类型')).toBeInTheDocument();
    });
  });

  it('opens edit modal when edit button is clicked', async () => {
    render(<DataSourceConfig />);
    
    const editButtons = screen.getAllByText('编辑');
    fireEvent.click(editButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('编辑数据源')).toBeInTheDocument();
    });
  });

  it('calls testDataSourceConnection when test button is clicked', async () => {
    const mockTest = vi.fn().mockResolvedValue({});
    (useConfigStore as any).mockReturnValue({
      ...mockConfigStore,
      testDataSourceConnection: mockTest,
    });

    render(<DataSourceConfig />);
    
    const testButtons = screen.getAllByText('测试');
    fireEvent.click(testButtons[0]);

    await waitFor(() => {
      expect(mockTest).toHaveBeenCalledWith(mockDataSourceConfigs[0]);
    });
  });

  it('shows test results modal when test completes', async () => {
    (useConfigStore as any).mockReturnValue({
      ...mockConfigStore,
      testResults: {
        llm: null,
        dataSource: { success: true, message: 'Connection successful' },
      },
    });

    render(<DataSourceConfig />);
    
    // Test results modal should be visible
    expect(screen.getByText('连接测试结果')).toBeInTheDocument();
    expect(screen.getByText('连接成功')).toBeInTheDocument();
    expect(screen.getByText('Connection successful')).toBeInTheDocument();
  });

  it('moves priority up when up button is clicked', async () => {
    const mockUpdate = vi.fn().mockResolvedValue([]);
    (useConfigStore as any).mockReturnValue({
      ...mockConfigStore,
      updateDataSourceConfigs: mockUpdate,
    });

    render(<DataSourceConfig />);
    
    // Click up button for second item (Tushare)
    const upButtons = screen.getAllByRole('button', { name: /up/i });
    fireEvent.click(upButtons[1]);

    await waitFor(() => {
      expect(mockUpdate).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({ source_type: DataSourceType.TUSHARE, priority: 1 }),
          expect.objectContaining({ source_type: DataSourceType.AKSHARE, priority: 2 }),
        ])
      );
    });
  });

  it('deletes data source when delete is confirmed', async () => {
    const mockUpdate = vi.fn().mockResolvedValue([]);
    (useConfigStore as any).mockReturnValue({
      ...mockConfigStore,
      updateDataSourceConfigs: mockUpdate,
    });

    render(<DataSourceConfig />);
    
    const deleteButtons = screen.getAllByText('删除');
    fireEvent.click(deleteButtons[0]);

    // Confirm deletion
    await waitFor(() => {
      const confirmButton = screen.getByText('确定');
      fireEvent.click(confirmButton);
    });

    await waitFor(() => {
      expect(mockUpdate).toHaveBeenCalledWith([
        expect.objectContaining({ source_type: DataSourceType.TUSHARE, priority: 1 }),
      ]);
    });
  });

  it('saves new data source config', async () => {
    const mockUpdate = vi.fn().mockResolvedValue([]);
    (useConfigStore as any).mockReturnValue({
      ...mockConfigStore,
      updateDataSourceConfigs: mockUpdate,
    });

    render(<DataSourceConfig />);
    
    // Open add modal
    const addButton = screen.getByText('添加数据源');
    fireEvent.click(addButton);

    await waitFor(() => {
      // Select data source type
      const sourceTypeSelect = screen.getByLabelText('数据源类型');
      fireEvent.mouseDown(sourceTypeSelect);
    });

    await waitFor(() => {
      const finnhubOption = screen.getByText('Finnhub');
      fireEvent.click(finnhubOption);
    });

    // Fill in API key
    const apiKeyInput = screen.getByLabelText('API Key');
    fireEvent.change(apiKeyInput, { target: { value: 'test-api-key' } });

    // Save
    const saveButton = screen.getByText('保存');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockUpdate).toHaveBeenCalledWith(
        expect.arrayContaining([
          ...mockDataSourceConfigs,
          expect.objectContaining({
            source_type: DataSourceType.FINNHUB,
            api_key: 'test-api-key',
          }),
        ])
      );
    });
  });

  it('exports configuration when export button is clicked', () => {
    // Mock URL.createObjectURL and related functions
    global.URL.createObjectURL = vi.fn(() => 'mock-url');
    global.URL.revokeObjectURL = vi.fn();
    
    const mockAppendChild = vi.fn();
    const mockRemoveChild = vi.fn();
    const mockClick = vi.fn();
    
    Object.defineProperty(document, 'createElement', {
      value: vi.fn(() => ({
        href: '',
        download: '',
        click: mockClick,
      })),
    });
    
    Object.defineProperty(document.body, 'appendChild', {
      value: mockAppendChild,
    });
    
    Object.defineProperty(document.body, 'removeChild', {
      value: mockRemoveChild,
    });

    render(<DataSourceConfig />);
    
    const exportButton = screen.getByText('导出配置');
    fireEvent.click(exportButton);

    expect(mockClick).toHaveBeenCalled();
    expect(global.URL.createObjectURL).toHaveBeenCalled();
  });

  it('shows loading state when isLoading is true', () => {
    (useConfigStore as any).mockReturnValue({
      ...mockConfigStore,
      isLoading: true,
    });

    render(<DataSourceConfig />);
    
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('refreshes configs when refresh button is clicked', () => {
    render(<DataSourceConfig />);
    
    const refreshButton = screen.getByText('刷新');
    fireEvent.click(refreshButton);

    expect(mockConfigStore.loadDataSourceConfigs).toHaveBeenCalledTimes(2); // Once on mount, once on click
  });

  it('shows API key requirement for Tushare', async () => {
    render(<DataSourceConfig />);
    
    // Open add modal
    const addButton = screen.getByText('添加数据源');
    fireEvent.click(addButton);

    await waitFor(() => {
      // Select Tushare
      const sourceTypeSelect = screen.getByLabelText('数据源类型');
      fireEvent.mouseDown(sourceTypeSelect);
    });

    await waitFor(() => {
      const tushareOption = screen.getByText('Tushare');
      fireEvent.click(tushareOption);
    });

    await waitFor(() => {
      expect(screen.getByLabelText('API Key')).toBeInTheDocument();
      expect(screen.getByText('专业的股票数据接口，提供全面的A股数据')).toBeInTheDocument();
    });
  });

  it('does not show API key field for AKShare', async () => {
    render(<DataSourceConfig />);
    
    // Open add modal
    const addButton = screen.getByText('添加数据源');
    fireEvent.click(addButton);

    await waitFor(() => {
      // AKShare should be selected by default
      expect(screen.queryByLabelText('API Key')).not.toBeInTheDocument();
    });
  });
});