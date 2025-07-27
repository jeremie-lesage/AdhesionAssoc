<template>
  <div>
    <h2>Finalisation</h2>
    <div class="summary-container">
      <div class="summary-section">
        <h3>Résumé</h3>

        <p><strong>Email:</strong> {{ formData.email }}</p>
        <p><strong>Adhérant:</strong> {{ formData.prenom }} {{ formData.nom }}</p>
        <p><strong>Date de Naissance:</strong> {{ formattedDateNaissance }}</p>
        <p><strong>Adresse:</strong> {{ formData.numero_rue }}, {{ formData.nom_rue }} - {{ formData.code_postal }}
          {{ formData.ville }}</p>
        <p><strong>Montant Adhésion:</strong> {{ formData.adhesion_amount }}€</p>
        <p><strong>Activités sélectionnées:</strong></p>
        <ul>
          <li v-for="activity in selectedActivitiesDetails" :key="activity.id!">
            {{ activity.name }} - {{ getPrice(activity) }}€
          </li>
        </ul>
        <p><strong>Coût total:</strong> {{ totalCost }}€</p>
      </div>
      <div class="payment-section">
        <h3>Moyens de Paiements</h3>
        <h4>Par chèque</h4>
        <ul style="padding-left: 1rem;">
          <li>Soit 1 chèque de {{ totalCost }} € (Encaissement en Octobre)</li>
          <li>Soit 2 chèques de  {{ totalCost /2 }} € (Encaissement en Octobre et Février)</li>
        </ul>
        <h4>Par virement</h4>
        <pre>{{ bank }}</pre>
        <pre>IBAN: {{ iban }}</pre>
        <pre>BIC: {{ bic }}</pre>
        <b>Pensez à mettre le nom de l'adhérant dans l'objet du virement.</b>
      </div>
    </div>

    <button @click="prevStep">Précédent</button>
    <button @click="submitForm">Valider</button>

    <ConfirmationModal :visible="isModalVisible" :form-id="formIdToDisplay" @close="handleModalClose" />
  </div>

</template>

<script lang="ts" setup>
import {ref, computed, onMounted} from 'vue';
import {useFormStore} from '@/stores/form';
import api from '@/api';
import {useRouter} from 'vue-router';
import type {Activity} from '@/types';
import ConfirmationModal from '../ConfirmationModal.vue';

const store = useFormStore();
const formData = store.formData;
const router = useRouter();

const allActivities = ref<Activity[]>([]);
const isModalVisible = ref(false);
const isUpdate = ref(false);
const iban = ref('');
const bic = ref('');
const bank = ref('');

onMounted(async () => {
  try {
    const activitiesResponse = await api.get('/api/activities');
    allActivities.value = activitiesResponse.data;

    const configResponse = await api.get('/api/config');
    iban.value = configResponse.data.iban;
    bic.value = configResponse.data.bic;
    bank.value = configResponse.data.bank;
  } catch (error) {
    console.error("Erreur lors du chargement des données:", error);
  }
});

const formIdToDisplay = computed(() => {
  return store.formData.code || store.lastGeneratedCode || '';
});

const selectedActivitiesDetails = computed<Activity[]>(() => {
  return formData.activities;
});

const getPrice = (activity: Activity) => {
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

  const { adhesion_selected, ...restOfFormData } = store.formData;
  const payload = {
    ...restOfFormData,
    activities: store.formData.activities.map(activity => activity.id)
  };

  try {
    if (store.formData.code) {
      await api.put(`/api/adhesions/${store.formData.code}`, payload);
      isUpdate.value = true;
    } else {
      const response = await api.post('/api/adhesions', payload);
      const newCode = response.data.code;
      const recentCodes = JSON.parse(localStorage.getItem('recentCodes') || '[]');
      recentCodes.unshift(newCode);
      if (recentCodes.length > 5) {
        recentCodes.pop();
      }
      localStorage.setItem('recentCodes', JSON.stringify(recentCodes));
      store.lastGeneratedCode = newCode;
    }
    isModalVisible.value = true;
  } catch (error) {
    console.error(error);
    alert('Une erreur est survenue lors de la validation du formulaire.');
  }
};

const handleModalClose = () => {
  isModalVisible.value = false;
  store.resetForm();
  if (isUpdate.value) {
    router.push('/');
  } else {
    router.push('/confirmation');
  }
};
</script>

<style scoped>
.summary-container {
  display: flex;
  gap: 2rem;
  margin-bottom: 1rem;
}

.summary-section, .payment-section {
  flex: 1;
}


@media (max-width: 768px) {
  .summary-container {
    flex-direction: column;
  }
}

</style>
