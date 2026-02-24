import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  register: (userData) => api.post('/auth/register', userData),
  getMe: () => api.get('/auth/me'),
};

// Devices API
export const devicesAPI = {
  getAll: () => api.get('/devices'),
  getById: (id) => api.get(`/devices/${id}`),
  create: (device) => api.post('/devices', device),
  update: (id, device) => api.put(`/devices/${id}`, device),
  delete: (id) => api.delete(`/devices/${id}`),
  reboot: (id) => api.post(`/devices/${id}/reboot`),
  otaUpdate: (id, data) => api.post(`/devices/${id}/ota-update`, data),
  changeWifi: (id, data) => api.post(`/devices/${id}/wifi`, data),
  controlLED: (id, data) => api.post(`/devices/${id}/led`, data),
  requestStatus: (id) => api.post(`/devices/${id}/status`),
};

// Schedules API
export const schedulesAPI = {
  getAll: (deviceId = null) => {
    const params = deviceId ? { device_id: deviceId } : {};
    return api.get('/schedules', { params });
  },
  getById: (id) => api.get(`/schedules/${id}`),
  create: (schedule) => api.post('/schedules', schedule),
  update: (id, schedule) => api.put(`/schedules/${id}`, schedule),
  delete: (id) => api.delete(`/schedules/${id}`),
};

export default api;
