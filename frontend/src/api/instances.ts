import axios from 'axios';

export const coreApi = axios.create({
  baseURL: import.meta.env.VITE_CORE_API_URL,
});

export const mediaApi = axios.create({
  baseURL: import.meta.env.VITE_MEDIA_API_URL,
});

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


const authInterceptor = (config: any) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
};

coreApi.interceptors.request.use(authInterceptor);
mediaApi.interceptors.request.use(authInterceptor);


const responseInterceptor = async (error: any) => {
  const originalRequest = error.config;

  if (error.response?.status === 401 && !originalRequest._retry) {
    
    if (isRefreshing) {
      
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
      
      const res = await axios.post(`${import.meta.env.VITE_CORE_API_URL}/auth/refresh`, {}, {
        headers: { Authorization: `Bearer ${refreshToken}` }
      });

      const { access_token, refresh_token } = res.data;
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);

      
      processQueue(null, access_token);
      
      originalRequest.headers.Authorization = `Bearer ${access_token}`;
      return axios(originalRequest);
    } catch (refreshError) {
      processQueue(refreshError, null);
      localStorage.clear();
      
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