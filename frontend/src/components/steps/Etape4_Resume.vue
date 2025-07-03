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

const store = useFormStore();
const formData = store.formData;

const prevStep = () => {
  store.prevStep();
};

const submitForm = async () => {
  try {
    const response = await axios.post('http://localhost:8000/api/adhesions', formData);
    alert(`Formulaire validé ! Votre code d\'accès est : ${response.data.code}`);
    store.resetForm();
  } catch (error) {
    console.error(error);
    alert('Une erreur est survenue lors de la validation du formulaire.');
  }
};
</script>
