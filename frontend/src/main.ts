import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import ConfirmationService from 'primevue/confirmationservice'
import ToastService from 'primevue/toastservice'
import { definePreset } from '@primeuix/themes'
import Aura from '@primeuix/themes/aura'
import 'primeicons/primeicons.css'

import App from './App.vue'
import router from './router'

declare global {
  interface Window {
    BACKEND_URL: string;
  }
}

import api from './api'
api.defaults.baseURL = window.BACKEND_URL || 'http://localhost:5173'

const FoyerPreset = definePreset(Aura, {
  semantic: {
    primary: {
      50: '#edf4fc',
      100: '#d4e4f8',
      200: '#a9c9f1',
      300: '#7bb0f0',
      400: '#4a90e2',
      500: '#3a7fd1',
      600: '#2e6ab3',
      700: '#225195',
      800: '#173a77',
      900: '#0e2659',
      950: '#071539'
    },
    colorScheme: {
      light: {
        surface: {
          0: '#ffffff',
          50: '#f8f8f8',
          100: '#f0f0f0',
          200: '#e0e0e0',
          300: '#d0d0d0',
          400: '#b0b0b0',
          500: '#808080',
          600: '#666666',
          700: '#555555',
          800: '#333333',
          900: '#1a1a1a',
          950: '#0d0d0d'
        }
      }
    }
  }
})

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(PrimeVue, {
  theme: {
    preset: FoyerPreset,
    options: {
      darkModeSelector: false,
      cssLayer: {
        name: 'primevue',
        order: 'primevue, app'
      }
    }
  }
})
app.use(ConfirmationService)
app.use(ToastService)

app.mount('#app')
