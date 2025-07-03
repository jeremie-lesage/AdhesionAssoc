<template>
  <div>
    <h2>Étape 3: Choix des Activités</h2>
    <p v-if="loadingActivities">Chargement des activités...</p>
    <p v-if="activitiesError">Erreur lors du chargement des activités: {{ activitiesError }}</p>
    <form @submit.prevent="nextStep" v-if="!loadingActivities && !activitiesError">
      <div v-for="activity in availableActivities" :key="activity.id">
        <label>
          <input type="checkbox" :value="activity.name" v-model="formData.activites">
          {{ activity.name }} <span v-if="activity.description">- {{ activity.description }}</span>
          <span v-if="activity.resident_price"> (Résident: {{ activity.resident_price }}€)</span>
          <span v-if="activity.external_price"> (Extérieur: {{ activity.external_price }}€)</span>
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
import { ref, onMounted } from 'vue';
import { useFormStore } from '@/stores/form';
import axios from 'axios';

const store = useFormStore();
const formData = store.formData;

const availableActivities = ref([]);
const loadingActivities = ref(true);
const activitiesError = ref(null);

onMounted(async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/activities');
    availableActivities.value = response.data;
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
</script>
