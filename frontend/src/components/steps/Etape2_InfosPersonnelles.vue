<template>
  <div>
    <h2>Étape 2: Informations Personnelles</h2>
    <form @submit.prevent="nextStep">
      <div>
        <label for="nom">Nom:</label>
        <input type="text" id="nom" v-model="formData.nom" required>
      </div>
      <div>
        <label for="prenom">Prénom:</label>
        <input type="text" id="prenom" v-model="formData.prenom" required>
      </div>
      <div>
        <label for="date_naissance">Date de Naissance:</label>
        <input type="date" id="date_naissance" v-model="formData.date_naissance" required>
      </div>
      <div>
        <label for="numero_rue">Numéro de la rue:</label>
        <input type="text" id="numero_rue" v-model="formData.numero_rue" required>
      </div>
      <div>
        <label for="nom_rue">Nom de la rue:</label>
        <input type="text" id="nom_rue" v-model="formData.nom_rue" required>
      </div>
      <div>
        <label for="code_postal">Code Postal:</label>
        <input type="text" id="code_postal" v-model="formData.code_postal" required>
      </div>
      <div>
        <label for="ville">Ville:</label>
        <input type="text" id="ville" v-model="formData.ville" required>
      </div>
      <button @click="prevStep">Précédent</button>
      <button type="submit">Suivant</button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { useFormStore } from '@/stores/form';

const store = useFormStore();
const formData = store.formData;

const nextStep = () => {
  store.nextStep();
};

const prevStep = () => {
  store.prevStep();
};
</script>
