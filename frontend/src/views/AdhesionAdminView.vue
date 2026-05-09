<script lang="ts" setup>
import {ref, onMounted, computed} from 'vue';
import {useRouter} from 'vue-router';
import {getAdhesions, deleteAdhesion, validateAdhesion, updateAdhesionPayment} from '../api';
import type {Adhesion, Activity} from '../types';
import { useConfirm } from 'primevue/useconfirm';
import PaymentModal from '../components/PaymentModal.vue';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Button from 'primevue/button';
import Tag from 'primevue/tag';
import InputText from 'primevue/inputtext';
import Select from 'primevue/select';
import Message from 'primevue/message';
import ConfirmDialog from 'primevue/confirmdialog';

const confirm = useConfirm();
const adhesions = ref<Adhesion[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const success = ref<string | null>(null);
const router = useRouter();
const selectedStatus = ref('all'); // 'all', 'pending', 'validated', 'paid'
const searchQuery = ref('');

const isPaymentModalVisible = ref(false);
const selectedAdhesionCode = ref<string | null>(null);

const backendUrl = window.BACKEND_URL || 'http://localhost:8000';

const statusOptions = [
  { label: 'Tous', value: 'all' },
  { label: 'En attente', value: 'pending' },
  { label: 'Validé', value: 'validated' },
  { label: 'Payé', value: 'paid' },
];

const fetchAdhesions = async () => {
  try {
    loading.value = true;
    adhesions.value = await getAdhesions();
  } catch (err) {
    error.value = 'Erreur lors de la récupération des adhésions.';
  } finally {
    loading.value = false;
  }
};

const calculateTotalCost = (adhesion: Adhesion): number => {
  const isResident = adhesion.ville.toLowerCase() === 'fauverney';
  const activitiesCost = adhesion.activities.reduce((total, activity) => {
    const price = isResident ? activity.resident_price : activity.external_price;
    return total + (price || 0);
  }, 0);
  return (adhesion.adhesion_amount || 0) + activitiesCost;
};

const adhesionsWithTotal = computed(() => {
  return adhesions.value.map(adhesion => ({
    ...adhesion,
    totalCost: calculateTotalCost(adhesion),
    fullName: `${adhesion.prenom} ${adhesion.nom}`,
    activitiesDisplay: adhesion.activities.map(a => a.name).join(', '),
  }));
});

const filteredAdhesions = computed(() => {
  let result = adhesionsWithTotal.value;
  if (selectedStatus.value !== 'all') {
    result = result.filter(adhesion => adhesion.status === selectedStatus.value);
  }
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    result = result.filter(adhesion =>
      adhesion.nom.toLowerCase().includes(query) ||
      adhesion.prenom.toLowerCase().includes(query) ||
      adhesion.email.toLowerCase().includes(query) ||
      adhesion.ville.toLowerCase().includes(query) ||
      adhesion.code.toLowerCase().includes(query)
    );
  }
  return result;
});

const getStatusSeverity = (status: string) => {
  switch (status) {
    case 'pending': return 'warn';
    case 'validated': return 'success';
    case 'paid': return 'info';
    default: return undefined;
  }
};

const getStatusLabel = (status: string) => {
  switch (status) {
    case 'pending': return 'En attente';
    case 'validated': return 'Validé';
    case 'paid': return 'Payé';
    default: return status;
  }
};

