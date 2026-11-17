import axios from 'axios';
import { getErrorMessage } from './errors';

export const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
});

const TOAST_STATUSES = new Set([400, 401, 403, 404, 500]);

const dispatchAppError = (message, status) => {
  window.dispatchEvent(new CustomEvent('app_error', { detail: { message, status } }));
};

const dispatchLogout = () => {
  window.dispatchEvent(new CustomEvent('auth_logout'));
};

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let isRefreshing = false;
let refreshQueue = [];

const processQueue = (error, token) => {
  refreshQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(token);
    }
  });
  refreshQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error;
    const status = response?.status;
    const isAuthRoute = config?.url === '/login' || config?.url === '/register' || config?.url === '/refresh';

    if (status === 401 && !isAuthRoute && !config._retry) {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        dispatchLogout();
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          refreshQueue.push({ resolve, reject });
        })
          .then((newToken) => {
            config._retry = true;
            config.headers.Authorization = `Bearer ${newToken}`;
            return api(config);
          })
          .catch((queueError) => Promise.reject(queueError));
      }

      config._retry = true;
      isRefreshing = true;
      try {
        const refreshResponse = await axios.post(`${API_BASE_URL}/refresh`, { refresh_token: refreshToken });
        const newAccessToken = refreshResponse.data.access_token;
        localStorage.setItem('access_token', newAccessToken);
        processQueue(null, newAccessToken);
        config.headers.Authorization = `Bearer ${newAccessToken}`;
        return api(config);
      } catch (refreshError) {
        processQueue(refreshError, null);
        dispatchLogout();
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    const message = getErrorMessage(error);
    if (status && TOAST_STATUSES.has(status)) {
      dispatchAppError(message, status);
    }

    return Promise.reject(error);
  }
);

export default api;
