// 简单的测试文件来验证 AnalysisReport 组件的类型
import React from 'react';

// 模拟数据结构
const mockAnalysis = {
  id: 'test-id',
  stockCode: 'AAPL',
  status: 'completed' as const,
  createdAt: new Date().toISOString(),
  completedAt: new Date().toISOString(),
  resultData: {
    decision: {
      action: '卖出',
      target_price: 245,
      confidence: 0.75,
      risk_score: 0.65,
      reasoning: '基于分析团队的综合评估，建议卖出'
    },
    market_report: '市场分析报告内容...',
    fundamentals_report: '基本面分析报告内容...',
    sentiment_report: '情绪分析报告内容...',
    news_report: '新闻分析报告内容...'
  }
};

// 测试报告数据结构
const testReportSections = {
  overview: {
    title: '概览',
    data: {
      overallScore: 7.5,
      targetPrice: 245,
      recommendation: '卖出',
      summary: '基于分析团队的综合评估，建议卖出',
      riskScore: 6.5
    }
  },
  fundamental: {
    title: '基本面分析',
    data: {
      report: '基本面分析报告内容...',
      summary: '基本面分析报告'
    }
  }
};

// 验证类型兼容性
const testData = testReportSections.overview.data;
console.log('Overview data:', testData.overallScore, testData.targetPrice);

const testFundamental = testReportSections.fundamental.data;
console.log('Fundamental data:', testFundamental.report, testFundamental.summary);

export default function TestAnalysisReport() {
  return (
    <div>
      <h1>Analysis Report Type Test</h1>
      <p>Stock: {mockAnalysis.stockCode}</p>
      <p>Status: {mockAnalysis.status}</p>
      <p>Recommendation: {mockAnalysis.resultData.decision.action}</p>
    </div>
  );
}