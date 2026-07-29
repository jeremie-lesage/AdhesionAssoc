<template>
  <div style="max-width: 960px; margin: 1.5rem auto">
    <h1>Tableau de bord</h1>

    <div v-if="loading" style="padding: 1rem;">Chargement...</div>

    <template v-if="stats">
      <!-- Indicateurs principaux -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-value">{{ stats.total_adhesions }}</div>
          <div class="kpi-label">Adhérents</div>
        </div>
        <div class="kpi-card kpi-warn">
          <div class="kpi-value">{{ stats.pending }}</div>
          <div class="kpi-label">En attente</div>
        </div>
        <div class="kpi-card kpi-success">
          <div class="kpi-value">{{ stats.validated }}</div>
          <div class="kpi-label">Validés</div>
        </div>
        <div class="kpi-card kpi-info">
          <div class="kpi-value">{{ stats.paid }}</div>
          <div class="kpi-label">Payés</div>
        </div>
      </div>

      <!-- Répartitions -->
      <div class="section-grid">
        <Card>
          <template #title>Répartition</template>
          <template #content>
            <dl class="stats-list">
              <dt>Contacts (emails uniques)</dt><dd>{{ stats.total_contacts }}</dd>
              <dt>Résidents Fauverney</dt><dd>{{ stats.residents }}</dd>
              <dt>Extérieurs</dt><dd>{{ stats.external }}</dd>
              <dt>Enfants (&lt;{{ adultAgeThreshold }} ans)</dt><dd>{{ stats.children }}</dd>
              <dt>Adultes</dt><dd>{{ stats.adults }}</dd>
            </dl>
          </template>
        </Card>

        <Card>
          <template #title>Revenus</template>
          <template #content>
            <dl class="stats-list">
              <dt>Total attendu</dt><dd class="revenue">{{ eur(stats.revenue_expected) }}</dd>
              <dt>Total encaissé</dt><dd class="revenue collected">{{ eur(stats.revenue_collected) }}</dd>
              <dt>Reste à encaisser</dt><dd class="revenue pending-amount">{{ eur(stats.revenue_expected - stats.revenue_collected) }}</dd>
            </dl>
          </template>
        </Card>
      </div>

      <!-- Activités -->
      <Card style="margin-top: 1rem;">
        <template #title>Activités</template>
        <template #content>
          <DataTable :value="stats.activities" stripedRows sortMode="multiple" removableSort>
            <Column field="name" header="Activité" sortable />
            <Column header="Type">
              <template #body="{ data }">
                <Tag v-if="data.is_child_activity" value="Enfant" severity="success" />
                <Tag v-if="data.is_adult_activity" value="Adulte" severity="info" />
              </template>
            </Column>
            <Column header="Remplissage" sortable :sortField="'current_participants'">
              <template #body="{ data }">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                  <ProgressBar
                    :value="data.max_participants > 0 ? Math.round(data.current_participants / data.max_participants * 100) : 0"
                    style="width: 100px; height: 8px;"
                    :showValue="false"
                  />
                  <span v-if="data.max_participants > 0">{{ data.current_participants }} / {{ data.max_participants }}</span>
                  <span v-else>{{ data.current_participants }} (illimité)</span>
                </div>
              </template>
            </Column>
            <Column field="revenue_expected" header="Revenus attendus" sortable style="text-align: right;">
              <template #body="{ data }"><div style="text-align: right;">{{ eur(data.revenue_expected) }}</div></template>
            </Column>
            <Column field="revenue_collected" header="Revenus encaissés" sortable style="text-align: right;">
              <template #body="{ data }"><div style="text-align: right;">{{ eur(data.revenue_collected) }}</div></template>
            </Column>
          </DataTable>
        </template>
      </Card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/api';
import Card from 'primevue/card';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Tag from 'primevue/tag';
import ProgressBar from 'primevue/progressbar';

interface ActivityStat {
  id: number;
  name: string;
  is_child_activity: boolean;
  is_adult_activity: boolean;
  max_participants: number;
  current_participants: number;
  revenue_expected: number;
  revenue_collected: number;
}

interface Stats {
  total_adhesions: number;
  pending: number;
  validated: number;
  paid: number;
  total_contacts: number;
  residents: number;
  external: number;
  children: number;
  adults: number;
  revenue_expected: number;
  revenue_collected: number;
  activities: ActivityStat[];
}

const eur = (n: number) => n.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €';

const stats = ref<Stats | null>(null);
const adultAgeThreshold = ref(16);
const loading = ref(true);
const router = useRouter();

onMounted(async () => {
  try {
    const res = await api.get('/api/config');
    adultAgeThreshold.value = res.data.adult_age_threshold;
  } catch {
    // Le libellé garde sa valeur par défaut si la config n'est pas disponible
  }

  try {
    const res = await api.get('/api/admin/stats');
    stats.value = res.data;
  } catch (err: any) {
    if (err.response?.status === 401) {
      router.push({ name: 'admin-login' });
    }
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 1rem;
}

.kpi-card {
  background: white;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 1.25rem;
  text-align: center;
  border-top: 3px solid var(--color-primary);
}

.kpi-card.kpi-warn { border-top-color: #f59e0b; }
.kpi-card.kpi-success { border-top-color: #22c55e; }
.kpi-card.kpi-info { border-top-color: #3b82f6; }

.kpi-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-text);
  line-height: 1;
}

.kpi-label {
  font-size: 0.85rem;
  color: #888;
  margin-top: 0.4rem;
}

.section-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.stats-list {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.5rem 1rem;
  margin: 0;
}

.stats-list dt {
  color: #666;
}

.stats-list dd {
  margin: 0;
  text-align: right;
  font-weight: 600;
}

.revenue { color: var(--color-text); }
.revenue.collected { color: #22c55e; }
.revenue.pending-amount { color: #f59e0b; }

@media (max-width: 768px) {
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .section-grid {
    grid-template-columns: 1fr;
  }
}
</style>
