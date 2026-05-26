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
  updateUserData: (user: User) => void;
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
             
          console.error("CheckAuth failed, waiting for interceptor...");
        }
      },

      updateUserData: (updatedUser) => {
        set({ user: updatedUser });
      },

    }),
    { name: 'mray-auth-storage' }
  )
);