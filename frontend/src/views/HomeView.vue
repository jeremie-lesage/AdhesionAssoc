<template>
  <div class="home-page public-view">
    <img src="@/assets/images/logo_foyer_rural.png" alt="Logo Foyer Rural de Fauverney" class="logo">
    <h1>Bienvenue au Foyer Rural !</h1>
    <p>Nous sommes ravis de vous compter parmi nous. Pour adhérer à notre association et participer à nos activités, veuillez suivre le processus d'inscription ci-dessous.</p>

    <h2>Processus d'adhésion :</h2>
    <ol>
      <li><strong>Saisie des coordonnées :</strong> Commencez par nous fournir votre adresse email.</li>
      <li><strong>Informations personnelles :</strong> Remplissez vos détails personnels (nom, prénom, date de naissance, adresse postale).</li>
      <li><strong>Choix des activités :</strong> Sélectionnez une ou plusieurs activités parmi celles que nous proposons (Danse, Gym, Pilate).</li>
      <li><strong>Récapitulatif et validation :</strong> Vérifiez toutes les informations saisies et validez votre demande. Un code d'accès unique vous sera fourni pour modifier votre demande ultérieurement.</li>
    </ol>

    Vous devez faire <b>une demande par adhérent</b>, mais vous pouvez utiliser <u>la même adresse email</u> de contact.

    <h2>Actions disponibles :</h2>
    <div class="action-buttons">
      <button @click="startNewForm" class="button">Nouveau Formulaire</button>
      <RouterLink to="/load" class="button">Charger un Formulaire</RouterLink>
      <RouterLink to="/admin" class="button">Administration</RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink, useRouter } from 'vue-router';
import { useFormStore } from '@/stores/form';

const router = useRouter();
const formStore = useFormStore();

const startNewForm = () => {
  formStore.resetForm();
  router.push('/adhesion');
};
</script>

<style scoped>
.home-page {
  text-align: center;
  padding: 1.5rem;
}

.home-page h1 {
  color: var(--color-primary);
  margin-bottom: 1.5rem;
}

.home-page .logo {
  max-width: 10rem; /* Ajustez la taille selon vos besoins */
  height: auto;
  margin-bottom: 1rem;
}

.home-page h2 {
  color: var(--color-primary);
  margin-top: 2rem;
  margin-bottom: 1rem;
}

.home-page p {
  margin-bottom: 1rem;
}

.home-page ol {
  text-align: left;
  margin: 0 auto 2rem auto;
  max-width: 40rem;
  padding-left: 1.5rem;
}

.home-page ol li {
  margin-bottom: 0.8rem;
}

.action-buttons {
  margin-top: 3rem;
  display: flex;
  justify-content: center;
  gap: 1.5rem;
}

.button {
  display: inline-block;
  background-color: var(--color-primary);
  color: white;
  padding: 0.8rem 1.5rem;
  border-radius: 5px;
  text-decoration: none;
  font-weight: 600;
  transition: background-color 0.3s ease;
}

@media (max-width: 768px) {
  .action-buttons {
    flex-direction: column;
  }
}

.button:hover {
  background-color: var(--color-primary-light);
}
</style>
