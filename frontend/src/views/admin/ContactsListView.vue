<template>
  <div style="max-width: 960px; margin: 1.5rem auto">
    <h1>Gérer les Demandes par Contact</h1>
    <DataTable :value="contacts" stripedRows>
      <Column field="email" header="Email du Contact" />
      <Column header="Statut">
        <template #body="{ data }">
          <Tag :value="data.status" :severity="getStatusSeverity(data.status)" />
        </template>
      </Column>
      <Column header="Actions">
        <template #body="{ data }">
          <Button
            label="Voir les détails"
            icon="pi pi-eye"
            size="small"
            as="router-link"
            :to="{ name: 'FamilyDetails', params: { email: data.email } }"
          />
        </template>
      </Column>
    </DataTable>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getContacts } from '@/api';
import type { ContactStatus } from '@/types';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Tag from 'primevue/tag';
import Button from 'primevue/button';

const contacts = ref<ContactStatus[]>([]);

onMounted(async () => {
  try {
    contacts.value = await getContacts();
  } catch (error) {
    console.error("Erreur lors de la récupération des contacts:", error);
  }
});

const getStatusSeverity = (status: string) => {
  switch (status) {
    case 'pending':
      return 'warn';
    case 'payé':
      return 'success';
    case 'Incomplet':
      return 'info';
    default:
      return 'secondary';
  }
};
</script>
