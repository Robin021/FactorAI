import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, LoginCredentials } from '@/types';
import { authService } from '@/services/auth';

interface AuthState {
  // State
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  getCurrentUser: () => Promise<void>;
  refreshToken: () => Promise<void>;
  clearError: () => void;
  setLoading: (loading: boolean) => void;
  clearSavedCredentials: () => void;
  hasRememberedCredentials: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      // Initial state
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Actions
      login: async (credentials: LoginCredentials) => {
        set({ isLoading: true, error: null });
        
        try {
          const authResponse = await authService.login(credentials);
          set({
            user: authResponse.user,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: error.message || 'Login failed',
          });
          throw error;
        }
      },

      logout: async () => {
        set({ isLoading: true });
        
        try {
          await authService.logout();
        } catch (error) {
          console.warn('Logout error:', error);
        } finally {
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        }
      },

      getCurrentUser: async () => {
        if (!authService.isAuthenticated()) {
          set({ isAuthenticated: false, user: null });
          return;
        }

        set({ isLoading: true, error: null });
        
        try {
          const user = await authService.getCurrentUser();
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: error.message || 'Failed to get user info',
          });
        }
      },

      refreshToken: async () => {
        try {
          const authResponse = await authService.refreshToken();
          set({
            user: authResponse.user,
            isAuthenticated: true,
            error: null,
          });
        } catch (error: any) {
          set({
            user: null,
            isAuthenticated: false,
            error: error.message || 'Token refresh failed',
          });
          throw error;
        }
      },

      clearError: () => {
        set({ error: null });
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },

      // Clear saved credentials
      clearSavedCredentials: () => {
        authService.clearSavedCredentials();
      },

      // Check if auto-login is available
      hasRememberedCredentials: () => {
        return localStorage.getItem('remember_me') === 'true' && 
               localStorage.getItem('saved_credentials') !== null;
      },
    }),
    {
      name: 'auth-store',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Initialize auth state on app start
export const initializeAuth = async () => {
  const { getCurrentUser, setLoading } = useAuthStore.getState();
  
  setLoading(true);
  
  try {
    // Try auto-login first
    const autoLoginSuccess = await authService.attemptAutoLogin();
    
    if (autoLoginSuccess) {
      await getCurrentUser();
    } else if (authService.isAuthenticated()) {
      // Fallback to regular token validation
      await getCurrentUser();
    }
  } catch (error) {
    console.warn('Failed to initialize auth:', error);
    // Clear any invalid auth state
    authService.clearSavedCredentials();
  } finally {
    setLoading(false);
  }
};