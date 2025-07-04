<template>
  <div>
    <h2>Administration des Adhésions</h2>
    <RouterLink to="/admin/activities" class="button">Gérer les Activités</RouterLink>
    <RouterLink to="/admin/adherents-by-activity" class="button">Adhérents par Activité</RouterLink>
    <button @click="exportToCsv" :disabled="!adhesions.length" class="button export-button">Exporter toutes les adhésions en CSV</button>
    <p v-if="loading">Chargement des adhésions...</p>
    <p v-if="error">Erreur lors du chargement des adhésions: {{ error }}</p>
    <table v-if="adhesions.length">
      <thead>
        <tr>
          <th>Code</th>
          <th>Email</th>
          <th>Nom</th>
          <th>Prénom</th>
          <th>Adresse</th>
          <th>Montant Adhésion</th>
          <th>Activités</th>
          <th>Coût Total</th>
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
          <td>{{ adhesion.numero_rue }}, {{ adhesion.nom_rue }} <br/> {{ adhesion.code_postal }} {{ adhesion.ville }}</td>
          <td>{{ adhesion.adhesion_amount }}€</td>
          <td>{{ adhesion.activites ? adhesion.activites.join(', ') : 'Aucune' }}</td>
          <td>{{ calculateTotalCost(adhesion) }}€</td>
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
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';
import { useRouter, RouterLink } from 'vue-router';
import { useFormStore } from '@/stores/form';

const adhesions = ref([]);
const loading = ref(true);
const error = ref(null);
const router = useRouter();
const formStore = useFormStore();
const allActivities = ref([]);

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

const fetchAllActivities = async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/activities');
    allActivities.value = response.data;
  } catch (err) {
    console.error("Erreur lors du chargement des activités:", err);
  }
};

const getPrice = (activity, city) => {
  if (city && city.toLowerCase() === 'fauverney') {
    return activity.resident_price;
  } else {
    return activity.external_price;
  }
};

const calculateTotalCost = (adhesion) => {
  let total = adhesion.adhesion_amount || 0;
  if (adhesion.activites && allActivities.value.length > 0) {
    adhesion.activites.forEach(adhesionActivityName => {
      const activity = allActivities.value.find(act => act.name === adhesionActivityName);
      if (activity) {
        total += getPrice(activity, adhesion.ville) || 0;
      }
    });
  }
  return total;
};

onMounted(() => {
  fetchAdhesions();
  fetchAllActivities();
});

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

const exportToCsv = () => {
  if (!adhesions.value.length) return;

  const headers = [
    "Code", "Email", "Nom", "Prénom", "Numéro Rue", "Nom Rue", 
    "Code Postal", "Ville", "Montant Adhésion", "Activités", "Statut", "Coût Total"
  ];
  const rows = adhesions.value.map(adhesion => [
    adhesion.code,
    adhesion.email,
    adhesion.nom,
    adhesion.prenom,
    adhesion.numero_rue,
    adhesion.nom_rue,
    adhesion.code_postal,
    adhesion.ville,
    adhesion.adhesion_amount,
    adhesion.activites ? adhesion.activites.join(', ') : 'Aucune',
    adhesion.status,
    calculateTotalCost(adhesion)
  ]);

  let csvContent = headers.join(";") + "\n";
  rows.forEach(row => {
    csvContent += row.join(";") + "\n";
  });

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.setAttribute("download", "toutes_adhesions.csv");
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
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


.button {
  display: inline-block;
  padding: 10px 15px;
  background-color: #007bff;
  color: white;
  text-decoration: none;
  border-radius: 5px;
  margin-bottom: 0.5rem;
  margin-right: 0.5rem;
}

.button:hover {
  background-color: #0056b3;
}

.export-button {
  background-color: #28a745;
  margin-left: 0;
}

.export-button:hover {
  background-color: #218838;
}

.export-button {
  background-color: #28a745;
  margin-left: 0;
}

.export-button:hover {
  background-color: #218838;
}
</style>
