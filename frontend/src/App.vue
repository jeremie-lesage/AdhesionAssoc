<template>
  <div id="app">
    <nav>
      <RouterLink to="/">Accueil</RouterLink> |
      <RouterLink to="/adhesion">Nouveau Formulaire</RouterLink> |
      <RouterLink to="/load">Charger un Formulaire</RouterLink> |
      <RouterLink to="/admin">Administration</RouterLink>
    </nav>
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>