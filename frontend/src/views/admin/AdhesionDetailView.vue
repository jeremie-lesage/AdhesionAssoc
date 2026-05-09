<template>
  <div style="max-width: 960px; margin: 1.5rem auto">
    <div v-if="!adhesion" style="padding: 1rem;">Chargement...</div>
    <template v-else>
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <h1 style="margin: 0;">{{ adhesion.prenom }} {{ adhesion.nom }}</h1>
        <Tag :value="getStatusLabel(adhesion.status)" :severity="getStatusSeverity(adhesion.status)" style="font-size: 1rem;" />
      </div>

      <div class="detail-grid">
        <Card>
          <template #title>Coordonnées</template>
          <template #content>
            <dl class="info-list">
              <dt>Email</dt><dd>{{ adhesion.email }}</dd>
              <dt>Téléphone</dt><dd>{{ adhesion.telephone || '—' }}</dd>
              <dt>Date de naissance</dt><dd>{{ adhesion.date_naissance }}</dd>
            </dl>
          </template>
        </Card>

        <Card>
          <template #title>Adresse</template>
          <template #content>
            <dl class="info-list">
              <dt>Rue</dt><dd>{{ adhesion.numero_rue }} {{ adhesion.nom_rue }}</dd>
              <dt>Code postal</dt><dd>{{ adhesion.code_postal }}</dd>
              <dt>Ville</dt><dd>{{ adhesion.ville }}</dd>
            </dl>
          </template>
        </Card>

        <Card>
          <template #title>Inscription</template>
          <template #content>
            <dl class="info-list">
              <dt>Code</dt><dd style="font-family: monospace;">{{ adhesion.code }}</dd>
              <dt>Adhésion</dt><dd>{{ adhesion.adhesion_amount }} €</dd>
              <dt>Paiement</dt><dd>{{ adhesion.payment_method || '—' }}</dd>
            </dl>
          </template>
        </Card>

        <Card>
          <template #title>Activités</template>
          <template #content>
            <ul v-if="adhesion.activities.length" style="list-style: none; padding: 0; margin: 0;">
              <li v-for="activity in adhesion.activities" :key="activity.id!" style="padding: 0.3rem 0; display: flex; justify-content: space-between;">
                <span>{{ activity.name }}</span>
                <span style="font-weight: 600; color: var(--color-primary);">{{ getPrice(activity) }} €</span>
              </li>
            </ul>
            <p v-else style="color: #999; margin: 0;">Aucune activité sélectionnée</p>
            <div style="border-top: 1px solid var(--color-border); margin-top: 0.75rem; padding-top: 0.75rem; display: flex; justify-content: space-between; font-weight: 600;">
              <span>Total</span>
              <span>{{ totalCost.toFixed(2) }} €</span>
            </div>
          </template>
        </Card>
      </div>

      <div style="display: flex; gap: 0.5rem; margin-top: 1.5rem;">
        <Button label="Retour" icon="pi pi-arrow-left" severity="secondary" @click="router.push({ name: 'admin-adhesions' })" />
        <Button v-if="adhesion.status !== 'paid'" label="Modifier" icon="pi pi-pencil" severity="info" @click="router.push({ name: 'adhesion', query: { code: adhesion.code, source: 'admin' } })" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getAdhesionByCode } from '@/api';
import type { Adhesion, Activity } from '@/types';
import Card from 'primevue/card';
import Tag from 'primevue/tag';
import Button from 'primevue/button';

const route = useRoute();
const router = useRouter();
const adhesion = ref<Adhesion | null>(null);

const getPrice = (activity: Activity) => {
  if (!adhesion.value) return 0;
  const isResident = adhesion.value.ville.toLowerCase() === 'fauverney';
  return (isResident ? activity.resident_price : activity.external_price) || 0;
};

const totalCost = computed(() => {
  if (!adhesion.value) return 0;
  const activitiesCost = adhesion.value.activities.reduce((sum, a) => sum + getPrice(a), 0);
  return (adhesion.value.adhesion_amount || 0) + activitiesCost;
});

const getStatusLabel = (status: string) => {
  switch (status) {
    case 'pending': return 'En attente';
    case 'validated': return 'Validé';
    case 'paid': return 'Payé';
    default: return status;
  }
};

const getStatusSeverity = (status: string) => {
  switch (status) {
    case 'pending': return 'warn';
    case 'validated': return 'success';
    case 'paid': return 'info';
    default: return undefined;
  }
};

onMounted(async () => {
  const code = route.params.code as string;
  try {
    adhesion.value = await getAdhesionByCode(code);
  } catch {
    router.push({ name: 'admin-adhesions' });
  }
});
</script>

<style scoped>
.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.info-list {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.4rem 1rem;
  margin: 0;
}

.info-list dt {
  font-weight: 600;
  color: #666;
}

.info-list dd {
  margin: 0;
}

@media (max-width: 768px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