const exportToCSV = () => {
  const headers = [
    "Nom", "Prénom", "Email", "Téléphone", "Ville", "Code", "Statut",
    "Montant Adhésion", "Activités", "Coût Total"
  ];
  const rows = filteredAdhesions.value.map(adhesion => [
    adhesion.nom,
    adhesion.prenom,
    adhesion.email,
    adhesion.telephone || '',
    adhesion.ville,
    adhesion.code,
    adhesion.status,
    adhesion.adhesion_amount,
    adhesion.activities.map(a => a.name).join(', '),
    adhesion.totalCost.toFixed(2)
  ]);

  let csvContent = "data:text/csv;charset=utf-8,"
      + headers.join(",") + "\n"
      + rows.map(e => e.join(",")).join("\n");

  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", "adhesions_filtrees.csv");
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

const updateAdhesionInList = (code: string, updatedAdhesion: Adhesion) => {
  const index = adhesions.value.findIndex(a => a.code === code);
  if (index !== -1) {
    adhesions.value[index] = updatedAdhesion;
  }
};

const handleEdit = (code: string) => {
  router.push({name: 'adhesion', query: {code, source: 'admin'}});
};

const handleValidate = async (code: string) => {
  try {
    const updated = await validateAdhesion(code);
    updateAdhesionInList(code, updated);
    success.value = `L'adhésion ${code} a été validée.`;
  } catch (err) {
    error.value = `Erreur lors de la validation de l'adhésion ${code}.`;
  }
};

const openPaymentModal = (code: string) => {
  selectedAdhesionCode.value = code;
  isPaymentModalVisible.value = true;
};

const processPayment = async (paymentMethod: 'Chèque' | 'Virement') => {
  if (!selectedAdhesionCode.value) return;

  try {
    const updated = await updateAdhesionPayment(selectedAdhesionCode.value, paymentMethod);
    updateAdhesionInList(selectedAdhesionCode.value, updated);
    success.value = `L'adhésion ${selectedAdhesionCode.value} a été marquée comme payée.`;
  } catch (err) {
    error.value = `Erreur lors de la mise à jour du paiement pour l'adhésion ${selectedAdhesionCode.value}.`;
  } finally {
    isPaymentModalVisible.value = false;
    selectedAdhesionCode.value = null;
  }
};

const handleReceipt = (code: string) => {
  window.open(`${backendUrl}/api/adhesions/${code}/receipt`, '_blank');
};

const removeAdhesion = (code: string) => {
  confirm.require({
    message: 'Êtes-vous sûr de vouloir supprimer cette adhésion ?',
    header: 'Confirmation',
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: 'Supprimer',
    rejectLabel: 'Annuler',
    acceptClass: 'p-button-danger',
    accept: async () => {
      try {
        await deleteAdhesion(code);
        adhesions.value = adhesions.value.filter(adhesion => adhesion.code !== code);
        success.value = `L'adhésion ${code} a été supprimée.`;
      } catch (err) {
        error.value = "Erreur lors de la suppression de l'adhésion.";
      }
    },
  });
};

onMounted(fetchAdhesions);
</script>

<template>
  <div style="padding: 2rem;">
    <h1>Administration des Adhésions</h1>

    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; gap: 1rem;">
      <div style="display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap;">
        <InputText v-model="searchQuery" placeholder="Rechercher..." style="width: 250px;" />
        <Select v-model="selectedStatus" :options="statusOptions" optionLabel="label" optionValue="value" placeholder="Statut" style="width: 180px;" />
      </div>
      <Button label="Exporter CSV" icon="pi pi-download" @click="exportToCSV" />
    </div>

    <div v-if="loading" style="padding: 1rem;">Chargement...</div>
    <Message v-if="error" severity="error" :closable="true" @close="error = null">{{ error }}</Message>
    <Message v-if="success" severity="success" :closable="true" @close="success = null">{{ success }}</Message>

    <DataTable v-if="!loading" :value="filteredAdhesions" paginator :rows="20" stripedRows sortMode="multiple" removableSort>
      <Column field="fullName" header="Nom Complet" sortable />
      <Column field="email" header="Email" sortable style="max-width: 12rem; overflow: hidden; text-overflow: ellipsis;" />
      <Column field="telephone" header="Téléphone" sortable />
      <Column field="ville" header="Ville" sortable />
      <Column field="adhesion_amount" header="Adhésion" sortable>
        <template #body="{ data }">{{ data.adhesion_amount }} €</template>
      </Column>
      <Column field="activitiesDisplay" header="Activités">
        <template #body="{ data }">
          <ul style="list-style-type: none; padding: 0; margin: 0;">
            <li v-for="activity in data.activities" :key="`${data.code}-${activity.id}`">{{ activity.name }}</li>
          </ul>
        </template>
      </Column>
      <Column field="totalCost" header="Coût Total" sortable>
        <template #body="{ data }">{{ data.totalCost.toFixed(0) }} €</template>
      </Column>
      <Column field="status" header="Statut" sortable>
        <template #body="{ data }">
          <Tag :value="getStatusLabel(data.status)" :severity="getStatusSeverity(data.status)" />
        </template>
      </Column>
      <Column header="Actions" style="min-width: 12rem;">
        <template #body="{ data }">
          <Button icon="pi pi-eye" severity="secondary" text rounded size="small" title="Voir" @click="router.push({ name: 'admin-adhesion-detail', params: { code: data.code } })" />
          <Button v-if="data.status !== 'paid'" icon="pi pi-pencil" severity="info" text rounded size="small" title="Corriger" @click="handleEdit(data.code)" />
          <Button v-if="data.status === 'pending'" icon="pi pi-check" severity="success" text rounded size="small" title="Valider" @click="handleValidate(data.code)" />
          <Button v-if="data.status === 'pending' || data.status === 'validated'" icon="pi pi-euro" severity="warn" text rounded size="small" title="Payer" @click="openPaymentModal(data.code)" />
          <Button v-if="data.status === 'paid'" icon="pi pi-file" severity="secondary" text rounded size="small" title="Reçu" @click="handleReceipt(data.code)" />
          <Button icon="pi pi-trash" severity="danger" text rounded size="small" title="Supprimer" @click="removeAdhesion(data.code)" />
        </template>
      </Column>
    </DataTable>

    <PaymentModal
        :visible="isPaymentModalVisible"
        @close="isPaymentModalVisible = false"
        @pay="processPayment"
    />
    <ConfirmDialog />
  </div>
</template>
