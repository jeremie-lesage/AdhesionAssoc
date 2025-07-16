<template>
  <div class="container mt-4">
    <h1>Gérer les Demandes par Contact</h1>
    <table class="table table-striped">
      <thead>
        <tr>
          <th>Email du Contact</th>
          <th>Statut</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="contact in contacts" :key="contact.email">
          <td>{{ contact.email }}</td>
          <td>
            <span :class="getStatusClass(contact.status)">{{ contact.status }}</span>
          </td>
          <td>
            <router-link :to="{ name: 'FamilyDetails', params: { email: contact.email } }" class="btn btn-primary">
              Voir les détails
            </router-link>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getContacts } from '@/api';
import type { ContactStatus } from '@/types';

const contacts = ref<ContactStatus[]>([]);

onMounted(async () => {
  try {
    contacts.value = await getContacts();
  } catch (error) {
    console.error("Erreur lors de la récupération des contacts:", error);
  }
});

const getStatusClass = (status: string) => {
  switch (status) {
    case 'pending':
      return 'badge bg-warning text-dark';
    case 'payé':
      return 'badge bg-success';
    case 'Incomplet':
      return 'badge bg-info text-dark';
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
