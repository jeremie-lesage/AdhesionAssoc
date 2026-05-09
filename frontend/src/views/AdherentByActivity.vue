<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
      <h2 style="margin: 0;">Adhérents par Activité</h2>
      <Button label="Tout exporter en ZIP" icon="pi pi-file-export" :loading="exporting" :disabled="!activities.length" @click="exportAllToZip" />
    </div>

    <p v-if="loadingActivities">Chargement des activités...</p>

    <Tabs v-if="activities.length" :value="activeTab" @update:value="onTabChange">
      <TabList>
        <Tab v-for="activity in activities" :key="activity.id!" :value="String(activity.id)">
          {{ activity.name }}
        </Tab>
      </TabList>
      <TabPanels>
        <TabPanel v-for="activity in activities" :key="activity.id!" :value="String(activity.id)">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <div>
              <span v-if="activity.location" style="color: var(--p-surface-500);">{{ activity.location }}</span>
              <span v-if="activity.max_participants > 0" style="margin-left: 1rem;">
                — {{ adherents.length }} / {{ activity.max_participants }} inscrits
              </span>
              <span v-else style="margin-left: 1rem;">— {{ adherents.length }} inscrits</span>
            </div>
            <Button label="Exporter CSV" icon="pi pi-download" severity="secondary" size="small" :disabled="!adherents.length" @click="exportToCsv(activity)" />
          </div>

          <p v-if="loadingAdherents">Chargement...</p>

          <DataTable v-else-if="adherents.length" :value="adherents" stripedRows sortMode="multiple" removableSort>
            <Column field="nom" header="Nom" sortable />
            <Column field="prenom" header="Prénom" sortable />
            <Column field="email" header="Email" sortable />
            <Column field="telephone" header="Téléphone" sortable />
            <Column field="ville" header="Ville" sortable />
            <Column field="status" header="Statut" sortable>
              <template #body="{ data }">
                <Tag :value="statusLabel(data.status)" :severity="statusSeverity(data.status)" />
              </template>
            </Column>
          </DataTable>
          <p v-else style="color: var(--p-surface-400); font-style: italic;">Aucun inscrit pour cette activité.</p>
        </TabPanel>
      </TabPanels>
    </Tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import JSZip from 'jszip';
import api from '@/api';
import { useRouter } from 'vue-router';
import type { Activity, Adhesion } from '@/types';
import Tabs from 'primevue/tabs';
import TabList from 'primevue/tablist';
import Tab from 'primevue/tab';
import TabPanels from 'primevue/tabpanels';
import TabPanel from 'primevue/tabpanel';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Button from 'primevue/button';
import Tag from 'primevue/tag';

const activities = ref<Activity[]>([]);
const adherents = ref<Adhesion[]>([]);
const activeTab = ref('');
const loadingActivities = ref(true);
const loadingAdherents = ref(false);
const exporting = ref(false);
const router = useRouter();

const statusLabel = (status: string) => {
  switch (status) {
    case 'pending': return 'En attente';
    case 'validated': return 'Validé';
    case 'paid': return 'Payé';
    default: return status;
  }
};

const statusSeverity = (status: string) => {
  switch (status) {
    case 'pending': return 'warn';
    case 'validated': return 'success';
    case 'paid': return 'info';
    default: return 'secondary';
  }
};

const onTabChange = (value: string | number) => {
  activeTab.value = String(value);
  fetchAdherents(Number(value));
};

const fetchAdherents = async (activityId: number) => {
  loadingAdherents.value = true;
  try {
    const res = await api.get(`/api/activities/${activityId}/adherents`);
    adherents.value = res.data;
  } catch (err: any) {
    if (err.response?.status === 401) {
      router.push({ name: 'admin-login' });
    }
    adherents.value = [];
  } finally {
    loadingAdherents.value = false;
  }
};

const buildCsv = (adherentsList: Adhesion[]) => {
  const headers = ['Nom', 'Prénom', 'Email', 'Téléphone', 'Ville', 'Statut'];
  const rows = adherentsList.map(a => [a.nom, a.prenom, a.email, a.telephone || '', a.ville, a.status]);
  return '﻿' + headers.join(';') + '\n' + rows.map(r => r.join(';')).join('\n');
};

const exportAllToZip = async () => {
  exporting.value = true;
  try {
    const zip = new JSZip();
    for (const activity of activities.value) {
      const res = await api.get(`/api/activities/${activity.id}/adherents`);
      const csv = buildCsv(res.data);
      zip.file(`${activity.name.replace(/[/\\?%*:|"<>]/g, '_')}.csv`, csv);
    }
    const blob = await zip.generateAsync({ type: 'blob' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.setAttribute('download', 'adherents_par_activite.zip');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } finally {
    exporting.value = false;
  }
};

const exportToCsv = (activity: Activity) => {
  if (!adherents.value.length) return;

  const headers = ['Nom', 'Prénom', 'Email', 'Téléphone', 'Ville', 'Statut'];
  const rows = adherents.value.map(a => [a.nom, a.prenom, a.email, a.telephone || '', a.ville, a.status]);

  let csv = headers.join(';') + '\n';
  rows.forEach(row => { csv += row.join(';') + '\n'; });

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.setAttribute('download', `adherents_${activity.name.replace(/\s/g, '_')}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

onMounted(async () => {
  try {
    const res = await api.get('/api/activities');
    activities.value = res.data;
    if (activities.value.length) {
      activeTab.value = String(activities.value[0].id);
      fetchAdherents(activities.value[0].id!);
    }
  } catch (err: any) {
    if (err.response?.status === 401) {
      router.push({ name: 'admin-login' });
    }
  } finally {
    loadingActivities.value = false;
  }
});
</script>

<style scoped>
:deep(.p-tablist-tab-list) {
  flex-wrap: wrap;
}
</style>
