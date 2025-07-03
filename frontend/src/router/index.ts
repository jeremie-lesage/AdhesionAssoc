import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import LoadForm from '../views/LoadForm.vue'
import AdminView from '../views/AdminView.vue'
import ConfirmationPage from '../views/ConfirmationPage.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/load',
      name: 'load',
      component: LoadForm
    },
    {
      path: '/admin',
      name: 'admin',
      component: AdminView
    },
    {
      path: '/confirmation',
      name: 'confirmation',
      component: ConfirmationPage
    }
  ]
})

export default router
