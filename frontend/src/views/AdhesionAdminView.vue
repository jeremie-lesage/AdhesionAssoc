<script lang="ts" setup>
import {ref, onMounted, computed} from 'vue';
import {useRouter} from 'vue-router';
import {getAdhesions, deleteAdhesion, validateAdhesion, updateAdhesionPayment} from '../api';
import type {Adhesion, Activity} from '../types';
import PaymentModal from '../components/PaymentModal.vue';

const adhesions = ref<Adhesion[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const success = ref<string | null>(null);
const router = useRouter();
const selectedStatus = ref('all'); // 'all', 'pending', 'validated', 'paid'

const isPaymentModalVisible = ref(false);
const selectedAdhesionCode = ref<string | null>(null);

const backendUrl = window.BACKEND_URL || 'http://localhost:8000';

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
  }));
});

const filteredAdhesions = computed(() => {
  if (selectedStatus.value === 'all') {
    return adhesionsWithTotal.value;
  }
  return adhesionsWithTotal.value.filter(adhesion => adhesion.status === selectedStatus.value);
});

const exportToCSV = () => {
  const headers = [
    "Nom", "Prénom", "Email", "Ville", "Code", "Statut",
    "Montant Adhésion", "Activités", "Coût Total"
  ];
  const rows = filteredAdhesions.value.map(adhesion => [
    adhesion.nom,
    adhesion.prenom,
    adhesion.email,
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

const removeAdhesion = async (code: string) => {
  if (window.confirm("Êtes-vous sûr de vouloir supprimer cette adhésion ?")) {
    try {
      await deleteAdhesion(code);
      adhesions.value = adhesions.value.filter(adhesion => adhesion.code !== code);
      success.value = `L'adhésion ${code} a été supprimée.`;
    } catch (err) {
      error.value = "Erreur lors de la suppression de l'adhésion.";
    }
  }
};

onMounted(fetchAdhesions);
</script>

<template>
  <div class="admin-container">
    <h1>Administration des Adhésions</h1>

    <div class="top-bar">
      <div class="filters">
        <button :class="{ active: selectedStatus === 'all' }" @click="selectedStatus = 'all'">Tous</button>
        <button :class="{ active: selectedStatus === 'pending' }" @click="selectedStatus = 'pending'">En attente
        </button>
        <button :class="{ active: selectedStatus === 'validated' }" @click="selectedStatus = 'validated'">Validé
        </button>
        <button :class="{ active: selectedStatus === 'paid' }" @click="selectedStatus = 'paid'">Payé</button>
      </div>
      <button class="export-button" @click="exportToCSV">Exporter en CSV</button>
    </div>

    <div v-if="loading">Chargement...</div>
    <div v-if="error" class="error-message" @click="error = null">{{ error }}</div>
    <div v-if="success" class="success-message" @click="success = null">{{ success }}</div>
    <div v-if="!loading && !error" class="table-container">
      <table class="adhesions-table">
        <thead>
        <tr>
          <th>Nom Complet</th>
          <th>Email</th>
          <th>Ville</th>
          <th>Adhésion</th>
          <th>Activités</th>
          <th>Coût Total</th>
          <th>Status</th>
          <th>Actions</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="adhesion in filteredAdhesions" :key="adhesion.code">
          <td>{{ adhesion.prenom }} {{ adhesion.nom }}</td>
          <td :title="adhesion.email" style="max-width: 3rem; text-overflow: ellipsis; overflow: hidden">
            {{ adhesion.email }}
          </td>
          <td>{{ adhesion.ville }}</td>
          <td>{{ adhesion.adhesion_amount }} €</td>
          <td>
            <ul style="list-style-type: none; padding: 0">
              <li v-for="activity in adhesion.activities" :key="`${adhesion.code}-${activity.id}`">{{
                  activity.name
                }}
              </li>
            </ul>
          </td>
          <td>{{ adhesion.totalCost.toFixed(0) }} €</td>
          <td>
            <span :class="`status status-${adhesion.status}`">{{ adhesion.status }}</span>
          </td>
          <td class="actions">
            <button v-if="adhesion.status !== 'paid'" class="action-button" title="Corriger"
                    @click="handleEdit(adhesion.code)">✏️
            </button>
            <button v-if="adhesion.status === 'pending'" class="action-button" title="Valider"
                    @click="handleValidate(adhesion.code)">✔️
            </button>
            <button v-if="adhesion.status === 'pending' || adhesion.status === 'validated'"
                    class="action-button" title="Payer" @click="openPaymentModal(adhesion.code)">💶
            </button>
            <button v-if="adhesion.status === 'paid'" class="action-button" title="Reçu"
                    @click="handleReceipt(adhesion.code)">🧾
            </button>
            <button class="action-button" title="Supprimer" @click="removeAdhesion(adhesion.code)">🗑️</button>


          </td>
        </tr>
        </tbody>
      </table>
    </div>
    <PaymentModal
        :visible="isPaymentModalVisible"
        @close="isPaymentModalVisible = false"
        @pay="processPayment"
    />
  </div>
</template>

<style scoped>
.admin-container {
  padding: 2rem;
  max-width: 100%;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.filters {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.filters button {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  background-color: #f9f9f9;
  cursor: pointer;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.filters button.active {
  background-color: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.export-button {
  padding: 0.5rem 1rem;
  border: 1px solid var(--color-primary);
  background-color: var(--color-primary);
  color: white;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.export-button:hover {
  background-color: var(--color-hover);
}

.table-container {
  overflow-x: auto;
}

.error-message, .success-message {
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
  cursor: pointer;
}

.error-message {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.success-message {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.adhesions-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
  font-size: 0.9rem;
}

.adhesions-table th,
.adhesions-table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
  vertical-align: middle;
}

.adhesions-table th {
  background-color: #f4f4f4;
}

.adhesions-table ul {
  margin: 0;
  padding-left: 1.2rem;
}

.status {
  margin: 0.5rem;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-weight: bold;
  color: white;
  text-transform: capitalize;
  white-space: nowrap;
}

.status-pending {
  background-color: #ffc107;
}

.status-validated {
  background-color: #28a745;
}

.status-paid {
  background-color: #007bff;
}

.actions {
  display: flex;
  flex-wrap: wrap;
}

.action-button {
  background: none;
  border: 1px solid var(--color-border);
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0.6rem;
  margin: 0.1rem;
  transition: transform 0.2s;
}

.action-button:hover {
  transform: scale(1.2);
}
</style>
