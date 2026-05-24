import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { coreApi } from '../api/instances';

interface User {
  id: number;
  username: string;
  email: string;
  is_superuser: boolean;
  image_key?: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  setAuth: (user: User, accessToken: string, refreshToken: string) => void;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,

      setAuth: (user, accessToken, refreshToken) => {
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
        set({ user, isAuthenticated: true });
      },

      logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        set({ user: null, isAuthenticated: false });
      },

      // src/store/useAuthStore.ts

      checkAuth: async () => {
        const token = localStorage.getItem('access_token');
        if (!token) {
          set({ user: null, isAuthenticated: false });
          return;
        }
        
        try {
          const response = await coreApi.get('/user/profile');
          set({ user: response.data, isAuthenticated: true });
        } catch (error) {
          // ВАЖНО: Не удаляй здесь ничего! 
          // Если здесь 401 ошибка, интерцептор поймает её, обновит токен и повторит запрос.
          // Если даже рефреш не сработает, интерцептор сам сделает logout.
          console.error("CheckAuth failed, waiting for interceptor...");
        }
      },
    }),
    { name: 'mray-auth-storage' }
  )
);