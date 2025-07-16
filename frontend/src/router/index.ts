import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import NewAdhesionForm from '../views/NewAdhesionForm.vue'
import LoadForm from '../views/LoadForm.vue'
import AdminView from '../views/AdminView.vue'
import ConfirmationPage from '../views/ConfirmationPage.vue'
import ActivityAdmin from '../views/ActivityAdmin.vue'
import AdminLogin from '../views/AdminLogin.vue'

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
      path: '/admin/login',
      name: 'admin-login',
      component: AdminLogin
    },
    {
      path: '/admin',
      name: 'admin',
      component: AdminView,
      meta: { requiresAuth: true }
    },
    {
      path: '/admin/adhesions',
      name: 'admin-adhesions',
      component: () => import('../views/AdhesionAdminView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/admin/activities',
      name: 'admin-activities',
      component: ActivityAdmin,
      meta: { requiresAuth: true }
    },
    {
      path: '/confirmation',
      name: 'confirmation',
      component: ConfirmationPage
    },
    {
      path: '/admin/adherents-by-activity',
      name: 'admin-adherents-by-activity',
      component: () => import('../views/AdherentByActivity.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/admin/accounts',
      name: 'admin-accounts',
      component: () => import('../views/AdminAccounts.vue'),
      meta: { requiresAuth: true }
    }
  ]
})

router.beforeEach((to, from, next) => {
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!localStorage.getItem('admin_token')) {
      next({ name: 'admin-login' });
    } else {
      next();
    }
  } else {
    next();
  }
});

export default router
