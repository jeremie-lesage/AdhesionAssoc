<template>
  <div class="container mt-4" v-if="familyDetails">
    <h1>Détails de la Famille</h1>
    <div class="card">
      <div class="card-header">
        <strong>Email de contact :</strong> {{ familyDetails.email }}
      </div>
      <div class="card-body">
        <h5 class="card-title">Membres de la famille</h5>
        <ul class="list-group mb-3">
          <li v-for="adherent in familyDetails.adherents" :key="adherent.code" class="list-group-item">
            {{ adherent.prenom }} {{ adherent.nom }} - Statut : <span :class="getStatusClass(adherent.status)">{{ adherent.status }}</span>
          </li>
        </ul>
        <h5 class="card-title">Montant total dû</h5>
        <p class="card-text">{{ familyDetails.total_due }} €</p>
      </div>
      <div class="card-footer">
        <router-link to="/admin/contacts" class="btn btn-secondary">Retour à la liste</router-link>
      </div>
    </div>
  </div>
  <div v-else class="container mt-4">
    <p>Chargement des détails de la famille...</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { getFamilyDetails } from '@/api';
import type { FamilyDetails } from '@/types';

const route = useRoute();
const familyDetails = ref<FamilyDetails | null>(null);

onMounted(async () => {
  const email = route.params.email as string;
  if (email) {
    try {
      familyDetails.value = await getFamilyDetails(email);
    } catch (error) {
      console.error("Erreur lors de la récupération des détails de la famille:", error);
    }
  }
});

const getStatusClass = (status: string) => {
  switch (status) {
    case 'pending':
      return 'badge bg-warning text-dark';
    case 'validated':
      return 'badge bg-info text-dark';
    case 'paid':
      return 'badge bg-success';
    default:
      return 'badge bg-secondary';
  }
};
</script>

<style scoped>
.container {
  max-width: 960px;
}
</style>
