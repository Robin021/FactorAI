import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { Card, Spin, Row, Col, Statistic, Tag } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, MinusOutlined } from '@ant-design/icons';
import type { AnalystOpinion } from '../../types/charts';

interface AnalystOpinionsChartProps {
  opinions: AnalystOpinion[];
  title?: string;
  loading?: boolean;
  height?: number;
}

const AnalystOpinionsChart: React.FC<AnalystOpinionsChartProps> = ({
  opinions,
  title = '分析师观点',
  loading = false,
  height = 400,
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!chartRef.current || loading || !opinions.length) return;

    // Initialize chart
    if (chartInstance.current) {
      chartInstance.current.dispose();
    }
    chartInstance.current = echarts.init(chartRef.current);

    // Prepare data for visualization
    const opinionCounts = opinions.reduce((acc, opinion) => {
      acc[opinion.opinion] = (acc[opinion.opinion] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const confidenceByOpinion = opinions.reduce((acc, opinion) => {
      if (!acc[opinion.opinion]) {
        acc[opinion.opinion] = [];
      }
      acc[opinion.opinion].push(opinion.confidence);
      return acc;
    }, {} as Record<string, number[]>);

    // Calculate average confidence for each opinion
    const avgConfidence = Object.entries(confidenceByOpinion).map(([opinion, confidences]) => ({
      opinion,
      avgConfidence: confidences.reduce((sum, conf) => sum + conf, 0) / confidences.length,
      count: confidences.length,
    }));

    const option: echarts.EChartsOption = {
      title: {
        text: '分析师观点分布',
        left: 'center',
        textStyle: { fontSize: 14 },
      },
      tooltip: {
        trigger: 'item',
        formatter: function (params: any) {
          const data = params.data;
          return `
            <div>
              <div><strong>${getOpinionLabel(data.name)}</strong></div>
              <div>数量: ${data.value}</div>
              <div>占比: ${params.percent}%</div>
            </div>
          `;
        },
      },
      legend: {
        orient: 'horizontal',
        bottom: '5%',
        data: ['买入', '卖出', '持有'],
      },
      series: [
        {
          name: '观点分布',
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['50%', '45%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2,
          },
          label: {
            show: false,
            position: 'center',
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 20,
              fontWeight: 'bold',
            },
          },
          labelLine: {
            show: false,
          },
          data: [
            {
              value: opinionCounts.buy || 0,
              name: 'buy',
              itemStyle: { color: '#52c41a' },
            },
            {
              value: opinionCounts.sell || 0,
              name: 'sell',
              itemStyle: { color: '#ff4d4f' },
            },
            {
              value: opinionCounts.hold || 0,
              name: 'hold',
              itemStyle: { color: '#faad14' },
            },
          ],
        },
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
  }, [opinions, loading, height]);

  useEffect(() => {
    return () => {
      if (chartInstance.current) {
        chartInstance.current.dispose();
      }
    };
  }, []);

  const getOpinionLabel = (opinion: string) => {
    switch (opinion) {
      case 'buy': return '买入';
      case 'sell': return '卖出';
      case 'hold': return '持有';
      default: return opinion;
    }
  };

  const getOpinionIcon = (opinion: string) => {
    switch (opinion) {
      case 'buy': return <ArrowUpOutlined style={{ color: '#52c41a' }} />;
      case 'sell': return <ArrowDownOutlined style={{ color: '#ff4d4f' }} />;
      case 'hold': return <MinusOutlined style={{ color: '#faad14' }} />;
      default: return null;
    }
  };

  const getOpinionColor = (opinion: string) => {
    switch (opinion) {
      case 'buy': return 'success';
      case 'sell': return 'error';
      case 'hold': return 'warning';
      default: return 'default';
    }
  };

  // Calculate statistics
  const totalOpinions = opinions.length;
  const buyCount = opinions.filter(op => op.opinion === 'buy').length;
  const sellCount = opinions.filter(op => op.opinion === 'sell').length;
  const holdCount = opinions.filter(op => op.opinion === 'hold').length;
  
  const avgConfidence = opinions.reduce((sum, op) => sum + op.confidence, 0) / totalOpinions;
  
  const targetPrices = opinions.filter(op => op.targetPrice).map(op => op.targetPrice!);
  const avgTargetPrice = targetPrices.length > 0 
    ? targetPrices.reduce((sum, price) => sum + price, 0) / targetPrices.length 
    : null;

  return (
    <Card className="analyst-opinions-chart" title={title}>
      <Spin spinning={loading}>
        <Row gutter={[16, 16]}>
          {/* Statistics */}
          <Col span={24}>
            <Row gutter={16}>
              <Col span={6}>
                <Statistic
                  title="总观点数"
                  value={totalOpinions}
                  suffix="个"
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="平均信心度"
                  value={avgConfidence}
                  precision={1}
                  suffix="%"
                  valueStyle={{ color: avgConfidence > 70 ? '#52c41a' : avgConfidence > 50 ? '#faad14' : '#ff4d4f' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="平均目标价"
                  value={avgTargetPrice}
                  precision={2}
                  prefix="¥"
                  valueStyle={{ color: 'var(--accent-color)' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="看涨比例"
                  value={(buyCount / totalOpinions) * 100}
                  precision={1}
                  suffix="%"
                  valueStyle={{ color: '#52c41a' }}
                />
              </Col>
            </Row>
          </Col>

          {/* Chart */}
          <Col span={12}>
            <div
              ref={chartRef}
              style={{ width: '100%', height: `${height}px` }}
            />
          </Col>

          {/* Opinion Details */}
          <Col span={12}>
            <div style={{ maxHeight: `${height}px`, overflowY: 'auto' }}>
              <h4>详细观点</h4>
              {opinions.slice(0, 10).map((opinion, index) => (
                <div key={index} style={{ marginBottom: 12, padding: 12, border: '1px solid #f0f0f0', borderRadius: 6 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <strong>{opinion.analyst}</strong>
                    <Tag color={getOpinionColor(opinion.opinion)} icon={getOpinionIcon(opinion.opinion)}>
                      {getOpinionLabel(opinion.opinion)}
                    </Tag>
                  </div>
                  <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>
                    信心度: {opinion.confidence}% 
                    {opinion.targetPrice && ` | 目标价: ¥${opinion.targetPrice.toFixed(2)}`}
                  </div>
                  <div style={{ fontSize: 12, color: '#999' }}>
                    {opinion.reasoning.length > 100 
                      ? `${opinion.reasoning.substring(0, 100)}...` 
                      : opinion.reasoning
                    }
                  </div>
                  <div style={{ fontSize: 11, color: '#ccc', marginTop: 4 }}>
                    {new Date(opinion.timestamp).toLocaleString()}
                  </div>
                </div>
              ))}
              {opinions.length > 10 && (
                <div style={{ textAlign: 'center', color: '#999', fontSize: 12 }}>
                  还有 {opinions.length - 10} 个观点...
                </div>
              )}
            </div>
          </Col>
        </Row>
      </Spin>
    </Card>
  );
};

export default AnalystOpinionsChart;
