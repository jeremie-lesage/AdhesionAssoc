<template>
  <div>
    <h2>Adhérents par Activité</h2>
    <Button label="Retour à l'Administration" icon="pi pi-arrow-left" severity="secondary" as="router-link" to="/admin" />

    <div style="display: flex; align-items: center; gap: 1rem; margin: 1.5rem 0;">
      <label for="activity-select">Sélectionner une activité:</label>
      <Select
        id="activity-select"
        v-model="selectedActivityId"
        :options="activities"
        optionLabel="name"
        optionValue="id"
        placeholder="Choisir une activité"
        fluid
        @change="fetchAdherentsForActivity"
      />
    </div>

    <p v-if="loading">Chargement des adhérents...</p>
    <p v-if="error">Erreur: {{ error }}</p>

    <div v-if="selectedActivityId && !loading && !error">
      <h3>Adhérents pour l'activité: {{ selectedActivityName }}</h3>
      <p>Nombre total d'adhérents: {{ adherents.length }}</p>
      <Button label="Exporter en CSV" icon="pi pi-download" severity="success" :disabled="!adherents.length" @click="exportToCsv" style="margin-bottom: 1rem;" />

      <DataTable v-if="adherents.length" :value="adherents" stripedRows>
        <Column field="nom" header="Nom" sortable />
        <Column field="prenom" header="Prénom" sortable />
        <Column field="email" header="Email" sortable />
        <Column field="status" header="Statut" sortable />
      </DataTable>
      <p v-else>Aucun adhérent pour cette activité.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import api from '@/api';
import { useRouter } from 'vue-router';
import type { Activity, Adhesion } from '@/types';
import Button from 'primevue/button';
import Select from 'primevue/select';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';

const activities = ref<Activity[]>([]);
const selectedActivityId = ref<number | string>('');
const adherents = ref<Adhesion[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const router = useRouter();

const selectedActivityName = computed(() => {
  const activity = activities.value.find((act: Activity) => act.id === selectedActivityId.value);
  return activity ? activity.name : '';
});

const fetchActivities = async () => {
  try {
    const response = await api.get('/api/activities');
    activities.value = response.data;
  } catch (err: any) {
    if (err.response && err.response.status === 401) {
      await router.push({name: 'admin-login'});
    } else {
      error.value = err.message;
    }
  }
};

const fetchAdherentsForActivity = async () => {
  if (!selectedActivityId.value) {
    adherents.value = [];
    return;
  }
  loading.value = true;
  error.value = null;
  try {
    const response = await api.get(`/api/activities/${selectedActivityId.value}/adherents`);
    adherents.value = response.data;
  } catch (err: any) {
    if (err.response && err.response.status === 401) {
      router.push({ name: 'admin-login' });
    } else {
      error.value = err.message;
    }
  } finally {
    loading.value = false;
  }
};

const exportToCsv = () => {
  if (!adherents.value.length) return;

  const headers = ["Nom", "Prénom", "Email", "Statut"];
  const rows = adherents.value.map(adherent => [
    adherent.nom,
    adherent.prenom,
    adherent.email,
    adherent.status
  ]);

  let csvContent = headers.join(";") + "\n";
  rows.forEach(row => {
    csvContent += row.join(";") + "\n";
  });

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.setAttribute("download", `adherents_${selectedActivityName.value.replace(/\s/g, '_')}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

onMounted(() => {
  fetchActivities();
});
</script>
