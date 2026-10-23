import { apiClient } from './client';
import type { LoginCredentials, TokenResponse, User } from '../types/auth';

export const authApi = {
  /**
   * Authenticate with email/phone and password.
   * Sets HttpOnly session cookies (access_token, refresh_token, csrf_token).
   */
  login: async (credentials: LoginCredentials): Promise<TokenResponse> => {
    return apiClient<TokenResponse>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  },

  /**
   * Fetch current authenticated user and student profile.
   */
  getMe: async (): Promise<User> => {
    return apiClient<User>('/api/v1/auth/me', {
      method: 'GET',
    });
  },

  /**
   * Rotate refresh token and obtain renewed access session.
   */
  refreshToken: async (): Promise<TokenResponse> => {
    return apiClient<TokenResponse>('/api/v1/auth/refresh', {
      method: 'POST',
    });
  },

  /**
   * Terminate active session and clear all authentication cookies.
   */
  logout: async (): Promise<{ message: string }> => {
    return apiClient<{ message: string }>('/api/v1/auth/logout', {
      method: 'POST',
    });
  },
};
