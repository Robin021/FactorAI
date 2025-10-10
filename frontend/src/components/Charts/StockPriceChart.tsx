import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { Card, Spin } from 'antd';
import type { StockPriceData } from '../../types/charts';

interface StockPriceChartProps {
  data: StockPriceData[];
  title?: string;
  loading?: boolean;
  height?: number;
  showVolume?: boolean;
}

const StockPriceChart: React.FC<StockPriceChartProps> = ({
  data,
  title = '股价走势图',
  loading = false,
  height = 500,
  showVolume = true,
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!chartRef.current || loading || !data.length) return;

    // Initialize chart
    if (chartInstance.current) {
      chartInstance.current.dispose();
    }
    chartInstance.current = echarts.init(chartRef.current);

    // Prepare data
    const dates = data.map(item => item.date);
    const candlestickData = data.map(item => [item.open, item.close, item.low, item.high]);
    const volumeData = data.map(item => item.volume);

    // Calculate moving averages
    const ma5 = calculateMA(data.map(item => item.close), 5);
    const ma10 = calculateMA(data.map(item => item.close), 10);
    const ma20 = calculateMA(data.map(item => item.close), 20);

    const option: echarts.EChartsOption = {
      title: {
        text: title,
        left: 'center',
        textStyle: {
          fontSize: 16,
          fontWeight: 'bold',
        },
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
        formatter: function (params: any) {
          const dataIndex = params[0].dataIndex;
          const item = data[dataIndex];
          return `
            <div>
              <div><strong>${item.date}</strong></div>
              <div>开盘: ${item.open.toFixed(2)}</div>
              <div>收盘: ${item.close.toFixed(2)}</div>
              <div>最高: ${item.high.toFixed(2)}</div>
              <div>最低: ${item.low.toFixed(2)}</div>
              <div>成交量: ${(item.volume / 10000).toFixed(2)}万</div>
            </div>
          `;
        },
      },
      legend: {
        data: ['K线', 'MA5', 'MA10', 'MA20', '成交量'],
        top: 30,
      },
      grid: [
        {
          left: '10%',
          right: '8%',
          height: showVolume ? '50%' : '70%',
          top: '15%',
        },
        ...(showVolume ? [{
          left: '10%',
          right: '8%',
          top: '70%',
          height: '20%',
        }] : []),
      ],
      xAxis: [
        {
          type: 'category',
          data: dates,
          scale: true,
          boundaryGap: false,
          axisLine: { onZero: false },
          splitLine: { show: false },
          splitNumber: 20,
          min: 'dataMin',
          max: 'dataMax',
        },
        ...(showVolume ? [{
          type: 'category',
          gridIndex: 1,
          data: dates,
          scale: true,
          boundaryGap: false,
          axisLine: { onZero: false },
          axisTick: { show: false },
          splitLine: { show: false },
          axisLabel: { show: false },
          splitNumber: 20,
          min: 'dataMin',
          max: 'dataMax',
        }] : []),
      ],
      yAxis: [
        {
          scale: true,
          splitArea: {
            show: true,
          },
        },
        ...(showVolume ? [{
          scale: true,
          gridIndex: 1,
          splitNumber: 2,
          axisLabel: { show: false },
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { show: false },
        }] : []),
      ],
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: showVolume ? [0, 1] : [0],
          start: 50,
          end: 100,
        },
        {
          show: true,
          xAxisIndex: showVolume ? [0, 1] : [0],
          type: 'slider',
          top: '90%',
          start: 50,
          end: 100,
        },
      ],
      series: [
        {
          name: 'K线',
          type: 'candlestick',
          data: candlestickData,
          itemStyle: {
            color: '#ef232a',
            color0: '#14b143',
            borderColor: '#ef232a',
            borderColor0: '#14b143',
          },
          markPoint: {
            label: {
              formatter: function (param: any) {
                return param != null ? Math.round(param.value) + '' : '';
              },
            },
            data: [
              {
                name: 'Mark',
                coord: ['2013/5/31', 2300],
                value: 2300,
                itemStyle: {
                  color: 'rgb(41,60,85)',
                },
              },
              {
                name: 'highest value',
                type: 'max',
                valueDim: 'highest',
              },
              {
                name: 'lowest value',
                type: 'min',
                valueDim: 'lowest',
              },
              {
                name: 'average value on close',
                type: 'average',
                valueDim: 'close',
              },
            ],
          },
          markLine: {
            symbol: ['none', 'none'],
            data: [
              [
                {
                  name: 'from lowest to highest',
                  type: 'min',
                  valueDim: 'lowest',
                  symbol: 'circle',
                  symbolSize: 10,
                  label: {
                    show: false,
                  },
                  emphasis: {
                    label: {
                      show: false,
                    },
                  },
                },
                {
                  type: 'max',
                  valueDim: 'highest',
                  symbol: 'circle',
                  symbolSize: 10,
                  label: {
                    show: false,
                  },
                  emphasis: {
                    label: {
                      show: false,
                    },
                  },
                },
              ],
            ],
          },
        },
        {
          name: 'MA5',
          type: 'line',
          data: ma5,
          smooth: true,
          lineStyle: {
            opacity: 0.8,
            width: 1,
            color: '#0f766e',
          },
          showSymbol: false,
        },
        {
          name: 'MA10',
          type: 'line',
          data: ma10,
          smooth: true,
          lineStyle: {
            opacity: 0.8,
            width: 1,
            color: '#52c41a',
          },
          showSymbol: false,
        },
        {
          name: 'MA20',
          type: 'line',
          data: ma20,
          smooth: true,
          lineStyle: {
            opacity: 0.8,
            width: 1,
            color: '#faad14',
          },
          showSymbol: false,
        },
        ...(showVolume ? [{
          name: '成交量',
          type: 'bar',
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: volumeData,
          itemStyle: {
            color: function (params: any) {
              const dataIndex = params.dataIndex;
              const currentPrice = data[dataIndex].close;
              const prevPrice = dataIndex > 0 ? data[dataIndex - 1].close : currentPrice;
              return currentPrice >= prevPrice ? '#ef232a' : '#14b143';
            },
          },
        }] : []),
      ],
    };

    chartInstance.current.setOption(option);

    // Handle resize
    const handleResize = () => {
      chartInstance.current?.resize();
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [data, title, loading, height, showVolume]);

  useEffect(() => {
    return () => {
      if (chartInstance.current) {
        chartInstance.current.dispose();
      }
    };
  }, []);

  // Calculate moving average
  function calculateMA(data: number[], dayCount: number): (number | null)[] {
    const result: (number | null)[] = [];
    for (let i = 0; i < data.length; i++) {
      if (i < dayCount - 1) {
        result.push(null);
      } else {
        let sum = 0;
        for (let j = 0; j < dayCount; j++) {
          sum += data[i - j];
        }
        result.push(sum / dayCount);
      }
    }
    return result;
  }

  return (
    <Card className="stock-price-chart">
      <Spin spinning={loading}>
        <div
          ref={chartRef}
          style={{ width: '100%', height: `${height}px` }}
        />
      </Spin>
    </Card>
  );
};

export default StockPriceChart;
