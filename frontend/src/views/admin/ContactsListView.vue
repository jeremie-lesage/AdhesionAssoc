<template>
  <div style="max-width: 960px; margin: 1.5rem auto">
    <h1>Gérer les Demandes par Contact</h1>

    <div style="display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; margin-bottom: 1rem;">
      <InputText v-model="searchQuery" placeholder="Rechercher par email..." style="width: 280px;" />
      <Select v-model="selectedStatus" :options="statusOptions" optionLabel="label" optionValue="value" placeholder="Statut" style="width: 180px;" />
    </div>

    <DataTable :value="filteredContacts" stripedRows sortMode="multiple" removableSort paginator :rows="20">
      <Column field="email" header="Email du Contact" sortable />
      <Column field="status" header="Statut" sortable>
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
import { ref, computed, onMounted } from 'vue';
import { getContacts } from '@/api';
import type { ContactStatus } from '@/types';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Tag from 'primevue/tag';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import Select from 'primevue/select';

const contacts = ref<ContactStatus[]>([]);
const searchQuery = ref('');
const selectedStatus = ref('all');

const statusOptions = computed(() => {
  const statuses = new Set(contacts.value.map(c => c.status));
  return [
    { label: 'Tous', value: 'all' },
    ...Array.from(statuses).map(s => ({ label: s, value: s })),
  ];
});

const filteredContacts = computed(() => {
  let result = contacts.value;
  if (selectedStatus.value !== 'all') {
    result = result.filter(c => c.status === selectedStatus.value);
  }
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    result = result.filter(c => c.email.toLowerCase().includes(query));
  }
  return result;
});

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
