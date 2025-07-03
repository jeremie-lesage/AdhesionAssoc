<template>
  <div>
    <h2>Étape 3: Choix des Activités</h2>
    <p v-if="adherentAge !== null">
      Affichage des activités pour {{ adherentAge < 16 ? 'enfants' : 'adultes' }}.
    </p>
    <p v-if="formData.ville">
      Tarif appliqué: {{ formData.ville.toLowerCase() === 'fauverney' ? 'résident' : 'extérieur' }}.
    </p>
    <h3>Liste des activités proposées</h3>
    <p v-if="loadingActivities">Chargement des activités...</p>
    <p v-if="activitiesError">Erreur lors du chargement des activités: {{ activitiesError }}</p>
    <form @submit.prevent="nextStep" v-if="!loadingActivities && !activitiesError">
      <div v-for="activity in filteredActivities" :key="activity.id">
        <label>
          <input type="checkbox" :value="activity.name" v-model="formData.activites">
          {{ activity.name }} <span v-if="activity.description">- {{ activity.description }}</span>
          <span v-if="getPrice(activity) !== null"> (Tarif: {{ getPrice(activity) }}€)</span>
          <span v-if="activity.location"> (Lieu: {{ activity.location }})</span>
          <span v-if="activity.is_child_activity"> (Enfant)</span>
          <span v-if="activity.is_adult_activity"> (Adulte)</span>
        </label>
      </div>
      <button @click="prevStep">Précédent</button>
      <button type="submit">Suivant</button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useFormStore } from '@/stores/form';
import axios from 'axios';

const store = useFormStore();
const formData = store.formData;

const allActivities = ref([]);
const loadingActivities = ref(true);
const activitiesError = ref(null);

const adherentAge = computed(() => {
  if (!formData.date_naissance) return null;
  const birthDate = new Date(formData.date_naissance);
  const today = new Date();
  let age = today.getFullYear() - birthDate.getFullYear();
  const m = today.getMonth() - birthDate.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
    age--;
  }
  return age;
});

const filteredActivities = computed(() => {
  if (adherentAge.value === null) return [];

  if (adherentAge.value < 16) {
    return allActivities.value.filter(activity => activity.is_child_activity);
  } else {
    return allActivities.value.filter(activity => activity.is_adult_activity);
  }
});

onMounted(async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/activities');
    allActivities.value = response.data;
  } catch (err) {
    activitiesError.value = err.message;
  } finally {
    loadingActivities.value = false;
  }
});

if (!formData.activites) {
  formData.activites = [];
}

const nextStep = () => {
  store.nextStep();
};

const prevStep = () => {
  store.prevStep();
};

const getPrice = (activity) => {
  if (formData.ville && formData.ville.toLowerCase() === 'fauverney') {
    return activity.resident_price;
  } else {
    return activity.external_price;
  }
};
</script>
