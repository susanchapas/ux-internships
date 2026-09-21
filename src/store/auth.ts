import { create } from 'zustand';
import { getAuthSource } from '../api/auth';
import { usesFirebaseAuth } from '../api/mode';
import type { LoginCredentials, RegisterCredentials, User } from '../api/types';
import { ADMIN_EMAIL } from '../utils/constants';

interface AuthState {
  user: User | null;
  isLoading: boolean;
  error: string | null;
  init: () => () => void;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
  updateUsername: (name: string) => Promise<void>;
  updateEmail: (email: string) => Promise<void>;
  updatePassword: (current: string, next: string) => Promise<void>;
  isAdmin: () => boolean;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isLoading: true,
  error: null,

  init: () => {
    const authSource = getAuthSource();
    set({ isLoading: true });
    return authSource.onAuthStateChanged((user) => {
      set({ user, isLoading: false, error: null });
    });
  },

  login: async (credentials) => {
    set({ isLoading: true, error: null });
    try {
      const user = await getAuthSource().login(credentials);
      set({ user, isLoading: false, error: null });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Login failed';
      set({ isLoading: false, error: msg });
      throw err;
    }
  },

  register: async (credentials) => {
    set({ isLoading: true, error: null });
    try {
      const user = await getAuthSource().register(credentials);
      // Firebase registers and signs the user in; the server deliberately
      // requires a separate sign-in after creating the account.
      set({ user: usesFirebaseAuth() ? user : null, isLoading: false, error: null });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Registration failed';
      set({ isLoading: false, error: msg });
      throw err;
    }
  },

  loginWithGoogle: async () => {
    set({ isLoading: true, error: null });
    try {
      const user = await getAuthSource().loginWithGoogle();
      set({ user, isLoading: false, error: null });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Google sign-in failed';
      set({ isLoading: false, error: msg });
      throw err;
    }
  },

  logout: async () => {
    set({ isLoading: true });
    try {
      await getAuthSource().logout();
      set({ user: null, isLoading: false, error: null });
    } catch (err: unknown) {
      set({ isLoading: false });
      throw err;
    }
  },

  updateUsername: async (name: string) => {
    await getAuthSource().updateUsername(name);
    const current = get().user;
    if (current) {
      set({ user: { ...current, username: name } });
    }
  },

  updateEmail: async (email: string) => {
    await getAuthSource().updateEmail(email);
    const current = get().user;
    if (current) {
      set({ user: { ...current, email } });
    }
  },

  updatePassword: async (current: string, next: string) => {
    await getAuthSource().updatePassword(current, next);
  },

  isAdmin: () => {
    const user = get().user;
    if (!user) return false;
    return user.role === 'admin' || user.email === ADMIN_EMAIL;
  },

  clearError: () => set({ error: null }),
}));
