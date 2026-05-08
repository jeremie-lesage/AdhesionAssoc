<template>
  <div class="admin-layout">
    <aside class="admin-sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <h2 v-if="!sidebarCollapsed">Administration</h2>
        <Button
          :icon="sidebarCollapsed ? 'pi pi-bars' : 'pi pi-times'"
          text
          rounded
          @click="sidebarCollapsed = !sidebarCollapsed"
        />
      </div>
      <nav class="sidebar-nav">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="sidebar-link"
          :class="{ active: isActive(item.to) }"
        >
          <i :class="item.icon" />
          <span v-if="!sidebarCollapsed">{{ item.label }}</span>
        </RouterLink>
      </nav>
      <div class="sidebar-footer">
        <RouterLink to="/" class="sidebar-link">
          <i class="pi pi-home" />
          <span v-if="!sidebarCollapsed">Retour au site</span>
        </RouterLink>
        <a href="#" class="sidebar-link" @click.prevent="logout">
          <i class="pi pi-sign-out" />
          <span v-if="!sidebarCollapsed">Déconnexion</span>
        </a>
      </div>
    </aside>
    <main class="admin-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { RouterLink, useRouter, useRoute } from 'vue-router';
import Button from 'primevue/button';

const router = useRouter();
const route = useRoute();
const sidebarCollapsed = ref(false);

const navItems = [
  { to: '/admin/adhesions', icon: 'pi pi-file', label: 'Adhésions' },
  { to: '/admin/contacts', icon: 'pi pi-envelope', label: 'Contacts' },
  { to: '/admin/activities', icon: 'pi pi-list', label: 'Activités' },
  { to: '/admin/adherents-by-activity', icon: 'pi pi-users', label: 'Par activité' },
  { to: '/admin/accounts', icon: 'pi pi-key', label: 'Comptes admin' },
];

const isActive = (path: string) => route.path.startsWith(path);

const logout = () => {
  localStorage.removeItem('admin_token');
  router.push('/admin/login');
};
</script>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
  margin: -1rem;
  background-color: var(--p-surface-50, #f8f8f8);
}

.admin-sidebar {
  width: 260px;
  background-color: var(--p-surface-800, #1e293b);
  color: var(--p-surface-0, #fff);
  display: flex;
  flex-direction: column;
  transition: width 0.2s ease;
  flex-shrink: 0;
}

.admin-sidebar.collapsed {
  width: 60px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid var(--p-surface-700, #334155);
}

.sidebar-header h2 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--p-surface-0, #fff);
  white-space: nowrap;
}

.sidebar-nav {
  flex: 1;
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sidebar-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  color: var(--p-surface-300, #cbd5e1);
  text-decoration: none;
  font-size: 0.9rem;
  transition: all 0.15s ease;
  white-space: nowrap;
  overflow: hidden;
}

.sidebar-link:hover {
  background-color: var(--p-surface-700, #334155);
  color: var(--p-surface-0, #fff);
}

.sidebar-link.active {
  background-color: var(--p-primary-400, #4a90e2);
  color: var(--p-surface-0, #fff);
  font-weight: 500;
}

.sidebar-link i {
  font-size: 1.1rem;
  min-width: 1.25rem;
  text-align: center;
}

.sidebar-footer {
  padding: 0.5rem;
  border-top: 1px solid var(--p-surface-700, #334155);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.admin-content {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
  min-width: 0;
}

.collapsed .sidebar-link {
  justify-content: center;
  padding: 0.75rem;
}

.collapsed .sidebar-header {
  justify-content: center;
}

@media screen and (max-width: 768px) {
  .admin-sidebar {
    width: 60px;
  }

  .admin-sidebar .sidebar-link span,
  .admin-sidebar .sidebar-header h2 {
    display: none;
  }

  .admin-sidebar .sidebar-link {
    justify-content: center;
    padding: 0.75rem;
  }

  .admin-sidebar .sidebar-header {
    justify-content: center;
  }
}
</style>
