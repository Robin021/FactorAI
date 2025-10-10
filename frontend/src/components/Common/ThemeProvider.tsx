import React, { createContext, useContext, useState, useEffect } from 'react';
import { ConfigProvider, theme } from 'antd';
import type { ThemeConfig } from 'antd';

type ThemeMode = 'light' | 'dark';

interface ThemeContextType {
  themeMode: ThemeMode;
  toggleTheme: () => void;
  setThemeMode: (mode: ThemeMode) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

interface ThemeProviderProps {
  children: React.ReactNode;
}

const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [themeMode, setThemeMode] = useState<ThemeMode>(() => {
    const saved = localStorage.getItem('theme-mode');
    return (saved as ThemeMode) || 'dark';
  });

  useEffect(() => {
    localStorage.setItem('theme-mode', themeMode);
    
    // Update document class for CSS variables
    document.documentElement.setAttribute('data-theme', themeMode);
    console.log('Theme changed to:', themeMode);
  }, [themeMode]);

  const toggleTheme = () => {
    setThemeMode(prev => prev === 'light' ? 'dark' : 'light');
  };

  const themeConfig: ThemeConfig = {
    algorithm: themeMode === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
    token: {
      colorPrimary: '#0f766e',
      borderRadius: 8,
      wireframe: false,
    },
    components: {
      Layout: {
        headerBg: themeMode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(255, 255, 255, 0.85)',
        siderBg: themeMode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(255, 255, 255, 0.85)',
        bodyBg: themeMode === 'dark' ? 'linear-gradient(135deg, #000000 0%, #1a1a1a 100%)' : 'linear-gradient(135deg, #f5f7fa 0%, #e8f0fe 100%)',
      },
      Menu: {
        darkItemBg: 'rgba(255, 255, 255, 0.05)',
        darkSubMenuItemBg: 'rgba(255, 255, 255, 0.03)',
        darkItemSelectedBg: 'rgba(255, 255, 255, 0.06)',
      },
      Card: {
        borderRadiusLG: 12,
      },
      Button: {
        borderRadius: 8,
      },
      Input: {
        borderRadius: 8,
      },
    },
  };

  const contextValue: ThemeContextType = {
    themeMode,
    toggleTheme,
    setThemeMode,
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      <ConfigProvider theme={themeConfig}>
        {children}
      </ConfigProvider>
    </ThemeContext.Provider>
  );
};

export default ThemeProvider;
