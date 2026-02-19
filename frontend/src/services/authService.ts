import { signInWithPopup, signOut, User as FirebaseUser } from 'firebase/auth';
import { auth, googleProvider } from '../config/firebase';
import api from './api';
import { User } from '../types';

interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export const authService = {
  async signInWithGoogle(): Promise<AuthResponse> {
    const result = await signInWithPopup(auth, googleProvider);
    const idToken = await result.user.getIdToken();

    const response = await api.post<AuthResponse>('/auth/google', {
      id_token: idToken,
    });

    localStorage.setItem('token', response.data.access_token);
    return response.data;
  },

  async signOut(): Promise<void> {
    await signOut(auth);
    localStorage.removeItem('token');
  },

  async getCurrentUser(): Promise<User | null> {
    const token = localStorage.getItem('token');
    if (!token) return null;

    try {
      const response = await api.get<User>('/users/me');
      return response.data;
    } catch {
      localStorage.removeItem('token');
      return null;
    }
  },

  getToken(): string | null {
    return localStorage.getItem('token');
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('token');
  },
};
