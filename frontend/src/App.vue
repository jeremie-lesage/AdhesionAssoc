<template>
  <nav v-if="!isAdminRoute">
    <RouterLink to="/">Accueil</RouterLink>
    <span class="hide-mobile">
      |
      <button @click="startNewForm" class="nav-button">Nouveau Formulaire</button>
      |
      <RouterLink to="/planning">Planning</RouterLink>
      |
      <RouterLink to="/load">Reprendre mon inscription</RouterLink>
      |
      <RouterLink to="/admin">Administration</RouterLink>
    </span>
  </nav>
  <router-view />
</template>

<script lang="ts" setup>
import { computed, watch } from 'vue';
import { RouterLink, RouterView, useRouter, useRoute } from 'vue-router';
import { useFormStore } from '@/stores/form';

const router = useRouter();
const route = useRoute();
const formStore = useFormStore();

const isAdminRoute = computed(() => route.path.startsWith('/admin'));
const isWideRoute = computed(() => route.path === '/planning');

watch([isAdminRoute, isWideRoute], ([isAdmin, isWide]) => {
  document.getElementById('app')?.classList.toggle('no-shell', isAdmin);
  document.getElementById('app')?.classList.toggle('wide-shell', isWide);
}, { immediate: true });

const startNewForm = () => {
  formStore.resetForm();
  router.push('/adhesion');
};
</script>

<style scoped>
@media screen and (max-width: 768px) {
  .hide-mobile {
    display: none;
  }
}

.nav-button {
  background: none;
  border: none;
  font-family: inherit;
  font-size: inherit;
  color: var(--color-primary);
  font-weight: 500;
  padding: 8px 1rem;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}
.nav-button:hover {
  background-color: var(--color-hover);
}
</style>
