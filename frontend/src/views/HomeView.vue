<template>
  <div class="home-page">
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
  padding: 20px;
}

.home-page h1 {
  color: var(--color-primary);
  margin-bottom: 20px;
}

.home-page .logo {
  max-width: 150px; /* Ajustez la taille selon vos besoins */
  height: auto;
  margin-bottom: 30px;
}

.home-page h2 {
  color: var(--color-primary);
  margin-top: 30px;
  margin-bottom: 15px;
}

.home-page p {
  margin-bottom: 15px;
}

.home-page ol {
  text-align: left;
  margin: 0 auto 30px auto;
  max-width: 600px;
  padding-left: 20px;
}

.home-page ol li {
  margin-bottom: 10px;
}

.action-buttons {
  margin-top: 40px;
  display: flex;
  justify-content: center;
  gap: 20px;
}

.button {
  display: inline-block;
  background-color: var(--color-primary);
  color: white;
  padding: 12px 25px;
  border-radius: 5px;
  text-decoration: none;
  font-weight: 600;
  transition: background-color 0.3s ease;
}

.button:hover {
  background-color: var(--color-primary-light);
}
</style>
