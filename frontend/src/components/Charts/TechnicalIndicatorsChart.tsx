import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { Card, Spin, Select, Space } from 'antd';
import type { TechnicalData } from '../../types/charts';

interface TechnicalIndicatorsChartProps {
  data: TechnicalData[];
  title?: string;
  loading?: boolean;
  height?: number;
  defaultIndicator?: string;
  onIndicatorChange?: (indicator: string) => void;
}

const TechnicalIndicatorsChart: React.FC<TechnicalIndicatorsChartProps> = ({
  data,
  title = '技术指标图',
  loading = false,
  height = 400,
  defaultIndicator = 'rsi',
  onIndicatorChange,
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const [selectedIndicator, setSelectedIndicator] = React.useState(defaultIndicator);

  const indicators = [
    { value: 'rsi', label: 'RSI 相对强弱指标' },
    { value: 'macd', label: 'MACD 指标' },
    { value: 'bollinger', label: '布林带' },
    { value: 'kdj', label: 'KDJ 指标' },
  ];

  useEffect(() => {
    if (!chartRef.current || loading || !data.length) return;

    // Initialize chart
    if (chartInstance.current) {
      chartInstance.current.dispose();
    }
    chartInstance.current = echarts.init(chartRef.current);

    const dates = data.map(item => item.date);
    let option: echarts.EChartsOption = {};

    switch (selectedIndicator) {
      case 'rsi':
        option = {
          title: {
            text: 'RSI 相对强弱指标',
            left: 'center',
            textStyle: { fontSize: 14 },
          },
          tooltip: {
            trigger: 'axis',
            formatter: function (params: any) {
              const dataIndex = params[0].dataIndex;
              const rsi = data[dataIndex].rsi;
              return `
                <div>
                  <div><strong>${dates[dataIndex]}</strong></div>
                  <div>RSI: ${rsi?.toFixed(2) || 'N/A'}</div>
                </div>
              `;
            },
          },
          grid: {
            left: '10%',
            right: '10%',
            top: '20%',
            bottom: '15%',
          },
          xAxis: {
            type: 'category',
            data: dates,
          },
          yAxis: {
            type: 'value',
            min: 0,
            max: 100,
            axisLabel: {
              formatter: '{value}',
            },
          },
          series: [
            {
              name: 'RSI',
              type: 'line',
              data: data.map(item => item.rsi || null),
              lineStyle: {
                color: '#0f766e',
                width: 2,
              },
              areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: 'rgba(15, 118, 110, 0.3)' },
                  { offset: 1, color: 'rgba(15, 118, 110, 0.1)' },
                ]),
              },
              markLine: {
                data: [
                  { yAxis: 70, lineStyle: { color: '#ff4d4f', type: 'dashed' } },
                  { yAxis: 30, lineStyle: { color: '#52c41a', type: 'dashed' } },
                ],
                label: {
                  formatter: function (params: any) {
                    return params.value === 70 ? '超买线' : '超卖线';
                  },
                },
              },
            },
          ],
        };
        break;

      case 'macd':
        option = {
          title: {
            text: 'MACD 指标',
            left: 'center',
            textStyle: { fontSize: 14 },
          },
          tooltip: {
            trigger: 'axis',
            formatter: function (params: any) {
              const dataIndex = params[0].dataIndex;
              const macd = data[dataIndex].macd;
              return `
                <div>
                  <div><strong>${dates[dataIndex]}</strong></div>
                  <div>MACD: ${macd?.macd.toFixed(4) || 'N/A'}</div>
                  <div>Signal: ${macd?.signal.toFixed(4) || 'N/A'}</div>
                  <div>Histogram: ${macd?.histogram.toFixed(4) || 'N/A'}</div>
                </div>
              `;
            },
          },
          legend: {
            data: ['MACD', 'Signal', 'Histogram'],
            top: 30,
          },
          grid: {
            left: '10%',
            right: '10%',
            top: '25%',
            bottom: '15%',
          },
          xAxis: {
            type: 'category',
            data: dates,
          },
          yAxis: {
            type: 'value',
          },
          series: [
            {
              name: 'MACD',
              type: 'line',
              data: data.map(item => item.macd?.macd || null),
              lineStyle: { color: '#0f766e', width: 2 },
              showSymbol: false,
            },
            {
              name: 'Signal',
              type: 'line',
              data: data.map(item => item.macd?.signal || null),
              lineStyle: { color: '#ff4d4f', width: 2 },
              showSymbol: false,
            },
            {
              name: 'Histogram',
              type: 'bar',
              data: data.map(item => item.macd?.histogram || null),
              itemStyle: {
                color: function (params: any) {
                  return params.value >= 0 ? '#52c41a' : '#ff4d4f';
                },
              },
            },
          ],
        };
        break;

      case 'bollinger':
        option = {
          title: {
            text: '布林带',
            left: 'center',
            textStyle: { fontSize: 14 },
          },
          tooltip: {
            trigger: 'axis',
            formatter: function (params: any) {
              const dataIndex = params[0].dataIndex;
              const bollinger = data[dataIndex].bollinger;
              return `
                <div>
                  <div><strong>${dates[dataIndex]}</strong></div>
                  <div>上轨: ${bollinger?.upper.toFixed(2) || 'N/A'}</div>
                  <div>中轨: ${bollinger?.middle.toFixed(2) || 'N/A'}</div>
                  <div>下轨: ${bollinger?.lower.toFixed(2) || 'N/A'}</div>
                </div>
              `;
            },
          },
          legend: {
            data: ['上轨', '中轨', '下轨'],
            top: 30,
          },
          grid: {
            left: '10%',
            right: '10%',
            top: '25%',
            bottom: '15%',
          },
          xAxis: {
            type: 'category',
            data: dates,
          },
          yAxis: {
            type: 'value',
          },
          series: [
            {
              name: '上轨',
              type: 'line',
              data: data.map(item => item.bollinger?.upper || null),
              lineStyle: { color: '#ff4d4f', width: 1 },
              showSymbol: false,
            },
            {
              name: '中轨',
              type: 'line',
              data: data.map(item => item.bollinger?.middle || null),
              lineStyle: { color: '#0f766e', width: 2 },
              showSymbol: false,
            },
            {
              name: '下轨',
              type: 'line',
              data: data.map(item => item.bollinger?.lower || null),
              lineStyle: { color: '#52c41a', width: 1 },
              showSymbol: false,
            },
          ],
        };
        break;

      case 'kdj':
        option = {
          title: {
            text: 'KDJ 指标',
            left: 'center',
            textStyle: { fontSize: 14 },
          },
          tooltip: {
            trigger: 'axis',
            formatter: function (params: any) {
              const dataIndex = params[0].dataIndex;
              const kdj = data[dataIndex].kdj;
              return `
                <div>
                  <div><strong>${dates[dataIndex]}</strong></div>
                  <div>K: ${kdj?.k.toFixed(2) || 'N/A'}</div>
                  <div>D: ${kdj?.d.toFixed(2) || 'N/A'}</div>
                  <div>J: ${kdj?.j.toFixed(2) || 'N/A'}</div>
                </div>
              `;
            },
          },
          legend: {
            data: ['K', 'D', 'J'],
            top: 30,
          },
          grid: {
            left: '10%',
            right: '10%',
            top: '25%',
            bottom: '15%',
          },
          xAxis: {
            type: 'category',
            data: dates,
          },
          yAxis: {
            type: 'value',
            min: 0,
            max: 100,
          },
          series: [
            {
              name: 'K',
              type: 'line',
              data: data.map(item => item.kdj?.k || null),
              lineStyle: { color: '#0f766e', width: 2 },
              showSymbol: false,
            },
            {
              name: 'D',
              type: 'line',
              data: data.map(item => item.kdj?.d || null),
              lineStyle: { color: '#ff4d4f', width: 2 },
              showSymbol: false,
            },
            {
              name: 'J',
              type: 'line',
              data: data.map(item => item.kdj?.j || null),
              lineStyle: { color: '#52c41a', width: 2 },
              showSymbol: false,
            },
          ],
        };
        break;
    }

    chartInstance.current.setOption(option);

    // Handle resize
    const handleResize = () => {
      chartInstance.current?.resize();
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [data, selectedIndicator, loading, height]);

  useEffect(() => {
    return () => {
      if (chartInstance.current) {
        chartInstance.current.dispose();
      }
    };
  }, []);

  const handleIndicatorChange = (value: string) => {
    setSelectedIndicator(value);
    onIndicatorChange?.(value);
  };

  return (
    <Card 
      className="technical-indicators-chart"
      title={
        <Space>
          <span>{title}</span>
          <Select
            value={selectedIndicator}
            onChange={handleIndicatorChange}
            options={indicators}
            style={{ width: 200 }}
            size="small"
          />
        </Space>
      }
    >
      <Spin spinning={loading}>
        <div
          ref={chartRef}
          style={{ width: '100%', height: `${height}px` }}
        />
      </Spin>
    </Card>
  );
};

export default TechnicalIndicatorsChart;
