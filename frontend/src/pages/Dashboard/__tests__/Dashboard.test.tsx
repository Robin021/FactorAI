import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import Dashboard from '../index';

// Mock router wrapper
const MockRouter = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    <ConfigProvider>
      {children}
    </ConfigProvider>
  </BrowserRouter>
);

describe('Dashboard Component', () => {
  it('renders dashboard title', () => {
    render(
      <MockRouter>
        <Dashboard />
      </MockRouter>
    );

    expect(screen.getByText('仪表板')).toBeInTheDocument();
  });

  it('renders all statistics cards', () => {
    render(
      <MockRouter>
        <Dashboard />
      </MockRouter>
    );

    // Check all statistic titles
    expect(screen.getByText('总分析次数')).toBeInTheDocument();
    expect(screen.getByText('成功分析')).toBeInTheDocument();
    expect(screen.getByText('进行中')).toBeInTheDocument();
    expect(screen.getByText('活跃用户')).toBeInTheDocument();

    // Check statistic values
    expect(screen.getByText('156')).toBeInTheDocument();
    expect(screen.getByText('142')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('28')).toBeInTheDocument();
  });

  it('renders recent analysis and system status cards', () => {
    render(
      <MockRouter>
        <Dashboard />
      </MockRouter>
    );

    expect(screen.getByText('最近分析')).toBeInTheDocument();
    expect(screen.getByText('系统状态')).toBeInTheDocument();
    expect(screen.getByText('这里将显示最近的分析记录...')).toBeInTheDocument();
    expect(screen.getByText('这里将显示系统运行状态...')).toBeInTheDocument();
  });

  it('has correct responsive layout structure', () => {
    render(
      <MockRouter>
        <Dashboard />
      </MockRouter>
    );

    // Check if the main container exists
    const dashboard = screen.getByText('仪表板').closest('.dashboard');
    expect(dashboard).toBeInTheDocument();

    // Check if cards are rendered
    const cards = document.querySelectorAll('.ant-card');
    expect(cards).toHaveLength(6); // 4 statistic cards + 2 content cards
  });

  it('displays correct icons for statistics', () => {
    render(
      <MockRouter>
        <Dashboard />
      </MockRouter>
    );

    // Check if antd icons are rendered (they should be in the DOM)
    const icons = document.querySelectorAll('.anticon');
    expect(icons.length).toBeGreaterThan(0);
  });
});