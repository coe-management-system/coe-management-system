export interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'faculty' | 'coordinator' | 'student';
  department?: string;
  avatarUrl?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface AuthResponse {
  user: User;
  token: string;
  expiresIn: number;
}
