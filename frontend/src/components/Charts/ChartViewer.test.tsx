import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import ChartViewer from './ChartViewer';
import type { ChartData } from '../../types/charts';

// Mock ECharts
vi.mock('echarts', () => ({
  init: vi.fn(() => ({
    setOption: vi.fn(),
    dispose: vi.fn(),
    resize: vi.fn(),
    getDataURL: vi.fn(() => 'data:image/png;base64,mock-image-data'),
  })),
  graphic: {
    LinearGradient: vi.fn(),
  },
}));

// Mock message from antd
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

describe('ChartViewer', () => {
  const mockCharts: ChartData[] = [
    {
      id: 'chart1',
      title: '测试图表1',
      type: 'line',
      data: {
        xAxis: ['2023-01', '2023-02', '2023-03'],
        series: [100, 120, 110],
      },
      exportable: true,
    },
    {
      id: 'chart2',
      title: '测试图表2',
      type: 'bar',
      data: {
        xAxis: ['A', 'B', 'C'],
        series: [10, 20, 15],
      },
      exportable: false,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders empty state when no charts provided', () => {
    render(<ChartViewer charts={[]} />);
    expect(screen.getByText('暂无图表数据')).toBeInTheDocument();
  });

  it('renders charts when data is provided', () => {
    render(<ChartViewer charts={mockCharts} />);
    
    expect(screen.getByText('测试图表1')).toBeInTheDocument();
    expect(screen.getByText('测试图表2')).toBeInTheDocument();
  });

  it('shows chart actions when interactive is true', () => {
    render(<ChartViewer charts={mockCharts} interactive={true} />);
    
    // Should show export button for exportable chart
    const exportButtons = screen.getAllByRole('button');
    expect(exportButtons.length).toBeGreaterThan(0);
  });

  it('hides chart actions when interactive is false', () => {
    render(<ChartViewer charts={mockCharts} interactive={false} />);
    
    // Should not show action buttons
    const exportButtons = screen.queryAllByLabelText('导出图表');
    expect(exportButtons).toHaveLength(0);
  });

  it('calls onExport when export button is clicked', async () => {
    const mockOnExport = vi.fn();
    render(
      <ChartViewer 
        charts={mockCharts} 
        onExport={mockOnExport} 
        interactive={true} 
      />
    );
    
    // Find button by icon aria-label
    const exportButton = screen.getAllByRole('button')[0]; // First button should be export
    fireEvent.click(exportButton);
    
    await waitFor(() => {
      expect(mockOnExport).toHaveBeenCalledWith('chart1', 'png');
    });
  });

  it('calls onFullscreen when fullscreen button is clicked', () => {
    const mockOnFullscreen = vi.fn();
    render(
      <ChartViewer 
        charts={mockCharts} 
        onFullscreen={mockOnFullscreen} 
        interactive={true} 
      />
    );
    
    // Find button by icon aria-label
    const fullscreenButton = screen.getAllByRole('button')[1]; // Second button should be fullscreen
    fireEvent.click(fullscreenButton);
    
    expect(mockOnFullscreen).toHaveBeenCalledWith('chart1');
  });

  it('handles different chart types correctly', () => {
    const chartTypes: ChartData[] = [
      {
        id: 'line-chart',
        title: '线图',
        type: 'line',
        data: { xAxis: ['A'], series: [1] },
      },
      {
        id: 'bar-chart',
        title: '柱图',
        type: 'bar',
        data: { xAxis: ['A'], series: [1] },
      },
      {
        id: 'pie-chart',
        title: '饼图',
        type: 'pie',
        data: { series: [{ name: 'A', value: 1 }] },
      },
      {
        id: 'candlestick-chart',
        title: 'K线图',
        type: 'candlestick',
        data: { xAxis: ['A'], series: [[1, 2, 0.5, 1.5]] },
      },
      {
        id: 'scatter-chart',
        title: '散点图',
        type: 'scatter',
        data: { series: [[1, 2]] },
      },
      {
        id: 'heatmap-chart',
        title: '热力图',
        type: 'heatmap',
        data: { 
          xAxis: ['A'], 
          yAxis: ['B'], 
          series: [[0, 0, 5]] 
        },
      },
    ];

    render(<ChartViewer charts={chartTypes} />);
    
    chartTypes.forEach(chart => {
      expect(screen.getByText(chart.title)).toBeInTheDocument();
    });
  });

  it('applies custom options to charts', () => {
    const chartsWithOptions: ChartData[] = [
      {
        id: 'custom-chart',
        title: '自定义图表',
        type: 'line',
        data: { xAxis: ['A'], series: [1] },
        options: {
          color: ['#ff0000'],
          title: { textStyle: { color: '#ff0000' } },
        },
      },
    ];

    render(<ChartViewer charts={chartsWithOptions} />);
    expect(screen.getByText('自定义图表')).toBeInTheDocument();
  });

  it('handles chart resize on window resize', () => {
    const { unmount } = render(<ChartViewer charts={mockCharts} />);
    
    // Simulate window resize
    fireEvent(window, new Event('resize'));
    
    // Should not throw error
    expect(() => unmount()).not.toThrow();
  });

  it('cleans up chart instances on unmount', () => {
    const { unmount } = render(<ChartViewer charts={mockCharts} />);
    
    // Should not throw error when unmounting
    expect(() => unmount()).not.toThrow();
  });
});