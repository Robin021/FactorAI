import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import Login from './index';
import { useAuth } from '@/hooks/useAuth';

// Mock the useAuth hook
jest.mock('@/hooks/useAuth');
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

// Mock router
const MockRouter = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    <ConfigProvider>
      {children}
    </ConfigProvider>
  </BrowserRouter>
);

describe('Login Component', () => {
  const mockLogin = jest.fn();
  const mockClearError = jest.fn();

  beforeEach(() => {
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      login: mockLogin,
      logout: jest.fn(),
      refreshToken: jest.fn(),
      clearError: mockClearError,
      clearSavedCredentials: jest.fn(),
      hasRememberedCredentials: jest.fn().mockReturnValue(false),
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  it('renders login form correctly', () => {
    render(
      <MockRouter>
        <Login />
      </MockRouter>
    );

    expect(screen.getByText('因子智投（Factor AI）')).toBeInTheDocument();
    expect(screen.getByText('因子驱动的智能投研平台')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('用户名')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('密码')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '登录' })).toBeInTheDocument();
  });

  it('validates required fields', async () => {
    render(
      <MockRouter>
        <Login />
      </MockRouter>
    );

    const loginButton = screen.getByRole('button', { name: '登录' });
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(screen.getByText('请输入用户名')).toBeInTheDocument();
      expect(screen.getByText('请输入密码')).toBeInTheDocument();
    });
  });

  it('validates username format', async () => {
    render(
      <MockRouter>
        <Login />
      </MockRouter>
    );

    const usernameInput = screen.getByPlaceholderText('用户名');
    const passwordInput = screen.getByPlaceholderText('密码');
    const loginButton = screen.getByRole('button', { name: '登录' });

    fireEvent.change(usernameInput, { target: { value: 'ab' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(screen.getByText('用户名至少3个字符')).toBeInTheDocument();
    });
  });

  it('validates password length', async () => {
    render(
      <MockRouter>
        <Login />
      </MockRouter>
    );

    const usernameInput = screen.getByPlaceholderText('用户名');
    const passwordInput = screen.getByPlaceholderText('密码');
    const loginButton = screen.getByRole('button', { name: '登录' });

    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(passwordInput, { target: { value: '123' } });
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(screen.getByText('密码至少6个字符')).toBeInTheDocument();
    });
  });

  it('submits form with valid credentials', async () => {
    render(
      <MockRouter>
        <Login />
      </MockRouter>
    );

    const usernameInput = screen.getByPlaceholderText('用户名');
    const passwordInput = screen.getByPlaceholderText('密码');
    const loginButton = screen.getByRole('button', { name: '登录' });

    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123',
      });
    });
  });

  it('handles remember me functionality', async () => {
    render(
      <MockRouter>
        <Login />
      </MockRouter>
    );

    const usernameInput = screen.getByPlaceholderText('用户名');
    const passwordInput = screen.getByPlaceholderText('密码');
    const rememberCheckbox = screen.getByRole('checkbox', { name: '记住用户名' });
    const loginButton = screen.getByRole('button', { name: '登录' });

    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.click(rememberCheckbox);
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalled();
    });

    // Check if credentials are saved to localStorage
    expect(localStorage.getItem('saved_credentials')).toBeTruthy();
    expect(localStorage.getItem('remember_me')).toBe('true');
  });

  it('displays error message when login fails', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: '用户名或密码错误',
      login: mockLogin,
      logout: jest.fn(),
      refreshToken: jest.fn(),
      clearError: mockClearError,
      clearSavedCredentials: jest.fn(),
      hasRememberedCredentials: jest.fn().mockReturnValue(false),
    });

    render(
      <MockRouter>
        <Login />
      </MockRouter>
    );

    expect(screen.getByText('登录失败')).toBeInTheDocument();
    expect(screen.getByText('用户名或密码错误')).toBeInTheDocument();
  });

  it('shows loading state during login', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: true,
      error: null,
      login: mockLogin,
      logout: jest.fn(),
      refreshToken: jest.fn(),
      clearError: mockClearError,
      clearSavedCredentials: jest.fn(),
      hasRememberedCredentials: jest.fn().mockReturnValue(false),
    });

    render(
      <MockRouter>
        <Login />
      </MockRouter>
    );

    const loginButton = screen.getByRole('button', { name: '登录' });
    expect(loginButton).toBeDisabled();
  });

  it('loads saved credentials on mount', () => {
    // Set up saved credentials
    localStorage.setItem('saved_credentials', JSON.stringify({ username: 'saveduser' }));
    localStorage.setItem('remember_me', 'true');

    render(
      <MockRouter>
        <Login />
      </MockRouter>
    );

    const usernameInput = screen.getByPlaceholderText('用户名') as HTMLInputElement;
    const rememberCheckbox = screen.getByRole('checkbox', { name: '记住用户名' }) as HTMLInputElement;

    expect(usernameInput.value).toBe('saveduser');
    expect(rememberCheckbox.checked).toBe(true);
  });
});
