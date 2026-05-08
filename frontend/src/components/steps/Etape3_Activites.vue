<template>
  <div>
    <h2>Étape 3: Choix des Activités</h2>
    <p>
      Affichage des activités pour {{ adherentAge < 16 ? 'enfants' : 'adultes' }}.
    </p>
    <p v-if="formData.ville">
      Tarif appliqué: {{ formData.ville.toLowerCase() === 'fauverney' ? 'résident' : 'extérieur' }}.
    </p>
    <p v-if="loadingActivities">Chargement des activités...</p>
    <p v-if="activitiesError">Erreur lors du chargement des activités: {{ activitiesError }}</p>
    <form v-if="!loadingActivities && !activitiesError" @submit.prevent="nextStep">
      <h3>Adhésion Obligatoire</h3>
      <div class="adhesion-section">
        <label>
          Montant de l'adhésion:
        </label>
        <div>
          <template v-if="adherentAge >= 16">
            <label>
              <input v-model="formData.adhesion_amount" :value="12" name="adult_adhesion_amount" type="radio"> 12€
            </label>
          </template>
          <template v-else>
            <label>
              <input v-model="formData.adhesion_amount" :value="8" name="first_child_adhesion_amount" type="radio"> 8€
              (Premier enfant)
            </label>
            <label>
              <input v-model="formData.adhesion_amount" :value="6" name="child_adhesion_amount" type="radio"> 6€
              (Deuxième enfant et suivants)
            </label>
          </template>
        </div>
      </div>

      <h3>Liste des activités proposées</h3>
      <p v-if="adherentAge < 16">Détails des activités sur <a
          href="https://foyerruralfauverney.fr/activites/activites-enfant/" target="_blank">notre site internet</a></p>
      <p v-else> Détails des activités sur <a href="https://foyerruralfauverney.fr/activites/activites-adulte/"
                                              target="_blank">notre site internet</a></p>
      <div v-for="activity in filteredActivities" :key="activity.id!">
        <label
            :class="{ 'disabled-activity': isActivityUnavailable(activity) }">

          <div class="activity-info">
            <input v-model="selectedActivityIds"
                   :disabled="isActivityUnavailable(activity)"
                   :value="activity.id"
                   type="checkbox"> {{ activity.name }} <span
              v-if="activity.description">- {{ activity.description }}</span></div>
          <span v-if="getPrice(activity) !== null" style="font-weight: bold"> Tarif: {{ getPrice(activity) }}€</span>
          <br/>
          <div v-if="activity.location" class="activity-location">
            {{ activity.location }}
          </div>
          <span v-if="activity.max_participants > 0"> (Places restantes: {{
              activity.max_participants - (activity.current_participants || 0)
            }})
          </span>
          <span v-if="activity.max_participants > 0 && activity.current_participants >= activity.max_participants"
                style="color: red;"> (Complet)</span>
          <span v-else-if="isDeadlinePassed(activity)"
                style="color: red;"> (Inscriptions closes)</span>
          <span v-if="activity.registration_deadline && !isDeadlinePassed(activity)"
                style="color: #666;"> (Inscription avant le {{ formatDate(activity.registration_deadline) }})</span>
        </label>
      </div>
      <button @click="prevStep">Précédent</button>
      <button type="submit">Suivant</button>
    </form>
  </div>
</template>

<script lang="ts" setup>
import {ref, onMounted, computed, watch} from 'vue';
import {useFormStore} from '@/stores/form';
import api from '@/api';
import type {Activity} from '@/types';

const store = useFormStore();
const formData = store.formData;

const allActivities = ref<Activity[]>([]);
const loadingActivities = ref(true);
const activitiesError = ref<string | null>(null);
const selectedActivityIds = ref<number[]>([]);

const adherentAge = computed<number>(() => {
  if (!formData.date_naissance) return 0;
  const birthDate = new Date(formData.date_naissance);
  const today = new Date();
  let age = today.getFullYear() - birthDate.getFullYear();
  const m = today.getMonth() - birthDate.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
    age--;
  }
  return age;
});

// Set initial adhesion amount for children if not already set
watch(adherentAge, (newAge) => {
  if (newAge !== null && newAge < 16 && formData.adhesion_amount === null) {
    formData.adhesion_amount = 8; // Default to 8€ for first child
  }
}, {immediate: true});

const filteredActivities = computed<Activity[]>(() => {
  if (adherentAge.value === null) return [];

  if (adherentAge.value < 16) {
    return allActivities.value.filter((activity: Activity) => activity.is_child_activity);
  } else {
    return allActivities.value.filter((activity: Activity) => activity.is_adult_activity);
  }
});

onMounted(async () => {
  try {
    loadingActivities.value = true;
    const response = await api.get('/api/activities');
    allActivities.value = response.data;

    // Now that allActivities is available, initialize selectedActivityIds
    if (formData.activities && Array.isArray(formData.activities)) {
      selectedActivityIds.value = formData.activities.map(activity => activity.id).filter(id => id !== null) as number[];
    }
  } catch (err: any) {
    activitiesError.value = err.message;
  } finally {
    loadingActivities.value = false;
  }
});

const updateStore = () => {
  formData.activities = allActivities.value.filter(activity => selectedActivityIds.value.includes(activity.id!));
}

const nextStep = () => {
  if (!formData.adhesion_amount) {
    alert("L'adhésion est obligatoire pour toute inscription.");
    return;
  }
  updateStore(); // Commit changes to the store
  store.nextStep();
};

const prevStep = () => {
  updateStore(); // Commit changes to the store
  store.prevStep();
};

const isDeadlinePassed = (activity: Activity): boolean => {
  if (!activity.registration_deadline) return false;
  return new Date(activity.registration_deadline) < new Date(new Date().toDateString());
};

const isActivityUnavailable = (activity: Activity): boolean => {
  if (activity.max_participants > 0 && activity.current_participants >= activity.max_participants) return true;
  return isDeadlinePassed(activity);
};

const formatDate = (dateStr: string): string => {
  return new Date(dateStr).toLocaleDateString('fr-FR');
};

const getPrice = (activity: Activity) => {
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

.activity-info {
  width: 75%;
  display: inline-block;
}

.activity-location {
  width: 72%;
  display: inline-block;
  padding-left: 1.5rem
}


@media (max-width: 768px) {
  .activity-info {
    width: 100%;
    display: inline-block;
    padding: 0;
    margin: 0;
  }

  .activity-location {
    width: 100%;
    display: inline-block;
    padding: 0;
    margin: 0;
  }
}

</style>