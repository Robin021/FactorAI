import React from 'react';
import { Card, Empty, Row, Col, Button, Space, Tooltip, message } from 'antd';
import { DownloadOutlined, FullscreenOutlined, SettingOutlined } from '@ant-design/icons';
import * as echarts from 'echarts';
import './ChartViewer.css';

interface ChartData {
  id: string;
  title: string;
  type: 'line' | 'bar' | 'pie' | 'candlestick' | 'scatter' | 'heatmap';
  data: any;
  options?: any;
  exportable?: boolean;
}

interface ChartViewerProps {
  charts: ChartData[];
  onExport?: (chartId: string, format: 'png' | 'jpg' | 'svg') => void;
  onFullscreen?: (chartId: string) => void;
  interactive?: boolean;
}

const ChartViewer: React.FC<ChartViewerProps> = ({ 
  charts, 
  onExport, 
  onFullscreen, 
  interactive = true 
}) => {
  const chartRefs = React.useRef<{ [key: string]: HTMLDivElement | null }>({});
  const chartInstances = React.useRef<{ [key: string]: echarts.ECharts }>({});

  React.useEffect(() => {
    // Initialize charts
    charts.forEach((chart) => {
      const chartElement = chartRefs.current[chart.id];
      if (chartElement) {
        // Dispose existing chart instance
        if (chartInstances.current[chart.id]) {
          chartInstances.current[chart.id].dispose();
        }

        // Create new chart instance
        const chartInstance = echarts.init(chartElement);
        chartInstances.current[chart.id] = chartInstance;

        // Set chart options
        const options = getChartOptions(chart);
        chartInstance.setOption(options);

        // Handle resize
        const handleResize = () => {
          chartInstance.resize();
        };

        window.addEventListener('resize', handleResize);

        // Cleanup function
        return () => {
          window.removeEventListener('resize', handleResize);
        };
      }
    });

    // Cleanup on unmount
    return () => {
      Object.values(chartInstances.current).forEach((instance) => {
        instance.dispose();
      });
    };
  }, [charts]);

  const getChartOptions = (chart: ChartData) => {
    const baseOptions = {
      title: {
        text: chart.title,
        left: 'center',
        textStyle: {
          fontSize: 16,
          fontWeight: 'bold',
        },
      },
      tooltip: {
        trigger: 'axis',
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true,
      },
      ...chart.options,
    };

    switch (chart.type) {
      case 'line':
        return {
          ...baseOptions,
          xAxis: {
            type: 'category',
            data: chart.data.xAxis || [],
          },
          yAxis: {
            type: 'value',
          },
          series: [
            {
              type: 'line',
              data: chart.data.series || [],
              smooth: true,
              lineStyle: {
                width: 2,
              },
              itemStyle: {
                color: '#1890ff',
              },
            },
          ],
        };

      case 'bar':
        return {
          ...baseOptions,
          xAxis: {
            type: 'category',
            data: chart.data.xAxis || [],
          },
          yAxis: {
            type: 'value',
          },
          series: [
            {
              type: 'bar',
              data: chart.data.series || [],
              itemStyle: {
                color: '#52c41a',
              },
            },
          ],
        };

      case 'pie':
        return {
          ...baseOptions,
          tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b}: {c} ({d}%)',
          },
          series: [
            {
              name: chart.title,
              type: 'pie',
              radius: '50%',
              data: chart.data.series || [],
              emphasis: {
                itemStyle: {
                  shadowBlur: 10,
                  shadowOffsetX: 0,
                  shadowColor: 'rgba(0, 0, 0, 0.5)',
                },
              },
            },
          ],
        };

      case 'candlestick':
        return {
          ...baseOptions,
          xAxis: {
            type: 'category',
            data: chart.data.xAxis || [],
          },
          yAxis: {
            type: 'value',
            scale: true,
          },
          series: [
            {
              type: 'candlestick',
              data: chart.data.series || [],
              itemStyle: {
                color: '#ef232a',
                color0: '#14b143',
                borderColor: '#ef232a',
                borderColor0: '#14b143',
              },
            },
          ],
        };

      case 'scatter':
        return {
          ...baseOptions,
          xAxis: {
            type: 'value',
            scale: true,
          },
          yAxis: {
            type: 'value',
            scale: true,
          },
          series: [
            {
              type: 'scatter',
              data: chart.data.series || [],
              symbolSize: function (data: any) {
                return Math.sqrt(data[2] || 20);
              },
              itemStyle: {
                color: '#1890ff',
                opacity: 0.6,
              },
            },
          ],
        };

      case 'heatmap':
        return {
          ...baseOptions,
          tooltip: {
            position: 'top',
            formatter: function (params: any) {
              return `${params.data[0]}, ${params.data[1]}: ${params.data[2]}`;
            },
          },
          grid: {
            height: '50%',
            top: '10%',
          },
          xAxis: {
            type: 'category',
            data: chart.data.xAxis || [],
            splitArea: {
              show: true,
            },
          },
          yAxis: {
            type: 'category',
            data: chart.data.yAxis || [],
            splitArea: {
              show: true,
            },
          },
          visualMap: {
            min: 0,
            max: 10,
            calculable: true,
            orient: 'horizontal',
            left: 'center',
            bottom: '15%',
          },
          series: [
            {
              type: 'heatmap',
              data: chart.data.series || [],
              label: {
                show: true,
              },
              emphasis: {
                itemStyle: {
                  shadowBlur: 10,
                  shadowColor: 'rgba(0, 0, 0, 0.5)',
                },
              },
            },
          ],
        };

      default:
        return baseOptions;
    }
  };

  const handleExport = (chartId: string, format: 'png' | 'jpg' | 'svg' = 'png') => {
    const chartInstance = chartInstances.current[chartId];
    if (!chartInstance) {
      message.error('图表实例不存在');
      return;
    }

    try {
      const url = chartInstance.getDataURL({
        type: format,
        pixelRatio: 2,
        backgroundColor: '#fff',
      });

      // Create download link
      const link = document.createElement('a');
      link.download = `chart_${chartId}_${Date.now()}.${format}`;
      link.href = url;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      message.success('图表导出成功');
      onExport?.(chartId, format);
    } catch (error) {
      message.error('图表导出失败');
      console.error('Chart export error:', error);
    }
  };

  const handleFullscreen = (chartId: string) => {
    onFullscreen?.(chartId);
  };

  const renderChartActions = (chart: ChartData) => {
    if (!interactive) return null;

    return (
      <div className="chart-actions">
        <Space>
          {chart.exportable !== false && (
            <Tooltip title="导出图表">
              <Button
                type="text"
                size="small"
                icon={<DownloadOutlined />}
                onClick={() => handleExport(chart.id)}
              />
            </Tooltip>
          )}
          <Tooltip title="全屏显示">
            <Button
              type="text"
              size="small"
              icon={<FullscreenOutlined />}
              onClick={() => handleFullscreen(chart.id)}
            />
          </Tooltip>
        </Space>
      </div>
    );
  };

  if (!charts || charts.length === 0) {
    return (
      <Empty
        description="暂无图表数据"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      />
    );
  }

  return (
    <div className="chart-viewer">
      <Row gutter={[16, 16]}>
        {charts.map((chart) => (
          <Col xs={24} lg={12} key={chart.id}>
            <Card 
              className="chart-card"
              title={chart.title}
              extra={renderChartActions(chart)}
            >
              <div
                ref={(el) => (chartRefs.current[chart.id] = el)}
                className="chart-container"
                style={{ width: '100%', height: '400px' }}
              />
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
};

export default ChartViewer;