import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import { act } from 'react-dom/test-utils';
import Login from '@/pages/Login';
import { authService } from '@/services/auth';
import { useAuthStore } from '@/stores/authStore';
import { vi } from 'vitest';
import { vi } from 'vitest';
import { vi } from 'vitest';
import { vi } from 'vitest';

// Mock the auth service
vi.mock('@/services/auth');
const mockAuthService = authService as any;

// Mock router and provider wrapper
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    <ConfigProvider>
      {children}
    </ConfigProvider>
  </BrowserRouter>
);

describe('Login Flow Integration Tests', () => {
  const mockUser = {
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
    act(() => {
      useAuthStore.setState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      });
    });

    // Reset mocks
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe('Successful Login Flow', () => {
    it('should complete full login flow successfully', async () => {
      const user = userEvent.setup();
      mockAuthService.login.mockResolvedValue(mockAuthResponse);

      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      // Verify initial state
      expect(screen.getByText('因子智投（Factor AI）')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('用户名')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('密码')).toBeInTheDocument();

      // Fill in credentials
      const usernameInput = screen.getByPlaceholderText('用户名');
      const passwordInput = screen.getByPlaceholderText('密码');
      const loginButton = screen.getByRole('button', { name: '登录' });

      await user.type(usernameInput, 'testuser');
      await user.type(passwordInput, 'password123');

      // Verify form validation passes
      expect(usernameInput).toHaveValue('testuser');
      expect(passwordInput).toHaveValue('password123');

      // Submit form
      await user.click(loginButton);

      // Verify loading state
      await waitFor(() => {
        expect(loginButton).toBeDisabled();
      });

      // Wait for login to complete
      await waitFor(() => {
        expect(mockAuthService.login).toHaveBeenCalledWith({
          username: 'testuser',
          password: 'password123',
        });
      });

      // Verify success state
      const store = useAuthStore.getState();
      expect(store.user).toEqual(mockUser);
      expect(store.isAuthenticated).toBe(true);
      expect(store.error).toBeNull();
    });

    it('should handle remember me functionality', async () => {
      const user = userEvent.setup();
      mockAuthService.login.mockResolvedValue(mockAuthResponse);

      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      // Fill in credentials and check remember me
      await user.type(screen.getByPlaceholderText('用户名'), 'testuser');
      await user.type(screen.getByPlaceholderText('密码'), 'password123');
      await user.click(screen.getByRole('checkbox', { name: '记住用户名' }));

      // Submit form
      await user.click(screen.getByRole('button', { name: '登录' }));

      await waitFor(() => {
        expect(mockAuthService.login).toHaveBeenCalled();
      });

      // Verify credentials are saved
      expect(localStorage.getItem('saved_credentials')).toBeTruthy();
      expect(localStorage.getItem('remember_me')).toBe('true');
    });
  });

  describe('Failed Login Flow', () => {
    it('should handle login failure with error message', async () => {
      const user = userEvent.setup();
      const errorMessage = '用户名或密码错误';
      mockAuthService.login.mockRejectedValue(new Error(errorMessage));

      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      // Fill in invalid credentials
      await user.type(screen.getByPlaceholderText('用户名'), 'wronguser');
      await user.type(screen.getByPlaceholderText('密码'), 'wrongpassword');
      await user.click(screen.getByRole('button', { name: '登录' }));

      // Wait for error to appear
      await waitFor(() => {
        expect(screen.getByText('登录失败')).toBeInTheDocument();
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });

      // Verify error state
      const store = useAuthStore.getState();
      expect(store.user).toBeNull();
      expect(store.isAuthenticated).toBe(false);
      expect(store.error).toBe(errorMessage);
    });

    it('should handle multiple failed attempts with lockout', async () => {
      const user = userEvent.setup();
      mockAuthService.login.mockRejectedValue(new Error('Invalid credentials'));

      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      const usernameInput = screen.getByPlaceholderText('用户名');
      const passwordInput = screen.getByPlaceholderText('密码');
      const loginButton = screen.getByRole('button', { name: '登录' });

      // Attempt login 5 times
      for (let i = 0; i < 5; i++) {
        await user.clear(usernameInput);
        await user.clear(passwordInput);
        await user.type(usernameInput, 'wronguser');
        await user.type(passwordInput, 'wrongpassword');
        await user.click(loginButton);

        await waitFor(() => {
          expect(mockAuthService.login).toHaveBeenCalledTimes(i + 1);
        });

        // Check warning messages for attempts 3-4
        if (i >= 2 && i < 4) {
          await waitFor(() => {
            expect(screen.getByText(`还有 ${4 - i} 次尝试机会`)).toBeInTheDocument();
          });
        }
      }

      // After 5 attempts, should be locked out
      await waitFor(() => {
        expect(screen.getByText('账户已锁定')).toBeInTheDocument();
        expect(loginButton).toBeDisabled();
      });
    });
  });

  describe('Form Validation', () => {
    it('should validate required fields', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      // Try to submit empty form
      await user.click(screen.getByRole('button', { name: '登录' }));

      await waitFor(() => {
        expect(screen.getByText('请输入用户名')).toBeInTheDocument();
        expect(screen.getByText('请输入密码')).toBeInTheDocument();
      });

      expect(mockAuthService.login).not.toHaveBeenCalled();
    });

    it('should validate username format and length', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      // Test short username
      await user.type(screen.getByPlaceholderText('用户名'), 'ab');
      await user.type(screen.getByPlaceholderText('密码'), 'password123');
      await user.click(screen.getByRole('button', { name: '登录' }));

      await waitFor(() => {
        expect(screen.getByText('用户名至少3个字符')).toBeInTheDocument();
      });

      // Test invalid characters
      await user.clear(screen.getByPlaceholderText('用户名'));
      await user.type(screen.getByPlaceholderText('用户名'), 'user@name');
      await user.click(screen.getByRole('button', { name: '登录' }));

      await waitFor(() => {
        expect(screen.getByText('用户名只能包含字母、数字和下划线')).toBeInTheDocument();
      });
    });

    it('should validate password length', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      await user.type(screen.getByPlaceholderText('用户名'), 'testuser');
      await user.type(screen.getByPlaceholderText('密码'), '123');
      await user.click(screen.getByRole('button', { name: '登录' }));

      await waitFor(() => {
        expect(screen.getByText('密码至少6个字符')).toBeInTheDocument();
      });
    });
  });

  describe('Auto-login with Saved Credentials', () => {
    it('should load saved credentials on mount', () => {
      // Set up saved credentials
      localStorage.setItem('saved_credentials', JSON.stringify({ username: 'saveduser' }));
      localStorage.setItem('remember_me', 'true');

      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      const usernameInput = screen.getByPlaceholderText('用户名') as HTMLInputElement;
      const rememberCheckbox = screen.getByRole('checkbox', { name: '记住用户名' }) as HTMLInputElement;

      expect(usernameInput.value).toBe('saveduser');
      expect(rememberCheckbox.checked).toBe(true);
    });

    it('should clear invalid saved credentials', () => {
      // Set up invalid saved credentials
      localStorage.setItem('saved_credentials', 'invalid-json');
      localStorage.setItem('remember_me', 'true');

      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      expect(consoleSpy).toHaveBeenCalledWith('Failed to load saved credentials:', expect.any(Error));
      expect(localStorage.getItem('saved_credentials')).toBeNull();
      expect(localStorage.getItem('remember_me')).toBeNull();

      consoleSpy.mockRestore();
    });
  });

  describe('Error Handling', () => {
    it('should clear error when user dismisses alert', async () => {
      const user = userEvent.setup();
      mockAuthService.login.mockRejectedValue(new Error('Login failed'));

      // Set initial error state
      act(() => {
        useAuthStore.setState({
          error: 'Login failed',
        });
      });

      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      // Error should be visible
      expect(screen.getByText('登录失败')).toBeInTheDocument();

      // Click close button on alert
      const closeButton = screen.getByRole('button', { name: 'close' });
      await user.click(closeButton);

      // Error should be cleared
      await waitFor(() => {
        expect(screen.queryByText('登录失败')).not.toBeInTheDocument();
      });
    });

    it('should handle different HTTP error status codes', async () => {
      const user = userEvent.setup();

      const testCases = [
        { status: 401, expectedMessage: '用户名或密码错误' },
        { status: 403, expectedMessage: '账户已被禁用，请联系管理员' },
        { status: 429, expectedMessage: '登录请求过于频繁，请稍后重试' },
      ];

      for (const testCase of testCases) {
        const error = new Error('HTTP Error');
        (error as any).response = { status: testCase.status };
        mockAuthService.login.mockRejectedValue(error);

        render(
          <TestWrapper>
            <Login />
          </TestWrapper>
        );

        await user.type(screen.getByPlaceholderText('用户名'), 'testuser');
        await user.type(screen.getByPlaceholderText('密码'), 'password123');
        await user.click(screen.getByRole('button', { name: '登 录' }));

        await waitFor(() => {
          expect(screen.getByText(testCase.expectedMessage)).toBeInTheDocument();
        });

        // Clean up for next iteration
        vi.clearAllMocks();
        document.body.innerHTML = '';
      }
    });
  });
});
