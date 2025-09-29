
import { RouterProvider } from 'react-router-dom'
import { ConfigProvider, App as AntdApp } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { router } from './router'
import { ErrorBoundary, ThemeProvider } from './components/Common'
import { useEffect } from 'react'
import { initializeAuth } from './stores/authStore'
import './App.css'
import './styles/themes.css'
import './styles/theme-override.css'

function App() {
  // Initialize auth state only once on app mount
  useEffect(() => {
    initializeAuth();
  }, []);
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <ConfigProvider locale={zhCN}>
          <AntdApp>
            <RouterProvider router={router} />
          </AntdApp>
        </ConfigProvider>
      </ThemeProvider>
    </ErrorBoundary>
  )
}

export default App