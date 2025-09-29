import React, { useState } from 'react';
import { Card, Button, Space, message } from 'antd';
import { InteractiveChartDashboard } from './index';
import type { StockPriceData, TechnicalData, AnalystOpinion } from '../../types/charts';

// Mock data for demonstration
const generateMockStockData = (): StockPriceData[] => {
  const data: StockPriceData[] = [];
  const basePrice = 100;
  let currentPrice = basePrice;
  
  for (let i = 0; i < 60; i++) {
    const date = new Date();
    date.setDate(date.getDate() - (60 - i));
    
    const change = (Math.random() - 0.5) * 4;
    currentPrice += change;
    
    const open = currentPrice;
    const close = currentPrice + (Math.random() - 0.5) * 2;
    const high = Math.max(open, close) + Math.random() * 2;
    const low = Math.min(open, close) - Math.random() * 2;
    const volume = Math.floor(Math.random() * 1000000) + 500000;
    
    data.push({
      date: date.toISOString().split('T')[0],
      open: Number(open.toFixed(2)),
      close: Number(close.toFixed(2)),
      high: Number(high.toFixed(2)),
      low: Number(low.toFixed(2)),
      volume,
    });
    
    currentPrice = close;
  }
  
  return data;
};

const generateMockTechnicalData = (stockData: StockPriceData[]): TechnicalData[] => {
  return stockData.map((item, index) => ({
    date: item.date,
    rsi: Math.random() * 100,
    macd: {
      macd: (Math.random() - 0.5) * 2,
      signal: (Math.random() - 0.5) * 1.5,
      histogram: (Math.random() - 0.5) * 0.5,
    },
    bollinger: {
      upper: item.close + Math.random() * 5,
      middle: item.close,
      lower: item.close - Math.random() * 5,
    },
    kdj: {
      k: Math.random() * 100,
      d: Math.random() * 100,
      j: Math.random() * 100,
    },
  }));
};

const generateMockAnalystOpinions = (): AnalystOpinion[] => {
  const analysts = ['高盛', '摩根士丹利', '中信证券', '华泰证券', '招商证券'];
  const opinions: ('buy' | 'sell' | 'hold')[] = ['buy', 'sell', 'hold'];
  
  return analysts.map((analyst, index) => ({
    analyst,
    opinion: opinions[Math.floor(Math.random() * opinions.length)],
    confidence: Math.floor(Math.random() * 40) + 60, // 60-100
    targetPrice: 95 + Math.random() * 20, // 95-115
    currentPrice: 100,
    reasoning: `基于${analyst}的分析模型，考虑到当前市场环境和公司基本面，给出${opinions[Math.floor(Math.random() * opinions.length)]}建议。`,
    timestamp: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
  }));
};

const ChartDemo: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [stockData, setStockData] = useState<StockPriceData[]>(() => generateMockStockData());
  const [technicalData, setTechnicalData] = useState<TechnicalData[]>(() => 
    generateMockTechnicalData(stockData)
  );
  const [analystOpinions, setAnalystOpinions] = useState<AnalystOpinion[]>(() => 
    generateMockAnalystOpinions()
  );

  const handleRefresh = () => {
    setLoading(true);
    
    // Simulate API call
    setTimeout(() => {
      const newStockData = generateMockStockData();
      setStockData(newStockData);
      setTechnicalData(generateMockTechnicalData(newStockData));
      setAnalystOpinions(generateMockAnalystOpinions());
      setLoading(false);
      message.success('数据刷新成功');
    }, 1000);
  };

  const handleExport = (chartType: string) => {
    message.success(`${chartType} 图表导出成功`);
  };

  const handleSettingsChange = (settings: any) => {
    console.log('Settings changed:', settings);
  };

  return (
    <div style={{ padding: 24 }}>
      <Card 
        title="图表和数据可视化演示" 
        extra={
          <Space>
            <Button onClick={handleRefresh} loading={loading}>
              刷新数据
            </Button>
          </Space>
        }
        style={{ marginBottom: 24 }}
      >
        <p>
          这个演示展示了新的图表和数据可视化功能，包括：
        </p>
        <ul>
          <li>股价走势图（K线图 + 成交量）</li>
          <li>技术指标图（RSI、MACD、布林带、KDJ）</li>
          <li>分析师观点可视化</li>
          <li>交互式图表控制</li>
          <li>图表导出功能</li>
          <li>响应式设计</li>
        </ul>
      </Card>

      <InteractiveChartDashboard
        stockCode="000001"
        stockName="平安银行"
        priceData={stockData}
        technicalData={technicalData}
        analystOpinions={analystOpinions}
        loading={loading}
        onRefresh={handleRefresh}
        onExport={handleExport}
        onSettingsChange={handleSettingsChange}
      />
    </div>
  );
};

export default ChartDemo;