<template>
  <div>
    <h2>Administration des Activités</h2>

    <h3>Activités existantes</h3>
    <p v-if="loading">Chargement des activités...</p>
    <p v-if="error">Erreur lors du chargement des activités: {{ error }}</p>
    <table v-if="activities.length">
      <thead>
        <tr>
          <th>Nom</th>
          <th>Description</th>
          <th>Lieu</th>
          <th>Tarif Résident</th>
          <th>Tarif Extérieur</th>
          <th>Enfant</th>
          <th>Adulte</th>
          <th>Inscrits / Places</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="activity in activities" :key="activity.id">
          <td>{{ activity.name }}</td>
          <td>{{ activity.description }}</td>
          <td>{{ activity.location }}</td>
          <td>{{ activity.resident_price }}</td>
          <td>{{ activity.external_price }}</td>
          <td>{{ activity.is_child_activity ? 'Oui' : 'Non' }}</td>
          <td>{{ activity.is_adult_activity ? 'Oui' : 'Non' }}</td>
          <td>
            <span v-if="activity.max_participants > 0">{{ activity.current_participants }} / {{ activity.max_participants }}</span>
            <span v-else>Illimité</span>
          </td>
          <td>
            <button @click="startEdit(activity)">Modifier</button>
            <button @click="deleteActivity(activity.id)" class="delete-button">Supprimer</button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else-if="!loading && !error">Aucune activité définie.</p>


    <h3>Ajouter/Modifier une activité</h3>
    <form @submit.prevent="isEditing ? updateActivity() : addActivity()">
      <input type="hidden" v-model="editingActivity.id">
      <div class="form-group">
        <label for="name">Nom de l'activité:</label>
        <input type="text" id="name" v-model="editingActivity.name" placeholder="Nom de l'activité" required>
      </div>
      <div class="form-group">
        <label for="description">Description:</label>
        <textarea id="description" v-model="editingActivity.description" placeholder="Description"></textarea>
      </div>
      <div class="form-group">
        <label for="location">Lieu (École ou Foyer):</label>
        <input type="text" id="location" v-model="editingActivity.location" placeholder="Lieu (École ou Foyer)">
      </div>
      <div class="form-group">
        <label for="resident_price">Tarif Résident:</label>
        <input type="number" id="resident_price" v-model="editingActivity.resident_price" placeholder="Tarif Résident" step="0.01">
      </div>
      <div class="form-group">
        <label for="external_price">Tarif Extérieur:</label>
        <input type="number" id="external_price" v-model="editingActivity.external_price" placeholder="Tarif Extérieur" step="0.01">
      </div>
      <div class="form-group">
        <label for="max_participants">Nombre de places disponibles:</label>
        <input type="number" id="max_participants" v-model="editingActivity.max_participants" placeholder="Nombre de places" min="0">
      </div>
      <div class="form-group checkbox-group">
        <label>
          <input type="checkbox" v-model="editingActivity.is_child_activity"> Activité Enfant
        </label>
        <label>
          <input type="checkbox" v-model="editingActivity.is_adult_activity"> Activité Adulte
        </label>
      </div>
      <div class="form-actions">
        <button type="submit">{{ isEditing ? 'Modifier' : 'Ajouter' }}</button>
        <button type="button" @click="cancelEdit" v-if="isEditing">Annuler</button>
      </div>
    </form>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';

const activities = ref([]);
const editingActivity = ref({
  id: null,
  name: '',
  description: '',
  location: '',
  resident_price: null,
  external_price: null,
  is_child_activity: false,
  is_adult_activity: false,
  max_participants: 0,
});
const isEditing = ref(false);
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
  try {
    await axios.post('http://localhost:8000/api/activities', editingActivity.value);
    resetForm();
    fetchActivities();
  } catch (err) {
    alert(`Erreur lors de l'ajout de l'activité: ${err.response?.data?.detail || err.message}`);
  }
};

const startEdit = (activity) => {
  editingActivity.value = { ...activity };
  isEditing.value = true;
};

