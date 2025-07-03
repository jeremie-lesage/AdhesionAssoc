<template>
  <div>
    <h2>Administration des Adhésions</h2>
    <RouterLink to="/admin/activities" class="button">Gérer les Activités</RouterLink>
    <p v-if="loading">Chargement des adhésions...</p>
    <p v-if="error">Erreur lors du chargement des adhésions: {{ error }}</p>
    <table v-if="adhesions.length">
      <thead>
        <tr>
          <th>Code</th>
          <th>Email</th>
          <th>Nom</th>
          <th>Prénom</th>
          <th>Activités</th>
          <th>Statut</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="adhesion in adhesions" :key="adhesion.id">
          <td>{{ adhesion.code }}</td>
          <td>{{ adhesion.email }}</td>
          <td>{{ adhesion.nom }}</td>
          <td>{{ adhesion.prenom }}</td>
          <td>{{ adhesion.activites ? adhesion.activites.join(', ') : 'Aucune' }}</td>
          <td>{{ adhesion.status }}</td>
          <td>
            <button @click="editAdhesion(adhesion.code)">Corriger</button>
            <button v-if="adhesion.status === 'pending'" @click="validateAdhesion(adhesion.code)" class="validate-button">Valider</button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else-if="!loading && !error">Aucune adhésion trouvée.</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { useRouter, RouterLink } from 'vue-router';
import { useFormStore } from '@/stores/form';

const adhesions = ref([]);
const loading = ref(true);
const error = ref(null);
const router = useRouter();
const formStore = useFormStore();

const fetchAdhesions = async () => {
  loading.value = true;
  error.value = null;
  try {
    const response = await axios.get('http://localhost:8000/api/adhesions');
    adhesions.value = response.data;
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
};

onMounted(fetchAdhesions);

const editAdhesion = async (code: string) => {
  try {
    const response = await axios.get(`http://localhost:8000/api/adhesions/${code}`);
    formStore.formData = response.data;
    formStore.formData.code = response.data.code; // Assurez-vous que le code est bien stocké
    router.push('/adhesion'); // Redirige vers la page du formulaire
  } catch (err) {
    alert(`Impossible de charger le formulaire pour le code ${code}: ${err.message}`);
  }
};

const validateAdhesion = async (code: string) => {
  if (!confirm('Êtes-vous sûr de vouloir valider cette adhésion ?')) return;
  try {
    await axios.put(`http://localhost:8000/api/adhesions/${code}/validate`);
    alert('Adhésion validée avec succès !');
    fetchAdhesions(); // Recharger la liste
  } catch (err) {
    alert(`Erreur lors de la validation de l'adhésion: ${err.response?.data?.detail || err.message}`);
  }
};
</script>

<style scoped>
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

.validate-button {
  background-color: #28a745;
  margin-left: 10px;
}

.validate-button:hover {
  background-color: #218838;
}
</style>
