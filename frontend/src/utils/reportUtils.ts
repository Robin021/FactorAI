import { Analysis } from '@/types';
import { analysisService } from '@/services/analysis';
import { message } from 'antd';

export interface ExportOptions {
  format: 'pdf' | 'excel' | 'word' | 'json';
  includeCharts?: boolean;
  includeDetailedAnalysis?: boolean;
  customTitle?: string;
}

export interface ShareOptions {
  method: 'email' | 'link' | 'wechat';
  email?: string;
  message?: string;
  expiresIn?: number; // in hours
}

export class ReportUtils {
  // Export analysis report
  static async exportReport(analysis: Analysis, options: ExportOptions): Promise<void> {
    try {
      const blob = await analysisService.exportAnalysis(analysis.id, options.format);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      // Generate filename
      const timestamp = new Date().toISOString().split('T')[0];
      const filename = `${analysis.stockCode}_分析报告_${timestamp}.${this.getFileExtension(options.format)}`;
      link.download = filename;
      
      // Trigger download
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // Clean up
      window.URL.revokeObjectURL(url);
      
      message.success(`报告已导出为 ${options.format.toUpperCase()} 格式`);
    } catch (error: any) {
      message.error(`导出失败: ${error.message}`);
      throw error;
    }
  }

  // Share analysis report
  static async shareReport(analysis: Analysis, options: ShareOptions): Promise<string | null> {
    try {
      const result = await analysisService.shareAnalysis(analysis.id, options.method, options);
      
      if (options.method === 'link' && result.shareUrl) {
        // Copy to clipboard
        await navigator.clipboard.writeText(result.shareUrl);
        message.success('分享链接已复制到剪贴板');
        return result.shareUrl;
      } else if (options.method === 'email') {
        message.success('邮件分享请求已发送');
      } else if (options.method === 'wechat') {
        message.success('微信分享二维码已生成');
      }
      
      return null;
    } catch (error: any) {
      message.error(`分享失败: ${error.message}`);
      throw error;
    }
  }

  // Print report
  static printReport(analysis: Analysis, options?: {
    includeCharts?: boolean;
    includeDetailedAnalysis?: boolean;
  }): void {
    try {
      // Create a new window for printing
      const printWindow = window.open('', '_blank');
      if (!printWindow) {
        throw new Error('无法打开打印窗口，请检查浏览器设置');
      }

      // Generate print content
      const printContent = this.generatePrintHTML(analysis, options);
      
      printWindow.document.write(printContent);
      printWindow.document.close();
      
      // Wait for content to load, then print
      printWindow.onload = () => {
        printWindow.print();
        printWindow.close();
      };
      
      message.success('正在准备打印...');
    } catch (error: any) {
      message.error(`打印失败: ${error.message}`);
      throw error;
    }
  }

  // Compare multiple analyses
  static async compareAnalyses(analyses: Analysis[]): Promise<{
    analyses: Analysis[];
    comparison: Record<string, any>;
  }> {
    try {
      const analysisIds = analyses.map(a => a.id);
      const result = await analysisService.compareAnalyses(analysisIds);
      
      message.success(`成功对比 ${analyses.length} 个分析结果`);
      return result;
    } catch (error: any) {
      message.error(`对比失败: ${error.message}`);
      throw error;
    }
  }

