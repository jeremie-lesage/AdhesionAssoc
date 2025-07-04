<template>
  <div>
    <h2>Adhérents par Activité</h2>
    <RouterLink to="/admin" class="button">Retour à l'Administration</RouterLink>

    <div class="activity-selector">
      <label for="activity-select">Sélectionner une activité:</label>
      <select id="activity-select" v-model="selectedActivityId" @change="fetchAdherentsForActivity">
        <option value="">-- Choisir une activité --</option>
        <option v-for="activity in activities" :key="activity.id" :value="activity.id">
          {{ activity.name }}
        </option>
      </select>
    </div>

    <p v-if="loading">Chargement des adhérents...</p>
    <p v-if="error">Erreur: {{ error }}</p>

    <div v-if="selectedActivityId && !loading && !error">
      <h3>Adhérents pour l'activité: {{ selectedActivityName }}</h3>
      <p>Nombre total d'adhérents: {{ adherents.length }}</p>
      <button @click="exportToCsv" :disabled="!adherents.length" class="button export-button">Exporter en CSV</button>

      <table v-if="adherents.length">
        <thead>
          <tr>
            <th>Nom</th>
            <th>Prénom</th>
            <th>Email</th>
            <th>Statut</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="adherent in adherents" :key="adherent.id">
            <td>{{ adherent.nom }}</td>
            <td>{{ adherent.prenom }}</td>
            <td>{{ adherent.email }}</td>
            <td>{{ adherent.status }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else>Aucun adhérent pour cette activité.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import api from '@/api';
import { RouterLink } from 'vue-router';

const activities = ref([]);
const selectedActivityId = ref<number | string>('');
const adherents = ref([]);
const loading = ref(false);
const error = ref<string | null>(null);

const selectedActivityName = computed(() => {
  const activity = activities.value.find(act => act.id === selectedActivityId.value);
  return activity ? activity.name : '';
});

const fetchActivities = async () => {
  try {
    const response = await api.get('/api/activities');
    activities.value = response.data;
  } catch (err: any) {
    error.value = err.message;
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
    error.value = err.message;
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

<style scoped>
.activity-selector {
  margin-bottom: 20px;
}

.activity-selector label {
  margin-right: 10px;
}

.activity-selector select {
  padding: 8px;
  border-radius: 4px;
  border: 1px solid #ccc;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}

th, td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

th {
  background-color: #f2f2f2;
}

.button {
  display: inline-block;
  padding: 10px 15px;
  background-color: #007bff;
  color: white;
  text-decoration: none;
  border-radius: 5px;
  margin-bottom: 20px;
}

.button:hover {
  background-color: #0056b3;
}

.export-button {
  background-color: #28a745;
  margin-left: 10px;
}

.export-button:hover {
  background-color: #218838;
}
</style>
