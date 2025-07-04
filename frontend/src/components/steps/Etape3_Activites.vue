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
      <h3>Adhésion</h3>
      <div class="adhesion-section">
        <label>
          Montant de l'adhésion:
        </label>
        <div >
          <template v-if="adherentAge >= 16">
          <label >
            <input type="radio" v-model="formData.adhesion_amount" :value="12" name="adult_adhesion_amount"> 12€
          </label>
          </template>
          <template v-else>
          <label>
            <input type="radio" v-model="formData.adhesion_amount" :value="8" name="first_child_adhesion_amount"> 8€ (Premier enfant)
          </label>
          <label>
            <input type="radio" v-model="formData.adhesion_amount" :value="6" name="child_adhesion_amount"> 6€ (Deuxième enfant et suivants)
          </label>
          </template>
        </div>
      </div>

      <h3>Liste des activités proposées</h3>
      <div v-for="activity in filteredActivities" :key="activity.id">
        <label :class="{ 'disabled-activity': activity.max_participants > 0 && activity.current_participants >= activity.max_participants }">
          <input type="checkbox" :value="activity.name" v-model="formData.activites" :disabled="activity.max_participants > 0 && activity.current_participants >= activity.max_participants">
          {{ activity.name }} <span v-if="activity.description">- {{ activity.description }}</span>
          <span v-if="getPrice(activity) !== null"> (Tarif: {{ getPrice(activity) }}€)</span>
          <span v-if="activity.location"> (Lieu: {{ activity.location }})</span>
          <span v-if="activity.max_participants > 0"> (Places restantes: {{ activity.max_participants - activity.current_participants }})</span>
          <span v-if="activity.max_participants > 0 && activity.current_participants >= activity.max_participants" style="color: red;"> (Complet)</span>
        </label>
      </div>
      <button @click="prevStep">Précédent</button>
      <button type="submit">Suivant</button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
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

const adhesionCost = computed(() => {
  if (adherentAge.value === null) return 0;

  if (adherentAge.value >= 16) {
    return 12; // Adult
  } else {
    // For children, the actual cost will be set by the radio buttons
    return formData.adhesion_amount || 0; 
  }
});

// Set initial adhesion amount for children if not already set
watch(adherentAge, (newAge) => {
  if (newAge !== null && newAge < 16 && formData.adhesion_amount === null) {
    formData.adhesion_amount = 8; // Default to 8€ for first child
  }
}, { immediate: true });

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
  if (!formData.adhesion_amount) {
    alert("L'adhésion est obligatoire pour toute inscription.");
    return;
  }
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

<style scoped>
.disabled-activity {
  color: #999;
  cursor: not-allowed;
}

.disabled-activity input[type="checkbox"] {
  cursor: not-allowed;
}
</style>