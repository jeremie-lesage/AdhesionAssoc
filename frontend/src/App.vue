<template>
  <div id="app">
    <nav>
      <RouterLink to="/">Accueil</RouterLink>
      <span class="hide-mobile"
      >
        |
        <RouterLink to="/adhesion">Nouveau Formulaire</RouterLink>
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
import {RouterLink, RouterView} from 'vue-router'
</script>


<style>
@media screen and (max-width: 768px) {
  .hide-mobile {
    display: none;
  }
}
</style>
