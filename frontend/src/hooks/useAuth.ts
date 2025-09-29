import { useEffect } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { LoginCredentials } from '@/types';

export const useAuth = () => {
  const {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    getCurrentUser,
    refreshToken,
    clearError,
    clearSavedCredentials,
    hasRememberedCredentials,
  } = useAuthStore();

  // Initialize auth state on mount
  useEffect(() => {
    if (!isAuthenticated && localStorage.getItem('auth_token')) {
      getCurrentUser();
    }
  }, [isAuthenticated, getCurrentUser]);

  const handleLogin = async (credentials: LoginCredentials) => {
    try {
      await login(credentials);
    } catch (error) {
      // Error is already handled in the store
      throw error;
    }
  };

  const handleLogout = async () => {
    await logout();
  };

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    login: handleLogin,
    logout: handleLogout,
    refreshToken,
    clearError,
    clearSavedCredentials,
    hasRememberedCredentials,
  };
};