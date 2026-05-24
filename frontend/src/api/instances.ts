import axios from 'axios';

const CORE_URL = 'http://127.0.0.1:8081';
const MEDIA_URL = 'http://127.0.0.1:8000';

export const coreApi = axios.create({ baseURL: CORE_URL });
export const mediaApi = axios.create({ baseURL: MEDIA_URL });

// --- ПЕРЕМЕННЫЕ ДЛЯ ОЧЕРЕДИ ---
let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};
// ------------------------------

const authInterceptor = (config: any) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
};

coreApi.interceptors.request.use(authInterceptor);
mediaApi.interceptors.request.use(authInterceptor);

// Единый перехватчик ответов (можно применить к обоим API)
const responseInterceptor = async (error: any) => {
  const originalRequest = error.config;

  if (error.response?.status === 401 && !originalRequest._retry) {
    
    if (isRefreshing) {
      // Если обновление уже идет, создаем Promise, который подождет
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      })
        .then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return axios(originalRequest);
        })
        .catch((err) => Promise.reject(err));
    }

    originalRequest._retry = true;
    isRefreshing = true;

    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      isRefreshing = false;
      return Promise.reject(error);
    }

    try {
      // Используем чистый axios, чтобы не зациклиться
      const res = await axios.post(`${CORE_URL}/auth/refresh`, {}, {
        headers: { Authorization: `Bearer ${refreshToken}` }
      });

      const { access_token, refresh_token } = res.data;
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);

      // Пропускаем все накопившиеся в очереди запросы с новым токеном
      processQueue(null, access_token);
      
      originalRequest.headers.Authorization = `Bearer ${access_token}`;
      return axios(originalRequest);
    } catch (refreshError) {
      processQueue(refreshError, null);
      localStorage.clear();
      // Можно не редиректить жестко, а просто обнулить стор
      window.location.href = '/login';
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }

  return Promise.reject(error);
};

coreApi.interceptors.response.use((r) => r, responseInterceptor);
mediaApi.interceptors.response.use((r) => r, responseInterceptor);