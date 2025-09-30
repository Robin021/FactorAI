// Common types for the application
export interface User {
  id: string;
  username: string;
  email?: string;
  role: 'admin' | 'user' | 'viewer';
  permissions: string[];
  createdAt: string;
  lastLogin?: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthResponse {
  user: User;
  token: string;
  refreshToken: string;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface AnalysisRequest {
  symbol: string;
  market_type?: string;
  analysis_type?: string;
}

export interface Analysis {
  id: string;
  userId: string;
  stockCode: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  resultData?: Record<string, any>;
  createdAt: string;
  completedAt?: string;
  marketType?: string;
  analysisType?: string;
  config?: Record<string, any>;
  errorMessage?: string;
  startedAt?: string;
}

export type AnalysisStatus = Analysis['status'];