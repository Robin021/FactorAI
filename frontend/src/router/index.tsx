
import { createBrowserRouter, Navigate } from 'react-router-dom';
import AuthGuard from '@/components/Common/AuthGuard';
import MainLayout from '@/components/Layout/MainLayout';
import AuthLayout from '@/components/Layout/AuthLayout';
import Dashboard from '@/pages/Dashboard';
import Analysis from '@/pages/Analysis';
import AnalysisReport from '@/pages/AnalysisReport';
import Config from '@/pages/Config';
import Login from '@/pages/Login';
import AuthCallback from '@/pages/AuthCallback';

export const router = createBrowserRouter([
  {
    path: '/login',
    element: (
      <AuthGuard requireAuth={false} redirectTo="/dashboard">
        <AuthLayout>
          <Login />
        </AuthLayout>
      </AuthGuard>
    ),
  },
  {
    path: '/auth/callback',
    element: <AuthCallback />,
  },
  {
    path: '/',
    element: (
      <AuthGuard requireAuth={true} redirectTo="/login">
        <MainLayout />
      </AuthGuard>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: 'dashboard',
        element: <Dashboard />,
      },
      {
        path: 'analysis',
        element: <Analysis />,
      },
      {
        path: 'analysis/report/:id',
        element: <AnalysisReport />,
      },
      {
        path: 'config',
        element: <Config />,
      },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/dashboard" replace />,
  },
]);

export default router;