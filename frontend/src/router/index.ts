import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import NewAdhesionForm from '../views/NewAdhesionForm.vue'
import LoadForm from '../views/LoadForm.vue'
import AdminView from '../views/AdminView.vue'
import ConfirmationPage from '../views/ConfirmationPage.vue'
import ActivityAdmin from '../views/ActivityAdmin.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/adhesion',
      name: 'adhesion',
      component: NewAdhesionForm
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
      path: '/admin/activities',
      name: 'admin-activities',
      component: ActivityAdmin
    },
    {
      path: '/confirmation',
      name: 'confirmation',
      component: ConfirmationPage
    },
    {
      path: '/admin/adherents-by-activity',
      name: 'admin-adherents-by-activity',
      component: () => import('../views/AdherentByActivity.vue')
    }
  ]
})

export default router
