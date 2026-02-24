import { create } from 'zustand';
import { authAPI } from '../services/api';

export const useAuthStore = create((set) => ({
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  token: localStorage.getItem('token') || null,
  isAuthenticated: !!localStorage.getItem('token'),
  
  login: async (credentials) => {
    const response = await authAPI.login(credentials);
    const { access_token } = response.data;
    localStorage.setItem('token', access_token);
    
    // Fetch user info
    const userResponse = await authAPI.getMe();
    const user = userResponse.data;
    localStorage.setItem('user', JSON.stringify(user));
    
    set({ token: access_token, user, isAuthenticated: true });
    return user;
  },
  
  register: async (userData) => {
    await authAPI.register(userData);
    // After registration, automatically login
    return await useAuthStore.getState().login({
      username: userData.username,
      password: userData.password
    });
  },
  
  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    set({ token: null, user: null, isAuthenticated: false });
  },
}));

export const useDeviceStore = create((set) => ({
  devices: [],
  selectedDevice: null,
  loading: false,
  error: null,
  
  setDevices: (devices) => set({ devices }),
  setSelectedDevice: (device) => set({ selectedDevice: device }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}));

export const useScheduleStore = create((set) => ({
  schedules: [],
  selectedSchedule: null,
  loading: false,
  error: null,
  
  setSchedules: (schedules) => set({ schedules }),
  setSelectedSchedule: (schedule) => set({ selectedSchedule: schedule }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}));
