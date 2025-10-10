import React, { useState, useCallback } from 'react';
import { Card, Row, Col, Tabs, Button, Space, Select, DatePicker, Switch, Tooltip } from 'antd';
import { FullscreenOutlined, DownloadOutlined, SettingOutlined, SyncOutlined } from '@ant-design/icons';
import StockPriceChart from './StockPriceChart';
import TechnicalIndicatorsChart from './TechnicalIndicatorsChart';
import AnalystOpinionsChart from './AnalystOpinionsChart';
import type { StockPriceData, TechnicalData, AnalystOpinion, ChartSettings } from '../../types/charts';
import dayjs from 'dayjs';
const { RangePicker } = DatePicker;

interface DashboardChartSettings extends Omit<ChartSettings, 'timeRange'> {
  timeRange: [dayjs.Dayjs, dayjs.Dayjs] | null;
}

interface InteractiveChartDashboardProps {
  stockCode: string;
  stockName?: string;
  priceData: StockPriceData[];
  technicalData: TechnicalData[];
  analystOpinions: AnalystOpinion[];
  loading?: boolean;
  onRefresh?: () => void;
  onExport?: (chartType: string) => void;
  onSettingsChange?: (settings: Partial<DashboardChartSettings>) => void;
}

const InteractiveChartDashboard: React.FC<InteractiveChartDashboardProps> = ({
  stockCode,
  stockName,
  priceData,
  technicalData,
  analystOpinions,
  loading = false,
  onRefresh,
  onExport,
  onSettingsChange,
}) => {
  const [activeTab, setActiveTab] = useState('price');
  const [fullscreenChart, setFullscreenChart] = useState<string | null>(null);
  const [settings, setSettings] = useState<DashboardChartSettings>({
    showVolume: true,
    chartHeight: 500,
    timeRange: null,
    technicalIndicator: 'rsi',
    autoRefresh: false,
    refreshInterval: 30,
  });

  // Filter data based on time range
  const filteredPriceData = React.useMemo(() => {
    if (!settings.timeRange) return priceData;
    const [start, end] = settings.timeRange;
    return priceData.filter(item => {
      const itemDate = dayjs(item.date);
      return itemDate.isAfter(start) && itemDate.isBefore(end);
    });
  }, [priceData, settings.timeRange]);

  const filteredTechnicalData = React.useMemo(() => {
    if (!settings.timeRange) return technicalData;
    const [start, end] = settings.timeRange;
    return technicalData.filter(item => {
      const itemDate = dayjs(item.date);
      return itemDate.isAfter(start) && itemDate.isBefore(end);
    });
  }, [technicalData, settings.timeRange]);

  // Auto refresh functionality
  React.useEffect(() => {
    if (!settings.autoRefresh || !onRefresh) return;

    const interval = setInterval(() => {
      onRefresh();
    }, settings.refreshInterval * 1000);

    return () => clearInterval(interval);
  }, [settings.autoRefresh, settings.refreshInterval, onRefresh]);

  const handleSettingChange = useCallback((key: keyof DashboardChartSettings, value: any) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    onSettingsChange?.(newSettings);
  }, [settings, onSettingsChange]);

  const handleExport = useCallback((chartType: string) => {
    onExport?.(chartType);
  }, [onExport]);

  const handleFullscreen = useCallback((chartType: string) => {
    setFullscreenChart(chartType === fullscreenChart ? null : chartType);
  }, [fullscreenChart]);

  const renderToolbar = (chartType: string) => (
    <Space>
      <Tooltip title="刷新数据">
        <Button 
          icon={<SyncOutlined />} 
          size="small" 
          onClick={onRefresh}
          loading={loading}
        />
      </Tooltip>
      <Tooltip title="导出图表">
        <Button 
          icon={<DownloadOutlined />} 
          size="small" 
          onClick={() => handleExport(chartType)}
        />
      </Tooltip>
      <Tooltip title="全屏显示">
        <Button 
          icon={<FullscreenOutlined />} 
          size="small" 
          onClick={() => handleFullscreen(chartType)}
        />
      </Tooltip>
    </Space>
  );

  const renderSettingsPanel = () => (
    <Card size="small" title="图表设置" style={{ marginBottom: 16 }}>
      <Row gutter={[16, 16]}>
        <Col span={12}>
          <div style={{ marginBottom: 8 }}>
            <label>时间范围:</label>
            <RangePicker
              value={settings.timeRange}
              onChange={(dates) => handleSettingChange('timeRange', dates)}
              style={{ width: '100%', marginTop: 4 }}
              size="small"
            />
          </div>
        </Col>
        <Col span={12}>
          <div style={{ marginBottom: 8 }}>
            <label>图表高度:</label>
            <Select
              value={settings.chartHeight}
              onChange={(value) => handleSettingChange('chartHeight', value)}
              style={{ width: '100%', marginTop: 4 }}
              size="small"
              options={[
                { value: 300, label: '300px' },
                { value: 400, label: '400px' },
                { value: 500, label: '500px' },
                { value: 600, label: '600px' },
              ]}
            />
          </div>
        </Col>
        <Col span={12}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <label>显示成交量:</label>
            <Switch
              checked={settings.showVolume}
              onChange={(checked) => handleSettingChange('showVolume', checked)}
              size="small"
            />
          </div>
        </Col>
        <Col span={12}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <label>自动刷新:</label>
            <Switch
              checked={settings.autoRefresh}
              onChange={(checked) => handleSettingChange('autoRefresh', checked)}
              size="small"
            />
          </div>
        </Col>
        {settings.autoRefresh && (
          <Col span={12}>
            <div style={{ marginBottom: 8 }}>
              <label>刷新间隔(秒):</label>
              <Select
                value={settings.refreshInterval}
                onChange={(value) => handleSettingChange('refreshInterval', value)}
                style={{ width: '100%', marginTop: 4 }}
                size="small"
                options={[
                  { value: 10, label: '10秒' },
                  { value: 30, label: '30秒' },
                  { value: 60, label: '1分钟' },
                  { value: 300, label: '5分钟' },
                ]}
              />
            </div>
          </Col>
        )}
      </Row>
    </Card>
  );

  if (fullscreenChart) {
    const chartProps = {
      loading,
      height: window.innerHeight - 200,
    };

    return (
      <div style={{ 
        position: 'fixed', 
        top: 0, 
        left: 0, 
        right: 0, 
        bottom: 0, 
        backgroundColor: 'white', 
        zIndex: 1000,
        padding: 20,
      }}>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2>{stockCode} {stockName} - 全屏图表</h2>
          <Button onClick={() => setFullscreenChart(null)}>退出全屏</Button>
        </div>
        
        {fullscreenChart === 'price' && (
          <StockPriceChart
            data={filteredPriceData}
            title="股价走势图"
            showVolume={settings.showVolume}
            {...chartProps}
          />
        )}
        
        {fullscreenChart === 'technical' && (
          <TechnicalIndicatorsChart
            data={filteredTechnicalData}
            title="技术指标图"
            defaultIndicator={settings.technicalIndicator}
            onIndicatorChange={(indicator) => handleSettingChange('technicalIndicator', indicator)}
            {...chartProps}
          />
        )}
        
        {fullscreenChart === 'opinions' && (
          <AnalystOpinionsChart
            opinions={analystOpinions}
            title="分析师观点"
            {...chartProps}
          />
        )}
      </div>
    );
  }

  return (
    <div className="interactive-chart-dashboard">
      <Card 
        title={`${stockCode} ${stockName || ''} - 图表分析`}
        extra={
          <Space>
            <Button 
              icon={<SettingOutlined />} 
              size="small"
              onClick={() => {/* Toggle settings panel */}}
            >
              设置
            </Button>
            {renderToolbar(activeTab)}
          </Space>
        }
      >
        {renderSettingsPanel()}
        
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab}
          items={[
            {
              key: 'price',
              label: '股价走势',
              children: (
                <StockPriceChart
                  data={filteredPriceData}
                  title="股价走势图"
                  loading={loading}
                  height={settings.chartHeight}
                  showVolume={settings.showVolume}
                />
              ),
            },
            {
              key: 'technical',
              label: '技术指标',
              children: (
                <TechnicalIndicatorsChart
                  data={filteredTechnicalData}
                  title="技术指标图"
                  loading={loading}
                  height={settings.chartHeight}
                  defaultIndicator={settings.technicalIndicator}
                  onIndicatorChange={(indicator) => handleSettingChange('technicalIndicator', indicator)}
                />
              ),
            },
            {
              key: 'opinions',
              label: '分析师观点',
              children: (
                <AnalystOpinionsChart
                  opinions={analystOpinions}
                  title="分析师观点"
                  loading={loading}
                  height={settings.chartHeight}
                />
              ),
            },
            {
              key: 'comparison',
              label: '对比分析',
              children: (
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <StockPriceChart
                      data={filteredPriceData.slice(-30)} // Last 30 days
                      title="近30日走势"
                      loading={loading}
                      height={300}
                      showVolume={false}
                    />
                  </Col>
                  <Col span={12}>
                    <TechnicalIndicatorsChart
                      data={filteredTechnicalData.slice(-30)}
                      title="近30日技术指标"
                      loading={loading}
                      height={300}
                      defaultIndicator="rsi"
                    />
                  </Col>
                  <Col span={24}>
                    <AnalystOpinionsChart
                      opinions={analystOpinions}
                      title="分析师观点汇总"
                      loading={loading}
                      height={300}
                    />
                  </Col>
                </Row>
              ),
            },
          ]}
        />
      </Card>
    </div>
  );
};

export default InteractiveChartDashboard;
