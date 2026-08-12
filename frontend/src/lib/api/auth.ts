import { LoginCredentials, AuthResponse } from '@/types/auth';
import { MOCK_USER } from '@/lib/mock-data/auth';
import { mockApiCall } from './client';

export const authApi = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    // Validate mock credentials format
    if (!credentials.email || !credentials.password) {
      throw new Error('Email and password are required.');
    }

    if (!credentials.email.includes('@')) {
      throw new Error('Please enter a valid institutional email address.');
    }

    if (credentials.password.length < 8) {
      throw new Error('Password must be at least 8 characters.');
    }

    // Return mock successful authentication payload
    return mockApiCall<AuthResponse>({
      user: {
        ...MOCK_USER,
        email: credentials.email,
      },
      token: 'mock-jwt-token-coe-day1-m4',
      expiresIn: 86400,
    }, 400);
  },

  async getCurrentUser() {
    return mockApiCall(MOCK_USER);
  },
};