const updateActivity = async () => {
  try {
    await axios.put(`http://localhost:8000/api/activities/${editingActivity.value.id}`, editingActivity.value);
    resetForm();
    fetchActivities();
  } catch (err) {
    alert(`Erreur lors de la mise à jour de l'activité: ${err.response?.data?.detail || err.message}`);
  }
};

const cancelEdit = () => {
  resetForm();
};

const resetForm = () => {
  editingActivity.value = {
    id: null,
    name: '',
    description: '',
    location: '',
    resident_price: null,
    external_price: null,
    is_child_activity: false,
    is_adult_activity: false,
    max_participants: 0,
  };
  isEditing.value = false;
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
form {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 20px;
  padding: 20px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background-color: var(--color-background-soft);
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  margin-bottom: 5px;
  font-weight: bold;
  color: var(--color-heading);
}

.form-group input[type="text"],
.form-group input[type="number"],
.form-group textarea {
  padding: 10px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 1rem;
  width: 100%;
  box-sizing: border-box; /* Include padding and border in the element's total width and height */
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
}

.checkbox-group {
  display: flex;
  flex-direction: row;
  gap: 20px;
  margin-top: 10px;
  margin-bottom: 10px;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  font-weight: normal;
}

.checkbox-group input[type="checkbox"] {
  margin-right: 8px;
  transform: scale(1.2);
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

form button {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.3s ease;
}

form button[type="submit"] {
  background-color: var(--color-primary);
  color: white;
}

form button[type="submit"]:hover {
  background-color: var(--color-primary-dark);
}

form button[type="button"] {
  background-color: var(--color-secondary);
  color: white;
}

form button[type="button"]:hover {
  background-color: var(--color-secondary-dark);
}

/* Table styles */
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}

table th,
table td {
  border: 1px solid var(--color-border);
  padding: 10px;
  text-align: left;
}

table th {
  background-color: var(--color-background-soft);
  font-weight: bold;
}

table tr:nth-child(even) {
  background-color: var(--color-background-mute);
}

table button {
  padding: 8px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  margin-right: 5px;
  transition: background-color 0.3s ease;
}

table button:hover {
  opacity: 0.9;
}

table button:first-of-type {
  background-color: #3498db; /* Blue for Edit */
  color: white;
}

.delete-button {
  background-color: #e74c3c; /* Red for Delete */
  color: white;
}

.delete-button:hover {
  background-color: #c0392b;
}

/* General spacing */
h2,
h3 {
  margin-top: 25px;
  margin-bottom: 15px;
  color: var(--color-heading);
}

p {
  margin-bottom: 10px;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  form {
    padding: 15px;
  }

  .checkbox-group {
    flex-direction: column;
    gap: 10px;
  }

  table,
  thead,
  tbody,
  th,
  td,
  tr {
    display: block;
  }

  thead tr {
    position: absolute;
    top: -9999px;
    left: -9999px;
  }

  tr {
    border: 1px solid var(--color-border);
    margin-bottom: 10px;
  }

  td {
    border: none;
    border-bottom: 1px solid var(--color-border);
    position: relative;
    padding-left: 50%;
    text-align: right;
  }

  td:before {
    position: absolute;
    top: 6px;
    left: 6px;
    width: 45%;
    padding-right: 10px;
    white-space: nowrap;
    text-align: left;
    font-weight: bold;
  }

  /* Label the data */
  td:nth-of-type(1):before { content: "Nom:"; }
  td:nth-of-type(2):before { content: "Description:"; }
  td:nth-of-type(3):before { content: "Lieu:"; }
  td:nth-of-type(4):before { content: "Tarif Résident:"; }
  td:nth-of-type(5):before { content: "Tarif Extérieur:"; }
  td:nth-of-type(6):before { content: "Enfant:"; }
  td:nth-of-type(7):before { content: "Adulte:"; }
  td:nth-of-type(8):before { content: "Actions:"; }
}
</style>
