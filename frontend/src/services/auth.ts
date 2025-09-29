import { apiClient } from './api';
import { LoginCredentials, AuthResponse, User } from '@/types';

export class AuthService {
  // Login user
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    try {
      const response = await apiClient.post('/auth/login', credentials);
      
      // 适配后端返回格式
      if (response.access_token && response.user) {
        // Store tokens
        apiClient.setAuthToken(response.access_token);
        localStorage.setItem('refresh_token', response.access_token); // 暂时使用同一个token
        
        return {
          user: {
            id: response.user.username,
            username: response.user.username,
            email: response.user.email,
            role: response.user.role,
            permissions: response.user.permissions,
            createdAt: new Date().toISOString(),
          },
          token: response.access_token,
          refreshToken: response.access_token,
        };
      }
      
      throw new Error('Invalid response format');
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw error;
    }
  }

  // Logout user
  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout');
    } catch (error) {
      // Continue with logout even if API call fails
      console.warn('Logout API call failed:', error);
    } finally {
      // Always clear local tokens
      apiClient.clearAuthToken();
    }
  }

  // Get current user info
  async getCurrentUser(): Promise<User> {
    try {
      const response = await apiClient.get('/auth/me');
      
      // 适配后端返回格式
      return {
        id: response.username,
        username: response.username,
        email: response.email,
        role: response.role,
        permissions: response.permissions,
        createdAt: new Date().toISOString(),
      };
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw error;
    }
  }

  // Refresh auth token
  async refreshToken(): Promise<AuthResponse> {
    const refreshToken = localStorage.getItem('refresh_token');
    
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await apiClient.post<AuthResponse>('/auth/refresh', {
      refreshToken,
    });
    
    if (response.success && response.data) {
      // Update stored tokens
      apiClient.setAuthToken(response.data.token);
      localStorage.setItem('refresh_token', response.data.refreshToken);
      
      return response.data;
    }
    
    throw new Error(response.error || 'Token refresh failed');
  }

  // Check if user is authenticated
  isAuthenticated(): boolean {
    return !!apiClient.getAuthToken();
  }

  // Auto-refresh token if needed
  async ensureValidToken(): Promise<boolean> {
    if (!this.isAuthenticated()) {
      return false;
    }

    try {
      // Try to get current user to validate token
      await this.getCurrentUser();
      return true;
    } catch (error: any) {
      if (error.response?.status === 401) {
        // Token expired, try to refresh
        try {
          await this.refreshToken();
          return true;
        } catch (refreshError) {
          // Refresh failed, user needs to login again
          apiClient.clearAuthToken();
          return false;
        }
      }
      
      // Other errors, assume token is still valid
      return true;
    }
  }

  // Auto-login with saved credentials (if remember me was enabled)
  async attemptAutoLogin(): Promise<boolean> {
    const rememberMe = localStorage.getItem('remember_me') === 'true';
    const authToken = localStorage.getItem('auth_token');
    
    if (!rememberMe || !authToken) {
      return false;
    }

    try {
      // Validate existing token
      const isValid = await this.ensureValidToken();
      return isValid;
    } catch (error) {
      console.warn('Auto-login failed:', error);
      // Clear invalid credentials
      localStorage.removeItem('saved_credentials');
      localStorage.removeItem('remember_me');
      apiClient.clearAuthToken();
      return false;
    }
  }

  // Clear saved credentials
  clearSavedCredentials(): void {
    localStorage.removeItem('saved_credentials');
    localStorage.removeItem('remember_me');
  }
}

export const authService = new AuthService();
export default authService;