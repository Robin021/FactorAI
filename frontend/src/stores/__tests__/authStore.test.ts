import { renderHook, act } from '@testing-library/react';
import { useAuthStore, initializeAuth } from '../authStore';
import { authService } from '@/services/auth';
import { User } from '@/types';

// Mock the auth service
vi.mock('@/services/auth');
const mockAuthService = authService as any;

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('AuthStore', () => {
  const mockUser: User = {
    id: '1',
    username: 'testuser',
    email: 'test@example.com',
    role: 'user',
    permissions: ['read'],
    created_at: new Date().toISOString(),
    last_login: new Date().toISOString(),
  };

  const mockAuthResponse = {
    user: mockUser,
    token: 'mock-token',
  };

  beforeEach(() => {
    // Reset store state
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });

    // Reset mocks
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const { result } = renderHook(() => useAuthStore());

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });

  describe('Login', () => {
    it('should login successfully', async () => {
      mockAuthService.login.mockResolvedValue(mockAuthResponse);
      
      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.login({
          username: 'testuser',
          password: 'password123',
        });
      });

      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(mockAuthService.login).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123',
      });
    });

    it('should handle login failure', async () => {
      const errorMessage = 'Invalid credentials';
      mockAuthService.login.mockRejectedValue(new Error(errorMessage));
      
      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        try {
          await result.current.login({
            username: 'testuser',
            password: 'wrongpassword',
          });
        } catch (error) {
          // Expected to throw
        }
      });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBe(errorMessage);
    });

    it('should set loading state during login', async () => {
      let resolveLogin: (value: any) => void;
      const loginPromise = new Promise((resolve) => {
        resolveLogin = resolve;
      });
      mockAuthService.login.mockReturnValue(loginPromise);
      
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.login({
          username: 'testuser',
          password: 'password123',
        });
      });

      expect(result.current.isLoading).toBe(true);

      await act(async () => {
        resolveLogin!(mockAuthResponse);
        await loginPromise;
      });

      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('Logout', () => {
    it('should logout successfully', async () => {
      mockAuthService.logout.mockResolvedValue(undefined);
      
      const { result } = renderHook(() => useAuthStore());

      // Set initial authenticated state
      act(() => {
        useAuthStore.setState({
          user: mockUser,
          isAuthenticated: true,
        });
      });

      await act(async () => {
        await result.current.logout();
      });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.error).toBeNull();
      expect(mockAuthService.logout).toHaveBeenCalled();
    });

    it('should handle logout error gracefully', async () => {
      mockAuthService.logout.mockRejectedValue(new Error('Logout failed'));
      
      const { result } = renderHook(() => useAuthStore());

      // Set initial authenticated state
      act(() => {
        useAuthStore.setState({
          user: mockUser,
          isAuthenticated: true,
        });
      });

      await act(async () => {
        await result.current.logout();
      });

      // Should still clear state even if logout fails
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('Get Current User', () => {
    it('should get current user when authenticated', async () => {
      mockAuthService.isAuthenticated.mockReturnValue(true);
      mockAuthService.getCurrentUser.mockResolvedValue(mockUser);
      
      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.getCurrentUser();
      });

      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.error).toBeNull();
    });

    it('should clear state when not authenticated', async () => {
      mockAuthService.isAuthenticated.mockReturnValue(false);
      
      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.getCurrentUser();
      });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('should handle getCurrentUser error', async () => {
      mockAuthService.isAuthenticated.mockReturnValue(true);
      mockAuthService.getCurrentUser.mockRejectedValue(new Error('Unauthorized'));
      
      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.getCurrentUser();
      });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.error).toBe('Unauthorized');
    });
  });

  describe('Refresh Token', () => {
    it('should refresh token successfully', async () => {
      mockAuthService.refreshToken.mockResolvedValue(mockAuthResponse);
      
      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.refreshToken();
      });

      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.error).toBeNull();
    });

    it('should handle refresh token failure', async () => {
      mockAuthService.refreshToken.mockRejectedValue(new Error('Token expired'));
      
      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        try {
          await result.current.refreshToken();
        } catch (error) {
          // Expected to throw
        }
      });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.error).toBe('Token expired');
    });
  });

  describe('Utility Actions', () => {
    it('should clear error', () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        useAuthStore.setState({ error: 'Some error' });
      });

      expect(result.current.error).toBe('Some error');

      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBeNull();
    });

    it('should set loading state', () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.setLoading(true);
      });

      expect(result.current.isLoading).toBe(true);

      act(() => {
        result.current.setLoading(false);
      });

      expect(result.current.isLoading).toBe(false);
    });

    it('should clear saved credentials', () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.clearSavedCredentials();
      });

      expect(mockAuthService.clearSavedCredentials).toHaveBeenCalled();
    });

    it('should check for remembered credentials', () => {
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === 'remember_me') return 'true';
        if (key === 'saved_credentials') return '{"username":"test"}';
        return null;
      });

      const { result } = renderHook(() => useAuthStore());

      const hasRemembered = result.current.hasRememberedCredentials();
      expect(hasRemembered).toBe(true);
    });
  });

  describe('Initialize Auth', () => {
    it('should initialize auth with auto-login', async () => {
      mockAuthService.attemptAutoLogin.mockResolvedValue(true);
      mockAuthService.getCurrentUser.mockResolvedValue(mockUser);
      
      await act(async () => {
        await initializeAuth();
      });

      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
      expect(state.isAuthenticated).toBe(true);
      expect(mockAuthService.attemptAutoLogin).toHaveBeenCalled();
    });

    it('should fallback to token validation when auto-login fails', async () => {
      mockAuthService.attemptAutoLogin.mockResolvedValue(false);
      mockAuthService.isAuthenticated.mockReturnValue(true);
      mockAuthService.getCurrentUser.mockResolvedValue(mockUser);
      
      await act(async () => {
        await initializeAuth();
      });

      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
      expect(mockAuthService.getCurrentUser).toHaveBeenCalled();
    });

    it('should handle initialization error', async () => {
      mockAuthService.attemptAutoLogin.mockRejectedValue(new Error('Init failed'));
      
      await act(async () => {
        await initializeAuth();
      });

      const state = useAuthStore.getState();
      expect(state.isLoading).toBe(false);
      expect(mockAuthService.clearSavedCredentials).toHaveBeenCalled();
    });
  });
});