'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { api } from '@/lib/api';

export interface UserProfile {
  id: number;
  username: string;
  email: string;
  role_id: number;
  role?: string;
}

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  error: string | null;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const PUBLIC_ROUTES = ['/login', '/_not-found'];

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const router = useRouter();
  const pathname = usePathname();

  const logout = useCallback(() => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('coe_auth_token');
      localStorage.removeItem('coe_user');
    }
    setToken(null);
    setUser(null);
    router.push('/login');
  }, [router]);

  // Handle centralized 401 unauthorized session expiry
  useEffect(() => {
    const handleUnauthorized = () => {
      logout();
    };
    window.addEventListener('coe_unauthorized', handleUnauthorized);
    return () => window.removeEventListener('coe_unauthorized', handleUnauthorized);
  }, [logout]);

  // Initial load of token from localStorage
  useEffect(() => {
    const initAuth = async () => {
      setIsLoading(true);
      if (typeof window !== 'undefined') {
        const storedToken = localStorage.getItem('coe_auth_token');
        const storedUser = localStorage.getItem('coe_user');

        if (storedToken) {
          setToken(storedToken);
          if (storedUser) {
            try {
              setUser(JSON.parse(storedUser));
            } catch {
              // fallback
            }
          }
          // Fetch current user from backend GET /api/v1/auth/me
          try {
            const me = await api.getMe(storedToken);
            if (me) {
              const roleName = me.role_id === 1 ? 'Admin' : me.role_id === 2 ? 'Faculty' : 'Student';
              const fullUser: UserProfile = { ...me, role: roleName };
              setUser(fullUser);
              localStorage.setItem('coe_user', JSON.stringify(fullUser));
            }
          } catch (err) {
            console.error('Failed to validate session token', err);
            // If token invalid, clear
            localStorage.removeItem('coe_auth_token');
            localStorage.removeItem('coe_user');
            setToken(null);
            setUser(null);
          }
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  // Protect private routes
  useEffect(() => {
    if (!isLoading) {
      const isPublic = PUBLIC_ROUTES.some((route) => pathname.startsWith(route));
      if (!token && !isPublic) {
        router.push('/login');
      }
    }
  }, [token, isLoading, pathname, router]);

  const login = async (username: string, password: string) => {
    setError(null);
    try {
      const res = await api.login(username, password);
      setToken(res.access_token);
      if (typeof window !== 'undefined') {
        localStorage.setItem('coe_auth_token', res.access_token);
      }

      // Fetch user profile
      const me = await api.getMe(res.access_token);
      const roleName = me.role_id === 1 ? 'Admin' : me.role_id === 2 ? 'Faculty' : 'Student';
      const fullUser: UserProfile = { ...me, role: roleName };

      setUser(fullUser);
      if (typeof window !== 'undefined') {
        localStorage.setItem('coe_user', JSON.stringify(fullUser));
      }

      router.push('/dashboard');
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Invalid username or password.';
      setError(msg);
      throw err;
    }
  };

  const clearError = () => setError(null);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token,
        isLoading,
        login,
        logout,
        error,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
