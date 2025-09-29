import * as echarts from 'echarts';
import type { ChartExportOptions, ChartTheme, StockPriceData, TechnicalData } from '../types/charts';

// Chart theme configurations
export const chartThemes: Record<string, ChartTheme> = {
  light: {
    primaryColor: '#1890ff',
    backgroundColor: '#ffffff',
    textColor: '#333333',
    gridColor: '#f0f0f0',
    upColor: '#52c41a',
    downColor: '#ff4d4f',
  },
  dark: {
    primaryColor: '#177ddc',
    backgroundColor: '#141414',
    textColor: '#ffffff',
    gridColor: '#434343',
    upColor: '#73d13d',
    downColor: '#ff7875',
  },
  colorful: {
    primaryColor: '#722ed1',
    backgroundColor: '#f6ffed',
    textColor: '#262626',
    gridColor: '#d9f7be',
    upColor: '#389e0d',
    downColor: '#cf1322',
  },
};

// Apply theme to ECharts instance
export const applyChartTheme = (chart: echarts.ECharts, theme: ChartTheme) => {
  const option = chart.getOption();
  
  // Update colors in the option
  const updatedOption = {
    ...option,
    backgroundColor: theme.backgroundColor,
    textStyle: {
      color: theme.textColor,
    },
    grid: {
      ...option.grid,
      borderColor: theme.gridColor,
    },
  };
  
  chart.setOption(updatedOption);
};

// Export chart as image
export const exportChart = async (
  chart: echarts.ECharts,
  options: ChartExportOptions = { format: 'png' }
): Promise<string> => {
  const { format, quality = 1, backgroundColor = '#ffffff', pixelRatio = 2 } = options;
  
  return chart.getDataURL({
    type: format,
    pixelRatio,
    backgroundColor,
    excludeComponents: ['toolbox'],
  });
};

// Calculate technical indicators
export const calculateTechnicalIndicators = {
  // Simple Moving Average
  sma: (data: number[], period: number): (number | null)[] => {
    const result: (number | null)[] = [];
    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        result.push(null);
      } else {
        const sum = data.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
        result.push(sum / period);
      }
    }
    return result;
  },

  // Exponential Moving Average
  ema: (data: number[], period: number): (number | null)[] => {
    const result: (number | null)[] = [];
    const multiplier = 2 / (period + 1);
    
    for (let i = 0; i < data.length; i++) {
      if (i === 0) {
        result.push(data[i]);
      } else {
        const ema = (data[i] - result[i - 1]!) * multiplier + result[i - 1]!;
        result.push(ema);
      }
    }
    return result;
  },

  // Relative Strength Index
  rsi: (data: number[], period: number = 14): (number | null)[] => {
    const result: (number | null)[] = [];
    const gains: number[] = [];
    const losses: number[] = [];
    
    for (let i = 1; i < data.length; i++) {
      const change = data[i] - data[i - 1];
      gains.push(change > 0 ? change : 0);
      losses.push(change < 0 ? Math.abs(change) : 0);
    }
    
    for (let i = 0; i < gains.length; i++) {
      if (i < period - 1) {
        result.push(null);
      } else {
        const avgGain = gains.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0) / period;
        const avgLoss = losses.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0) / period;
        
        if (avgLoss === 0) {
          result.push(100);
        } else {
          const rs = avgGain / avgLoss;
          const rsi = 100 - (100 / (1 + rs));
          result.push(rsi);
        }
      }
    }
    
    return [null, ...result]; // Add null for first data point
  },

  // MACD
  macd: (data: number[], fastPeriod: number = 12, slowPeriod: number = 26, signalPeriod: number = 9) => {
    const fastEMA = calculateTechnicalIndicators.ema(data, fastPeriod);
    const slowEMA = calculateTechnicalIndicators.ema(data, slowPeriod);
    
    const macdLine: (number | null)[] = [];
    for (let i = 0; i < data.length; i++) {
      if (fastEMA[i] !== null && slowEMA[i] !== null) {
        macdLine.push(fastEMA[i]! - slowEMA[i]!);
      } else {
        macdLine.push(null);
      }
    }
    
    const signalLine = calculateTechnicalIndicators.ema(
      macdLine.filter(v => v !== null) as number[], 
      signalPeriod
    );
    
    const histogram: (number | null)[] = [];
    let signalIndex = 0;
    for (let i = 0; i < macdLine.length; i++) {
      if (macdLine[i] !== null) {
        if (signalLine[signalIndex] !== null) {
          histogram.push(macdLine[i]! - signalLine[signalIndex]!);
        } else {
          histogram.push(null);
        }
        signalIndex++;
      } else {
        histogram.push(null);
      }
    }
    
    return {
      macd: macdLine,
      signal: signalLine,
      histogram,
    };
  },

  // Bollinger Bands
  bollinger: (data: number[], period: number = 20, stdDev: number = 2) => {
    const sma = calculateTechnicalIndicators.sma(data, period);
    const upper: (number | null)[] = [];
    const lower: (number | null)[] = [];
    
    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        upper.push(null);
        lower.push(null);
      } else {
        const slice = data.slice(i - period + 1, i + 1);
        const mean = sma[i]!;
        const variance = slice.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / period;
        const standardDeviation = Math.sqrt(variance);
        
        upper.push(mean + (standardDeviation * stdDev));
        lower.push(mean - (standardDeviation * stdDev));
      }
    }
    
    return {
      upper,
      middle: sma,
      lower,
    };
  },
};

