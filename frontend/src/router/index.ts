import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import NewAdhesionForm from '../views/NewAdhesionForm.vue'
import LoadForm from '../views/LoadForm.vue'
import AdminLogin from '../views/AdminLogin.vue'
import AdminLayout from '../layouts/AdminLayout.vue'

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
      path: '/planning',
      name: 'planning',
      component: () => import('../views/CalendarView.vue')
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
      component: AdminLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'admin',
          redirect: '/admin/dashboard'
        },
        {
          path: 'dashboard',
          name: 'admin-dashboard',
          component: () => import('../views/admin/DashboardView.vue')
        },
        {
          path: 'adhesions',
          name: 'admin-adhesions',
          component: () => import('../views/AdhesionAdminView.vue')
        },
        {
          path: 'adhesions/:code',
          name: 'admin-adhesion-detail',
          component: () => import('../views/admin/AdhesionDetailView.vue'),
          props: true
        },
        {
          path: 'activities',
          name: 'admin-activities',
          component: () => import('../views/ActivityAdmin.vue')
        },
        {
          path: 'adherents-by-activity',
          name: 'admin-adherents-by-activity',
          component: () => import('../views/AdherentByActivity.vue')
        },
        {
          path: 'accounts',
          name: 'admin-accounts',
          component: () => import('../views/AdminAccounts.vue')
        },
        {
          path: 'contacts',
          name: 'ContactsList',
          component: () => import('../views/admin/ContactsListView.vue')
        },
        {
          path: 'contacts/:email',
          name: 'FamilyDetails',
          component: () => import('../views/admin/FamilyDetailsView.vue'),
          props: true
        }
      ]
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
