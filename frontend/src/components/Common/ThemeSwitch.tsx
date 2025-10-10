import React from 'react';
import { Select } from 'antd';
import { BgColorsOutlined } from '@ant-design/icons';

const { Option } = Select;

interface ThemeSwitchProps {
  className?: string;
}

const themes = [
  { value: 'moonlight', label: '月白清雅', color: '#0f766e' },
  { value: 'celadon', label: '青瓷雅韵', color: '#0f766e' },
  { value: 'warmjade', label: '暖玉温润', color: '#8fbc8f' },
  { value: 'sakura', label: '樱花粉韵', color: '#ec4899' },
  { value: 'begonia', label: '海棠红韵', color: '#fb923c' },
  { value: 'emerald', label: '翡翠青山', color: '#10b981' },
  { value: 'forbidden', label: '紫禁城', color: '#f59e0b' },
  { value: 'starnight', label: '星空夜幕', color: '#3b82f6' },
  { value: 'obsidian', label: '极夜黑曜', color: '#0f766e' },
  { value: 'deepblue', label: '深海蓝黑', color: '#60a5fa' },
  { value: 'inkdark', label: '墨韵深沉', color: '#d4a574' },
];

const ThemeSwitch: React.FC<ThemeSwitchProps> = ({ className }) => {
  const [currentTheme, setCurrentTheme] = React.useState('moonlight');

  React.useEffect(() => {
    // 从localStorage读取保存的主题
    const savedTheme = localStorage.getItem('app-theme') || 'moonlight';
    setCurrentTheme(savedTheme);
    document.documentElement.setAttribute('data-theme', savedTheme);
    console.log('Applied theme:', savedTheme); // 调试信息
  }, []);

  const handleThemeChange = (theme: string) => {
    setCurrentTheme(theme);
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('app-theme', theme);
    console.log('Changed to theme:', theme); // 调试信息
    
    // 强制重新渲染样式
    document.body.style.display = 'none';
    document.body.offsetHeight; // 触发重排
    document.body.style.display = '';
  };

  return (
    <Select
      value={currentTheme}
      onChange={handleThemeChange}
      className={className}
      style={{ width: 140 }}
      size="small"
      suffixIcon={<BgColorsOutlined />}
      placeholder="选择主题"
    >
      {themes.map(theme => (
        <Option key={theme.value} value={theme.value}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div
              style={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                backgroundColor: theme.color,
              }}
            />
            {theme.label}
          </div>
        </Option>
      ))}
    </Select>
  );
};

export default ThemeSwitch;
