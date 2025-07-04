<template>
  <div>
    <h2>Étape 4: Résumé</h2>
    <div>
      <p><strong>Email:</strong> {{ formData.email }}</p>
      <p><strong>Adhérant:</strong> {{ formData.prenom }} {{ formData.nom }}</p>
      <p><strong>Date de Naissance:</strong> {{ formattedDateNaissance }}</p>
      <p><strong>Adresse:</strong> {{ formData.numero_rue }}, {{ formData.nom_rue }} - {{ formData.code_postal }} {{ formData.ville }}</p>
      <p><strong>Montant Adhésion:</strong> {{ formData.adhesion_amount }}€</p>
      <p><strong>Activités sélectionnées:</strong></p>
      <ul>
        <li v-for="activity in selectedActivitiesDetails" :key="activity.id">
          {{ activity.name }} - {{ getPrice(activity) }}€
        </li>
      </ul>
      <p><strong>Coût total:</strong> {{ totalCost }}€</p>
    </div>
    <button @click="prevStep">Précédent</button>
    <button @click="submitForm">Valider</button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useFormStore } from '@/stores/form';
import api from '@/api';
import { useRouter } from 'vue-router';

const store = useFormStore();
const formData = store.formData;
const router = useRouter();

const allActivities = ref([]);

onMounted(async () => {
  try {
    const response = await api.get('/api/activities');
    allActivities.value = response.data;
  } catch (error) {
    console.error("Erreur lors du chargement des activités:", error);
  }
});

const selectedActivitiesDetails = computed(() => {
  return allActivities.value.filter(activity => formData.activites.includes(activity.name));
});

const getPrice = (activity) => {
  if (formData.ville && formData.ville.toLowerCase() === 'fauverney') {
    return activity.resident_price;
  } else {
    return activity.external_price;
  }
};

const formattedDateNaissance = computed(() => {
  if (!formData.date_naissance) return '';
  const date = new Date(formData.date_naissance);
  return date.toLocaleDateString('fr-FR');
});

const totalCost = computed(() => {
  const activitiesTotal = selectedActivitiesDetails.value.reduce((sum, activity) => {
    return sum + (getPrice(activity) || 0);
  }, 0);
  return activitiesTotal + (formData.adhesion_amount || 0);
});

const prevStep = () => {
  store.prevStep();
};

const submitForm = async () => {
  if (store.formData.status === 'validated') {
    alert('Ce formulaire a déjà été validé et ne peut plus être modifié.');
    return;
  }
  try {
    let response;
    if (store.formData.code) {
      response = await api.put(`/api/adhesions/${store.formData.code}`, store.formData);
      alert(`Formulaire mis à jour !`);
      store.resetForm();
      router.push('/'); // Redirige vers la page d'accueil après la mise à jour
    } else {
      response = await api.post('/api/adhesions', store.formData);
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
