import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

// Declare window.BACKEND_URL to avoid TypeScript errors
declare global {
  interface Window {
    BACKEND_URL: string;
  }
}

// Set the base URL for axios based on the global variable or default
// This needs to be done before any component tries to make an API call
import api from './api'; // Import the configured axios instance
api.defaults.baseURL = window.BACKEND_URL || 'http://localhost:5173';

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
