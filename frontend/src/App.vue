<template>
  <nav v-if="!isAdminRoute" class="site-nav">
    <!-- Barre visible uniquement sous 768px : le menu y est replié derrière le
         bouton. Sur desktop les entrées restent alignées, cette barre disparaît. -->
    <div class="nav-bar">
      <span class="nav-brand">Foyer Rural de Fauverney</span>
      <button
        type="button"
        class="nav-toggle"
        aria-controls="site-menu"
        :aria-expanded="menuOpen"
        :aria-label="menuOpen ? 'Fermer le menu' : 'Ouvrir le menu'"
        @click="menuOpen = !menuOpen"
      >
        <i :class="menuOpen ? 'pi pi-times' : 'pi pi-bars'" aria-hidden="true" />
      </button>
    </div>

    <ul id="site-menu" class="nav-links" :class="{ open: menuOpen }">
      <!-- Pas de lien vers la page courante : sur l'accueil il ne mènerait nulle part -->
      <li v-if="!isHome"><RouterLink to="/">Accueil</RouterLink></li>
      <li>
        <button @click="startNewForm" class="nav-button">Nouveau Formulaire</button>
      </li>
      <li><RouterLink to="/planning">Planning</RouterLink></li>
      <li><RouterLink to="/load">Reprendre mon inscription</RouterLink></li>
      <li><RouterLink to="/admin">Administration</RouterLink></li>
    </ul>
  </nav>
  <router-view />
</template>

<script lang="ts" setup>
import { computed, ref, watch } from 'vue';
import { RouterLink, RouterView, useRouter, useRoute } from 'vue-router';
import { useFormStore } from '@/stores/form';

const router = useRouter();
const route = useRoute();
const formStore = useFormStore();

const menuOpen = ref(false);

const isAdminRoute = computed(() => route.path.startsWith('/admin'));
const isWideRoute = computed(() => route.path === '/planning');
const isHome = computed(() => route.path === '/');

watch([isAdminRoute, isWideRoute], ([isAdmin, isWide]) => {
  document.getElementById('app')?.classList.toggle('no-shell', isAdmin);
  document.getElementById('app')?.classList.toggle('wide-shell', isWide);
}, { immediate: true });

// Le panneau mobile reste monté d'une route à l'autre : sans ça il masquerait
// le haut de la page d'arrivée après un clic sur une entrée.
watch(() => route.path, () => {
  menuOpen.value = false;
});

const startNewForm = () => {
  formStore.resetForm();
  router.push('/adhesion');
};
</script>

<style scoped>
.nav-bar {
  display: none;
}

.nav-links {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
}

/* Les séparateurs « | » étaient écrits en dur dans le template : en pseudo-élément
   ils disparaissent tout seuls quand le menu passe en colonne. */
.nav-links li + li::before {
  content: '|';
  color: var(--color-border);
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

.nav-toggle {
  background: none;
  border: none;
  color: var(--color-primary);
  font-size: 1.4rem;
  line-height: 1;
  padding: 0.5rem;
  border-radius: 4px;
  cursor: pointer;
}
.nav-toggle:hover {
  background-color: var(--color-hover);
}

.nav-brand {
  font-weight: 600;
  color: var(--color-primary);
}

@media screen and (max-width: 768px) {
  .nav-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
  }

  .nav-links {
    display: none;
    flex-direction: column;
    align-items: stretch;
    gap: 0;
    margin-top: 0.5rem;
  }

  .nav-links.open {
    display: flex;
  }

  .nav-links li + li::before {
    content: none;
  }

  /* Les liens sont inline par défaut : sans display:block la zone tactile
     ne fait pas la largeur du panneau et le padding vertical est ignoré. */
  .nav-links a,
  .nav-links .nav-button {
    display: block;
    width: 100%;
    box-sizing: border-box;
    text-align: left;
    padding: 0.75rem 1rem;
    border-radius: 4px;
  }

  .nav-links li + li {
    border-top: 1px solid var(--color-border);
  }
}
</style>