  // Generate summary statistics for multiple analyses
  static generateComparisonSummary(analyses: Analysis[]): {
    averageScore: number;
    highestScore: { score: number; stockCode: string };
    lowestScore: { score: number; stockCode: string };
    recommendationDistribution: Record<string, number>;
    averageTargetPrice: number;
  } {
    const validAnalyses = analyses.filter(a => a.resultData?.overallScore);
    
    if (validAnalyses.length === 0) {
      return {
        averageScore: 0,
        highestScore: { score: 0, stockCode: '' },
        lowestScore: { score: 0, stockCode: '' },
        recommendationDistribution: {},
        averageTargetPrice: 0,
      };
    }

    const scores = validAnalyses.map(a => a.resultData?.overallScore || 0);
    const targetPrices = validAnalyses.map(a => a.resultData?.targetPrice || 0).filter(p => p > 0);
    const recommendations = validAnalyses.map(a => a.resultData?.recommendation).filter(Boolean);

    const averageScore = scores.reduce((sum, score) => sum + score, 0) / scores.length;
    const maxScore = Math.max(...scores);
    const minScore = Math.min(...scores);
    
    const highestScoreAnalysis = validAnalyses.find(a => a.resultData?.overallScore === maxScore);
    const lowestScoreAnalysis = validAnalyses.find(a => a.resultData?.overallScore === minScore);
    
    const recommendationDistribution = recommendations.reduce((acc, rec) => {
      acc[rec] = (acc[rec] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const averageTargetPrice = targetPrices.length > 0 
      ? targetPrices.reduce((sum, price) => sum + price, 0) / targetPrices.length 
      : 0;

    return {
      averageScore: Number(averageScore.toFixed(1)),
      highestScore: { 
        score: maxScore, 
        stockCode: highestScoreAnalysis?.stockCode || '' 
      },
      lowestScore: { 
        score: minScore, 
        stockCode: lowestScoreAnalysis?.stockCode || '' 
      },
      recommendationDistribution,
      averageTargetPrice: Number(averageTargetPrice.toFixed(2)),
    };
  }

  // Get file extension for export format
  private static getFileExtension(format: string): string {
    const extensions: Record<string, string> = {
      pdf: 'pdf',
      excel: 'xlsx',
      word: 'docx',
      json: 'json',
    };
    return extensions[format] || 'txt';
  }

  // Generate HTML content for printing
  private static generatePrintHTML(analysis: Analysis, options?: {
    includeCharts?: boolean;
    includeDetailedAnalysis?: boolean;
  }): string {
    const resultData = analysis.resultData || {};
    const includeCharts = options?.includeCharts ?? false;
    const includeDetailedAnalysis = options?.includeDetailedAnalysis ?? true;

    return `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <title>${analysis.stockCode} 分析报告</title>
        <style>
          body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 20px;
          }
          .header {
            text-align: center;
            border-bottom: 2px solid #1890ff;
            padding-bottom: 20px;
            margin-bottom: 30px;
          }
          .header h1 {
            color: #1890ff;
            margin: 0;
            font-size: 28px;
          }
          .header .stock-code {
            font-size: 20px;
            font-weight: bold;
            margin: 10px 0;
          }
          .header .date {
            color: #666;
            font-size: 14px;
          }
          .section {
            margin-bottom: 30px;
            page-break-inside: avoid;
          }
          .section h2 {
            color: #1890ff;
            border-bottom: 1px solid #e8e8e8;
            padding-bottom: 10px;
            margin-bottom: 20px;
          }
          .summary-stats {
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
          }
          .stat-item {
            text-align: center;
            padding: 15px;
            background: #f5f5f5;
            border-radius: 8px;
            min-width: 120px;
          }
          .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #1890ff;
          }
          .stat-label {
            color: #666;
            font-size: 14px;
          }
          .info-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
          }
          .info-table th,
          .info-table td {
            border: 1px solid #e8e8e8;
            padding: 12px;
            text-align: left;
          }
          .info-table th {
            background: #f5f5f5;
            font-weight: bold;
          }
          .disclaimer {
            background: #fff7e6;
            border: 1px solid #ffd591;
            padding: 15px;
            border-radius: 6px;
            margin-top: 30px;
          }
          .disclaimer h3 {
            color: #ad6800;
            margin-top: 0;
          }
          .disclaimer p {
            color: #ad6800;
            font-style: italic;
            margin-bottom: 0;
          }
          .footer {
            text-align: center;
            color: #666;
            font-size: 12px;
            margin-top: 40px;
            border-top: 1px solid #e8e8e8;
            padding-top: 20px;
          }
          @media print {
            body { margin: 0; padding: 15px; }
            .section { page-break-inside: avoid; }
          }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>股票分析报告</h1>
          <div class="stock-code">${analysis.stockCode}</div>
          <div class="date">报告日期: ${new Date(analysis.createdAt).toLocaleDateString()}</div>
        </div>

        <div class="section">
          <h2>执行摘要</h2>
          <div class="summary-stats">
            <div class="stat-item">
              <div class="stat-value">${resultData.overallScore || 'N/A'}</div>
              <div class="stat-label">综合评分</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">¥${resultData.targetPrice || 'N/A'}</div>
              <div class="stat-label">目标价格</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">${resultData.recommendation || 'N/A'}</div>
              <div class="stat-label">投资建议</div>
            </div>
          </div>
          <p>${resultData.summary || '本次分析针对股票代码 ' + analysis.stockCode + ' 进行了全面的基本面、技术面和市场情绪分析。'}</p>
        </div>

        <div class="section">
          <h2>基本信息</h2>
          <table class="info-table">
            <tr><th>股票代码</th><td>${analysis.stockCode}</td></tr>
            <tr><th>分析状态</th><td>已完成</td></tr>
            <tr><th>分析开始时间</th><td>${new Date(analysis.createdAt).toLocaleString()}</td></tr>
            <tr><th>分析完成时间</th><td>${analysis.completedAt ? new Date(analysis.completedAt).toLocaleString() : 'N/A'}</td></tr>
            <tr><th>分析师类型</th><td>${resultData.analysts?.join(', ') || '综合分析'}</td></tr>
            <tr><th>数据源</th><td>${resultData.dataSources?.join(', ') || '多源数据'}</td></tr>
          </table>
        </div>

        ${includeDetailedAnalysis ? this.generateDetailedAnalysisHTML(resultData) : ''}

        <div class="disclaimer">
          <h3>风险提示</h3>
          <p>本报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。本分析基于公开信息和历史数据，市场情况可能发生变化。投资者应根据自身情况做出独立判断，并承担相应风险。</p>
        </div>

        <div class="footer">
          <p>报告生成时间: ${new Date().toLocaleString()}</p>
          <p>TradingAgents 智能分析系统</p>
        </div>
      </body>
      </html>
    `;
  }

  // Generate detailed analysis HTML
  private static generateDetailedAnalysisHTML(resultData: any): string {
    const analysisTypes = [
      { key: 'fundamentalAnalysis', title: '基本面分析' },
      { key: 'technicalAnalysis', title: '技术分析' },
      { key: 'marketAnalysis', title: '市场分析' },
      { key: 'newsAnalysis', title: '新闻分析' },
    ];

    return analysisTypes
      .filter(({ key }) => resultData[key])
      .map(({ key, title }) => {
        const data = resultData[key];
        return `
          <div class="section">
            <h2>${title}</h2>
            ${data.summary ? `<p><strong>分析摘要:</strong> ${data.summary}</p>` : ''}
            ${data.keyPoints ? `
              <div>
                <h3>关键要点:</h3>
                <ul>
                  ${data.keyPoints.map((point: string) => `<li>${point}</li>`).join('')}
                </ul>
              </div>
            ` : ''}
            ${data.recommendations ? `
              <div>
                <h3>建议:</h3>
                <ul>
                  ${data.recommendations.map((rec: string) => `<li>${rec}</li>`).join('')}
                </ul>
              </div>
            ` : ''}
          </div>
        `;
      })
      .join('');
  }
}

export default ReportUtils;