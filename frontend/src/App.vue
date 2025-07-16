<template>
  <div id="app">
    <nav>
      <RouterLink to="/">Accueil</RouterLink>
      <span class="hide-mobile">
        |
        <button @click="startNewForm" class="button">Nouveau Formulaire</button>
        |
        <RouterLink to="/load">Charger un Formulaire</RouterLink>
        |
        <RouterLink to="/admin">Administration</RouterLink>
      </span>
    </nav>
    <router-view/>
  </div>
</template>

<script lang="ts" setup>
import {RouterLink, RouterView, useRouter} from 'vue-router'
import {useFormStore} from "@/stores/form.ts";

const router = useRouter();
const formStore = useFormStore();
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


.button {
  display: inline-block;
  background-color: white;
  color: var(--color-primary);
  font-weight: 500;
  transition: background-color 0.3s ease;
}
.button:hover {
  background-color: var(--color-hover);
}
</style>
