// Chart data types for the visualization components

export interface StockPriceData {
  date: string;
  open: number;
  close: number;
  high: number;
  low: number;
  volume: number;
}

export interface TechnicalData {
  date: string;
  rsi?: number;
  macd?: {
    macd: number;
    signal: number;
    histogram: number;
  };
  bollinger?: {
    upper: number;
    middle: number;
    lower: number;
  };
  kdj?: {
    k: number;
    d: number;
    j: number;
  };
}

export interface AnalystOpinion {
  analyst: string;
  opinion: 'buy' | 'sell' | 'hold';
  confidence: number; // 0-100
  targetPrice?: number;
  currentPrice?: number;
  reasoning: string;
  timestamp: string;
}

export interface ChartData {
  id: string;
  title: string;
  type: 'line' | 'bar' | 'pie' | 'candlestick' | 'scatter' | 'heatmap';
  data: any;
  options?: any;
  exportable?: boolean;
}

export interface ChartSettings {
  showVolume: boolean;
  chartHeight: number;
  timeRange: [string, string] | null;
  technicalIndicator: string;
  autoRefresh: boolean;
  refreshInterval: number; // seconds
}

export interface ChartExportOptions {
  format: 'png' | 'jpg' | 'svg' | 'pdf';
  quality?: number;
  backgroundColor?: string;
  pixelRatio?: number;
}

export interface ChartTheme {
  primaryColor: string;
  backgroundColor: string;
  textColor: string;
  gridColor: string;
  upColor: string;
  downColor: string;
}

// Chart interaction events
export interface ChartInteractionEvent {
  type: 'click' | 'hover' | 'zoom' | 'brush';
  data: any;
  chartId: string;
  timestamp: number;
}

// Chart performance metrics
export interface ChartPerformanceMetrics {
  renderTime: number;
  dataPoints: number;
  memoryUsage: number;
  fps?: number;
}

// Chart configuration for different analysis types
export interface AnalysisChartConfig {
  fundamental: {
    charts: string[];
    defaultLayout: 'grid' | 'tabs' | 'stack';
    refreshInterval: number;
  };
  technical: {
    indicators: string[];
    timeframes: string[];
    overlays: string[];
  };
  sentiment: {
    sources: string[];
    aggregation: 'weighted' | 'simple' | 'exponential';
    timeWindow: number;
  };
}

export default {
  StockPriceData,
  TechnicalData,
  AnalystOpinion,
  ChartData,
  ChartSettings,
  ChartExportOptions,
  ChartTheme,
  ChartInteractionEvent,
  ChartPerformanceMetrics,
  AnalysisChartConfig,
};