// Format data for charts
export const formatChartData = {
  // Format stock price data for candlestick chart
  stockPrice: (data: StockPriceData[]) => ({
    dates: data.map(item => item.date),
    candlestick: data.map(item => [item.open, item.close, item.low, item.high]),
    volume: data.map(item => item.volume),
    closes: data.map(item => item.close),
  }),

  // Format technical data for line charts
  technical: (data: TechnicalData[], indicator: string) => {
    const dates = data.map(item => item.date);
    
    switch (indicator) {
      case 'rsi':
        return {
          dates,
          values: data.map(item => item.rsi || null),
        };
      case 'macd':
        return {
          dates,
          macd: data.map(item => item.macd?.macd || null),
          signal: data.map(item => item.macd?.signal || null),
          histogram: data.map(item => item.macd?.histogram || null),
        };
      case 'bollinger':
        return {
          dates,
          upper: data.map(item => item.bollinger?.upper || null),
          middle: data.map(item => item.bollinger?.middle || null),
          lower: data.map(item => item.bollinger?.lower || null),
        };
      case 'kdj':
        return {
          dates,
          k: data.map(item => item.kdj?.k || null),
          d: data.map(item => item.kdj?.d || null),
          j: data.map(item => item.kdj?.j || null),
        };
      default:
        return { dates, values: [] };
    }
  },
};

// Chart performance optimization
export const optimizeChartPerformance = (chart: echarts.ECharts) => {
  // Enable animation only for small datasets
  const option = chart.getOption();
  const seriesData = option.series?.[0]?.data;
  const dataLength = Array.isArray(seriesData) ? seriesData.length : 0;
  
  chart.setOption({
    animation: dataLength < 1000,
    animationDuration: dataLength < 500 ? 1000 : 0,
    progressive: dataLength > 1000 ? 500 : 0,
    progressiveThreshold: 1000,
  });
};

// Responsive chart sizing
export const makeChartResponsive = (chart: echarts.ECharts) => {
  const resizeHandler = () => {
    chart.resize();
  };
  
  window.addEventListener('resize', resizeHandler);
  
  // Return cleanup function
  return () => {
    window.removeEventListener('resize', resizeHandler);
  };
};

// Chart interaction helpers
export const addChartInteraction = (
  chart: echarts.ECharts,
  onInteraction?: (event: any) => void
) => {
  chart.on('click', (params) => {
    onInteraction?.({
      type: 'click',
      data: params,
      timestamp: Date.now(),
    });
  });
  
  chart.on('mouseover', (params) => {
    onInteraction?.({
      type: 'hover',
      data: params,
      timestamp: Date.now(),
    });
  });
  
  chart.on('datazoom', (params) => {
    onInteraction?.({
      type: 'zoom',
      data: params,
      timestamp: Date.now(),
    });
  });
};

export default {
  chartThemes,
  applyChartTheme,
  exportChart,
  calculateTechnicalIndicators,
  formatChartData,
  optimizeChartPerformance,
  makeChartResponsive,
  addChartInteraction,
};