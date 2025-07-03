<template>
  <div>
    <h2>Étape 4: Résumé</h2>
    <div>
      <p><strong>Email:</strong> {{ formData.email }}</p>
      <p><strong>Nom:</strong> {{ formData.nom }}</p>
      <p><strong>Prénom:</strong> {{ formData.prenom }}</p>
      <p><strong>Date de Naissance:</strong> {{ formData.date_naissance }}</p>
      <p><strong>Adresse Postale:</strong> {{ formData.adresse_postale }}</p>
      <p><strong>Activités:</strong> {{ formData.activites.join(', ') }}</p>
    </div>
    <button @click="prevStep">Précédent</button>
    <button @click="submitForm">Valider</button>
  </div>
</template>

<script setup lang="ts">
import { useFormStore } from '@/stores/form';
import axios from 'axios';
import { useRouter } from 'vue-router';

const store = useFormStore();
const formData = store.formData;
const router = useRouter();

const prevStep = () => {
  store.prevStep();
};

const submitForm = async () => {
  try {
    let response;
    if (store.formData.code) {
      response = await axios.put(`http://localhost:8000/api/adhesions/${store.formData.code}`, store.formData);
      alert(`Formulaire mis à jour !`);
      store.resetForm();
      router.push('/'); // Redirige vers la page d'accueil après la mise à jour
    } else {
      response = await axios.post('http://localhost:8000/api/adhesions', store.formData);
      store.resetForm(); // Réinitialise le formulaire mais garde le code
      store.lastGeneratedCode = response.data.code; // Stocke le code
      router.push('/confirmation'); // Redirige vers la page de confirmation
    }
  } catch (error) {
    console.error(error);
    alert('Une erreur est survenue lors de la validation du formulaire.');
  }
};
</script>
