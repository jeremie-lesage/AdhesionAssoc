<template>
  <nav v-if="!isAdminRoute">
    <RouterLink to="/">Accueil</RouterLink>
    <span class="hide-mobile">
      |
      <button @click="startNewForm" class="nav-button">Nouveau Formulaire</button>
      |
      <RouterLink to="/load">Charger un Formulaire</RouterLink>
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

watch(isAdminRoute, (isAdmin) => {
  document.getElementById('app')?.classList.toggle('no-shell', isAdmin);
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
  display: inline-block;
  background-color: white;
  color: var(--color-primary);
  font-weight: 500;
  transition: background-color 0.3s ease;
}
.nav-button:hover {
  background-color: var(--color-hover);
}
</style>
