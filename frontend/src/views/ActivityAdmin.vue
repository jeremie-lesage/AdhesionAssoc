<template>
  <div>
    <h2>Administration des Activités</h2>

    <h3>Ajouter une nouvelle activité</h3>
    <form @submit.prevent="addActivity">
      <input type="text" v-model="newActivityName" placeholder="Nom de l'activité" required>
      <button type="submit">Ajouter</button>
    </form>

    <h3>Activités existantes</h3>
    <p v-if="loading">Chargement des activités...</p>
    <p v-if="error">Erreur lors du chargement des activités: {{ error }}</p>
    <ul v-if="activities.length">
      <li v-for="activity in activities" :key="activity.id">
        {{ activity.name }}
        <button @click="deleteActivity(activity.id)" class="delete-button">Supprimer</button>
      </li>
    </ul>
    <p v-else-if="!loading && !error">Aucune activité définie.</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';

const activities = ref([]);
const newActivityName = ref('');
const loading = ref(true);
const error = ref(null);

const fetchActivities = async () => {
  loading.value = true;
  error.value = null;
  try {
    const response = await axios.get('http://localhost:8000/api/activities');
    activities.value = response.data;
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
};

const addActivity = async () => {
  if (!newActivityName.value) return;
  try {
    await axios.post('http://localhost:8000/api/activities', { name: newActivityName.value });
    newActivityName.value = '';
    fetchActivities(); // Recharger la liste
  } catch (err) {
    alert(`Erreur lors de l'ajout de l'activité: ${err.response?.data?.detail || err.message}`);
  }
};

const deleteActivity = async (id: number) => {
  if (!confirm('Êtes-vous sûr de vouloir supprimer cette activité ?')) return;
  try {
    await axios.delete(`http://localhost:8000/api/activities/${id}`);
    fetchActivities(); // Recharger la liste
  } catch (err) {
    alert(`Erreur lors de la suppression de l'activité: ${err.response?.data?.detail || err.message}`);
  }
};

onMounted(fetchActivities);
</script>

<style scoped>
ul {
  list-style: none;
  padding: 0;
}

li {
  background-color: #f9f9f9;
  border: 1px solid var(--color-border);
  padding: 10px;
  margin-bottom: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-radius: 4px;
}

.delete-button {
  background-color: #e74c3c;
  margin-left: 15px;
}

.delete-button:hover {
  background-color: #c0392b;
}

form {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

form input {
  flex-grow: 1;
}
</style>
