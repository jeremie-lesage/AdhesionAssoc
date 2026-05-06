<template>
  <div style="max-width: 800px; margin: 2rem auto; padding: 2rem">
    <h1 style="text-align: center; margin-bottom: 1.5rem">Espace Administration</h1>
    <p style="text-align: center; margin-bottom: 2rem">Bienvenue dans l'espace d'administration. Choisissez une section à gérer.</p>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem">
      <RouterLink v-for="item in navItems" :key="item.to" :to="item.to" style="text-decoration: none">
        <Card>
          <template #content>
            <div style="display: flex; align-items: center; gap: 1rem">
              <i :class="item.icon" style="font-size: 1.5rem" />
              <span style="font-weight: 500">{{ item.label }}</span>
            </div>
          </template>
        </Card>
      </RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router';
import Card from 'primevue/card';

const navItems = [
  { to: '/admin/adhesions', icon: 'pi pi-file', label: 'Gérer les Demandes d\'Adhésion' },
  { to: '/admin/contacts', icon: 'pi pi-envelope', label: 'Gérer les Demandes par Contact' },
  { to: '/admin/activities', icon: 'pi pi-list', label: 'Gérer les Activités' },
  { to: '/admin/adherents-by-activity', icon: 'pi pi-users', label: 'Voir les Adhérents par Activité' },
  { to: '/admin/accounts', icon: 'pi pi-key', label: 'Gérer les Comptes Administrateur' },
];
</script>
