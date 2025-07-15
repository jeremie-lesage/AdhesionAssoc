import axios from 'axios';
import type { AdminUser, AdminUserCreate, Activity, Adhesion, AdhesionCreate } from './types';

const backendUrl = window.BACKEND_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: backendUrl,
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('admin_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export const login = async (credentials: any) => {
  const params = new URLSearchParams();
  params.append('username', credentials.username);
  params.append('password', credentials.password);
  const response = await api.post('/api/token', params);
  const token = response.data.access_token;
  localStorage.setItem('admin_token', token);
  return token;
};

export const getAdmins = async (): Promise<AdminUser[]> => {
  const response = await api.get('/api/admins');
  return response.data;
};

export const createAdmin = async (admin: AdminUserCreate): Promise<AdminUser> => {
  const response = await api.post('/api/admins', admin);
  return response.data;
};

export const updateAdmin = async (id: number, admin: AdminUserCreate): Promise<AdminUser> => {
  const response = await api.put(`/api/admins/${id}`, admin);
  return response.data;
};

export const deleteAdmin = async (id: number): Promise<void> => {
  await api.delete(`/api/admins/${id}`);
};

export const getActivities = async (): Promise<Activity[]> => {
    const response = await api.get('/api/activities');
    return response.data;
};

export const createActivity = async (activity: Activity): Promise<Activity> => {
    const response = await api.post('/api/activities', activity);
    return response.data;
};

export const updateActivity = async (id: number, activity: Activity): Promise<Activity> => {
    const response = await api.put(`/api/activities/${id}`, activity);
    return response.data;
};

export const deleteActivity = async (id: number): Promise<void> => {
    await api.delete(`/api/activities/${id}`);
};

export const getAdhesions = async (): Promise<Adhesion[]> => {
    const response = await api.get('/api/adhesions');
    return response.data;
};

export const createAdhesion = async (adhesion: AdhesionCreate): Promise<Adhesion> => {
    const response = await api.post('/api/adhesions', adhesion);
    return response.data;
};

export const getAdhesionByCode = async (code: string): Promise<Adhesion> => {
    const response = await api.get(`/api/adhesions/${code}`);
    return response.data;
};

export const validateAdhesion = async (code: string): Promise<Adhesion> => {
    const response = await api.put(`/api/adhesions/${code}/validate`);
    return response.data;
};

export const updateAdhesion = async (code: string, adhesion: AdhesionCreate): Promise<Adhesion> => {
    const response = await api.put(`/api/adhesions/${code}`, adhesion);
    return response.data;
};

export const getAdherentsByActivity = async (activityId: number): Promise<Adhesion[]> => {
    const response = await api.get(`/api/activities/${activityId}/adherents`);
    return response.data;
};

export default api;