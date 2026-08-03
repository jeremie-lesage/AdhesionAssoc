<template>
  <div style="max-width: 960px; margin: 1.5rem auto" v-if="familyDetails">
    <h1>Détails de la Famille</h1>
    <Card>
      <template #title>
        Email de contact : {{ familyDetails.email }}
      </template>
      <template #content>
        <h3>Membres de la famille</h3>
        <DataTable :value="familyDetails.adherents" class="mb-3">
          <Column header="Membre">
            <template #body="{ data }">
              {{ data.prenom }} {{ data.nom }}
            </template>
          </Column>
          <Column field="telephone" header="Téléphone" />
          <Column header="Statut">
            <template #body="{ data }">
              <Tag :value="data.status" :severity="getStatusSeverity(data.status)" />
            </template>
          </Column>
          <Column header="Actions">
            <template #body="{ data }">
              <Button
                label="Voir l'adhésion"
                icon="pi pi-eye"
                size="small"
                as="router-link"
                :to="{ name: 'admin-adhesion-detail', params: { code: data.code } }"
              />
            </template>
          </Column>
        </DataTable>
        <h3>Montant total dû</h3>
        <p class="total-due">{{ familyDetails.total_due }} €</p>
      </template>
      <template #footer>
        <Button
          label="Retour à la liste"
          icon="pi pi-arrow-left"
          severity="secondary"
          as="router-link"
          to="/admin/contacts"
        />
      </template>
    </Card>
  </div>
  <div v-else style="max-width: 960px; margin: 1.5rem auto">
    <p>Chargement des détails de la famille...</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { getFamilyDetails } from '@/api';
import type { FamilyDetails } from '@/types';
import Card from 'primevue/card';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Tag from 'primevue/tag';
import Button from 'primevue/button';

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

const getStatusSeverity = (status: string) => {
  switch (status) {
    case 'pending':
      return 'warn';
    case 'validated':
      return 'info';
    case 'paid':
      return 'success';
    default:
      return 'secondary';
  }
};
</script>

<style scoped>
/* `main.css` centre les titres h1/h2/h3 mais pas les paragraphes, qui héritent
   du `text-align: left` de `#app` : sans cette règle le montant est décalé à
   gauche sous son titre centré. */
.total-due {
  text-align: center;
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
}
</style>
