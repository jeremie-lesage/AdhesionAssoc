import axios from 'axios';

const backendUrl = window.BACKEND_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: backendUrl,
});

export default api;
