<template>
  <div>
    <h2>Finalisation</h2>
    <div class="summary-container">
      <div class="summary-section">
        <h3>Résumé</h3>

        <p><strong>Email:</strong> {{ formData.email }}</p>
        <p><strong>Adhérent:</strong> {{ formData.prenom }} {{ formData.nom }}</p>
        <p><strong>Date de Naissance:</strong> {{ formattedDateNaissance }}</p>
        <p><strong>Adresse:</strong> {{ formData.nom_rue }} - {{ formData.code_postal }}
          {{ formData.ville }}</p>
        <p><strong>Montant Adhésion:</strong> {{ formData.adhesion_amount }}€</p>
        <p><strong>Activités sélectionnées:</strong></p>
        <ul>
          <li v-for="activity in selectedActivitiesDetails" :key="activity.id!">
            {{ activity.name }} - {{ getPrice(activity) }}€
          </li>
        </ul>
        <p><strong>Coût total:</strong> {{ totalCost }}€</p>
        <div v-if="documentsRequired.length" class="documents-notice">
          <strong>Documents à imprimer et signer</strong>
          <p>
            Merci de les remplir et de les remettre au responsable de l'activité lors
            de la première séance.
          </p>
          <ul>
            <li v-for="activity in documentsRequired" :key="activity.id!">
              <a :href="documentUrl(activity)" target="_blank">{{ activity.name }}</a>
            </li>
          </ul>
        </div>
      </div>
      <div class="payment-section">
        <h3>Moyens de paiement</h3>
        <h4>Par chèque</h4>
        <ul style="padding-left: 1rem;">
          <li>Soit 1 chèque de {{ totalCost }} € (Encaissement en Octobre)</li>
          <li>Soit 2 chèques de  {{ totalCost /2 }} € (Encaissement en Octobre et Février)</li>
        </ul>
        <h4>Par virement</h4>
        <pre>{{ bank }}</pre>
        <pre>IBAN: {{ iban }}</pre>
        <pre>BIC: {{ bic }}</pre>
        <b>Pensez à mettre le nom de l'adhérent dans l'objet du virement.</b>
      </div>
    </div>

    <button @click="prevStep">Précédent</button>
    <button @click="submitForm">Valider</button>

    <ConfirmationModal :visible="isModalVisible" :form-id="formIdToDisplay"
                       :documents="documentsRequired" @close="handleModalClose" />

    <MessageModal
      :message="errorModal.message"
      :title="errorModal.title"
      :variant="errorModal.variant"
      :visible="errorModal.visible"
      @close="errorModal.visible = false"
    />
  </div>

</template>

<script lang="ts" setup>
import {ref, computed, onMounted} from 'vue';
import {useFormStore} from '@/stores/form';
import api from '@/api';
import {useRouter} from 'vue-router';
import type {Activity} from '@/types';
import { activitiesCost, activityPrice } from '@/pricing';
import { documentUrl, documentsToSign } from '@/documents';
import { rememberCode } from '@/family';
import ConfirmationModal from '../ConfirmationModal.vue';
import MessageModal from '../MessageModal.vue';

const store = useFormStore();
const formData = store.formData;
const router = useRouter();

const allActivities = ref<Activity[]>([]);
const isModalVisible = ref(false);

const errorModal = ref<{
  visible: boolean;
  title: string;
  message: string;
  variant: 'info' | 'warning' | 'error';
}>({ visible: false, title: '', message: '', variant: 'error' });

const showError = (title: string, message: string, variant: 'warning' | 'error' = 'error') => {
  errorModal.value = { visible: true, title, message, variant };
};
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

// Encore renseigné quand la modale s'affiche : `store.resetForm()` n'a lieu qu'à
// sa fermeture, ce qui permet de lui passer la liste en propriété.
const documentsRequired = computed<Activity[]>(() =>
  documentsToSign(selectedActivitiesDetails.value)
);

const getPrice = (activity: Activity) => activityPrice(activity, formData.ville);

const formattedDateNaissance = computed(() => {
  if (!formData.date_naissance) return '';
  const date = new Date(formData.date_naissance);
  return date.toLocaleDateString('fr-FR');
});

const totalCost = computed(() => {
  return activitiesCost(selectedActivitiesDetails.value, formData.ville) + (formData.adhesion_amount || 0);
});

const prevStep = () => {
  store.prevStep();
};

const submitForm = async () => {
  if (store.formData.status === 'validated') {
    showError(
      'Inscription déjà validée',
      'Ce formulaire a déjà été validé et ne peut plus être modifié.\n'
        + 'Pour toute correction, contactez un responsable du Foyer Rural.',
      'warning'
    );
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
    } else {
      const response = await api.post('/api/adhesions', payload);
      const newCode = response.data.code;
      rememberCode(newCode);
      store.lastGeneratedCode = newCode;
    }
    isModalVisible.value = true;
  } catch (error) {
    console.error(error);
    showError(
      'Envoi impossible',
      "Une erreur est survenue lors de la validation du formulaire.\n"
        + 'Vos réponses sont conservées : réessayez dans un instant.'
    );
  }
};

// La modale de confirmation porte déjà le code d'accès et les documents à signer :
// retour direct à l'accueil, création comme modification.
const handleModalClose = () => {
  isModalVisible.value = false;
  store.resetForm();
  router.push('/');
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

.documents-notice {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  border-left: 4px solid #b9770e;
  background-color: #fdf6e3;
}

.documents-notice p {
  margin: 0.5rem 0;
  font-size: 0.9rem;
}


@media (max-width: 768px) {
  .summary-container {
    flex-direction: column;
  }
}

</style>
