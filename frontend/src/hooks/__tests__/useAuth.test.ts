import { renderHook, act } from '@testing-library/react';
import { useAuth } from '../useAuth';
import { useAuthStore } from '@/stores/authStore';
import { User, LoginCredentials } from '@/types';

// Mock the auth store
vi.mock('@/stores/authStore');
const mockUseAuthStore = useAuthStore as any;

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

describe('useAuth Hook', () => {
  const mockUser: User = {
    id: '1',
    username: 'testuser',
    email: 'test@example.com',
    role: 'user',
    permissions: ['read'],
    created_at: new Date().toISOString(),
    last_login: new Date().toISOString(),
  };

  const mockCredentials: LoginCredentials = {
    username: 'testuser',
    password: 'password123',
  };

  const mockStoreState = {
    user: null,
    isAuthenticated: false,
    isLoading: false,
    error: null,
    login: vi.fn(),
    logout: vi.fn(),
    getCurrentUser: vi.fn(),
    refreshToken: vi.fn(),
    clearError: vi.fn(),
    clearSavedCredentials: vi.fn(),
    hasRememberedCredentials: vi.fn(),
  };

  beforeEach(() => {
    mockUseAuthStore.mockReturnValue(mockStoreState);
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  describe('Initial State', () => {
    it('should return initial auth state', () => {
      const { result } = renderHook(() => useAuth());

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('should call getCurrentUser if token exists but not authenticated', () => {
      localStorageMock.getItem.mockReturnValue('mock-token');
      mockUseAuthStore.mockReturnValue({
        ...mockStoreState,
        isAuthenticated: false,
      });

      renderHook(() => useAuth());

      expect(mockStoreState.getCurrentUser).toHaveBeenCalled();
    });

    it('should not call getCurrentUser if already authenticated', () => {
      localStorageMock.getItem.mockReturnValue('mock-token');
      mockUseAuthStore.mockReturnValue({
        ...mockStoreState,
        isAuthenticated: true,
      });

      renderHook(() => useAuth());

      expect(mockStoreState.getCurrentUser).not.toHaveBeenCalled();
    });

    it('should not call getCurrentUser if no token exists', () => {
      localStorageMock.getItem.mockReturnValue(null);

      renderHook(() => useAuth());

      expect(mockStoreState.getCurrentUser).not.toHaveBeenCalled();
    });
  });

  describe('Login', () => {
    it('should call store login method', async () => {
      mockStoreState.login.mockResolvedValue(undefined);
      
      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.current.login(mockCredentials);
      });

      expect(mockStoreState.login).toHaveBeenCalledWith(mockCredentials);
    });

    it('should handle login success', async () => {
      mockStoreState.login.mockResolvedValue(undefined);
      
      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.current.login(mockCredentials);
      });

      expect(mockStoreState.login).toHaveBeenCalledWith(mockCredentials);
    });

    it('should handle login failure', async () => {
      const errorMessage = 'Invalid credentials';
      mockStoreState.login.mockRejectedValue(new Error(errorMessage));
      
      const { result } = renderHook(() => useAuth());

      await act(async () => {
        try {
          await result.current.login(mockCredentials);
        } catch (error: any) {
          expect(error.message).toBe(errorMessage);
        }
      });

      expect(mockStoreState.login).toHaveBeenCalledWith(mockCredentials);
    });
  });

  describe('Logout', () => {
    it('should call store logout method', async () => {
      mockStoreState.logout.mockResolvedValue(undefined);
      
      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.current.logout();
      });

      expect(mockStoreState.logout).toHaveBeenCalled();
    });

    it('should handle logout success', async () => {
      mockStoreState.logout.mockResolvedValue(undefined);
      
      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.current.logout();
      });

      expect(mockStoreState.logout).toHaveBeenCalled();
    });
  });

  describe('Other Methods', () => {
    it('should expose refreshToken method', () => {
      const { result } = renderHook(() => useAuth());

      expect(result.current.refreshToken).toBe(mockStoreState.refreshToken);
    });

    it('should expose clearError method', () => {
      const { result } = renderHook(() => useAuth());

      act(() => {
        result.current.clearError();
      });

      expect(mockStoreState.clearError).toHaveBeenCalled();
    });

    it('should expose clearSavedCredentials method', () => {
      const { result } = renderHook(() => useAuth());

      act(() => {
        result.current.clearSavedCredentials();
      });

      expect(mockStoreState.clearSavedCredentials).toHaveBeenCalled();
    });

    it('should expose hasRememberedCredentials method', () => {
      mockStoreState.hasRememberedCredentials.mockReturnValue(true);
      
      const { result } = renderHook(() => useAuth());

      const hasRemembered = result.current.hasRememberedCredentials();
      expect(hasRemembered).toBe(true);
      expect(mockStoreState.hasRememberedCredentials).toHaveBeenCalled();
    });
  });

  describe('State Updates', () => {
    it('should reflect store state changes', () => {
      const { result, rerender } = renderHook(() => useAuth());

      // Initial state
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);

      // Update store state
      mockUseAuthStore.mockReturnValue({
        ...mockStoreState,
        user: mockUser,
        isAuthenticated: true,
      });

      rerender();

      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
    });

    it('should reflect loading state changes', () => {
      const { result, rerender } = renderHook(() => useAuth());

      expect(result.current.isLoading).toBe(false);

      mockUseAuthStore.mockReturnValue({
        ...mockStoreState,
        isLoading: true,
      });

      rerender();

      expect(result.current.isLoading).toBe(true);
    });

    it('should reflect error state changes', () => {
      const { result, rerender } = renderHook(() => useAuth());

      expect(result.current.error).toBeNull();

      const errorMessage = 'Authentication failed';
      mockUseAuthStore.mockReturnValue({
        ...mockStoreState,
        error: errorMessage,
      });

      rerender();

      expect(result.current.error).toBe(errorMessage);
    });
  });
});