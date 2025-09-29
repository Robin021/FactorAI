
import { RouterProvider } from 'react-router-dom'
import { ConfigProvider, App as AntdApp } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { router } from './router'
import { ErrorBoundary, ThemeProvider } from './components/Common'
import { initializeAuth } from './stores/authStore'
import './App.css'

// Initialize auth state
initializeAuth();

function App() {
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