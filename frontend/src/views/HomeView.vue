<template>
  <div class="home-page public-view">
    <!-- Hero -->
    <section class="hero">
      <img src="@/assets/images/logo_foyer_rural.png" alt="Logo Foyer Rural de Fauverney" class="logo">
      <h1>Foyer Rural de Fauverney</h1>
      <p class="hero-subtitle">Rejoignez notre association et participez à nos activités sportives et culturelles !</p>
      <div class="hero-actions">
        <button @click="startNewForm" class="btn btn-primary btn-lg">S'inscrire</button>
        <RouterLink to="/load" class="btn btn-outline">Reprendre mon inscription</RouterLink>
      </div>
      <p class="hero-hint">Une demande par adhérent — vous pouvez utiliser la même adresse email pour chaque membre de la famille.</p>
    </section>

    <!-- Processus -->
    <section class="process">
      <h2>Comment ça marche ?</h2>
      <div class="process-cards">
        <div class="process-card">
          <div class="process-icon">1</div>
          <h3>Contact</h3>
          <p>Renseignez votre adresse email de contact</p>
        </div>
        <div class="process-card">
          <div class="process-icon">2</div>
          <h3>Vos infos</h3>
          <p>Complétez vos informations personnelles et votre adresse</p>
        </div>
        <div class="process-card">
          <div class="process-icon">3</div>
          <h3>Activités</h3>
          <p>Choisissez parmi nos activités et consultez les tarifs</p>
        </div>
        <div class="process-card">
          <div class="process-icon">4</div>
          <h3>Validation</h3>
          <p>Vérifiez et validez — vous recevrez un code de suivi</p>
        </div>
      </div>
    </section>

    <!-- Activités -->
    <section v-if="activities.length" class="activities-section">
      <h2>Nos activités</h2>
      <div class="activities-grid">
        <div v-for="activity in activities" :key="activity.id!" class="activity-card">
          <div class="activity-header">
            <h3>{{ activity.name }}</h3>
            <span v-if="activity.is_child_activity" class="activity-badge badge-child">Enfant</span>
            <span v-if="activity.is_adult_activity" class="activity-badge badge-adult">Adulte</span>
          </div>
          <p v-if="activity.description" class="activity-desc">{{ activity.description }}</p>
          <p v-if="activity.location" class="activity-location">{{ activity.location }}</p>
          <div class="activity-footer">
            <div class="activity-prices">
              <span v-if="activity.resident_price != null" class="price">{{ activity.resident_price }}€ <small>résident</small></span>
              <span v-if="activity.external_price != null" class="price">{{ activity.external_price }}€ <small>extérieur</small></span>
            </div>
            <div class="activity-status">
              <span v-if="isDeadlinePassed(activity)" class="status-closed">Inscriptions closes</span>
              <span v-else-if="isFull(activity)" class="status-closed">Complet</span>
              <template v-else>
                <span v-if="activity.max_participants > 0" class="status-open">
                  {{ activity.max_participants - (activity.current_participants || 0) }} place(s) restante(s)
                </span>
                <span v-if="activity.registration_deadline" class="status-deadline">
                  Avant le {{ formatDate(activity.registration_deadline) }}
                </span>
              </template>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { RouterLink, useRouter } from 'vue-router';
import { useFormStore } from '@/stores/form';
import api from '@/api';
import type { Activity } from '@/types';

const router = useRouter();
const formStore = useFormStore();
const activities = ref<Activity[]>([]);

const startNewForm = () => {
  formStore.resetForm();
  router.push('/adhesion');
};

const isFull = (a: Activity) => a.max_participants > 0 && a.current_participants >= a.max_participants;

const isDeadlinePassed = (a: Activity) => {
  if (!a.registration_deadline) return false;
  return new Date(a.registration_deadline) < new Date(new Date().toDateString());
};

const formatDate = (d: string) => new Date(d).toLocaleDateString('fr-FR');

onMounted(async () => {
  try {
    const res = await api.get('/api/activities');
    activities.value = res.data;
  } catch {
    // Silencieux si l'API n'est pas disponible
  }
});
</script>

<style scoped>
.home-page {
  padding: 0;
}

/* Hero */
.hero {
  text-align: center;
  padding: 2.5rem 1.5rem 2rem;
  background: linear-gradient(135deg, #e8f0fe 0%, #f0f7ff 100%);
  border-radius: 8px 8px 0 0;
}

.logo {
  max-width: 7rem;
  height: auto;
  margin-bottom: 0.75rem;
}

.hero h1 {
  font-size: 1.8rem;
  margin-bottom: 0.5rem;
}

.hero-subtitle {
  font-size: 1.1rem;
  color: #555;
  margin-bottom: 1.5rem;
  max-width: 500px;
  margin-left: auto;
  margin-right: auto;
}

.hero-actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 1.25rem;
}

.hero-hint {
  font-size: 0.85rem;
  color: #888;
  margin: 0;
}

/* Buttons */
.btn {
  display: inline-block;
  padding: 0.75rem 1.75rem;
  border-radius: 6px;
  font-weight: 600;
  font-size: 1rem;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 2px solid transparent;
}

.btn-primary {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.btn-primary:hover {
  background: var(--color-primary-light);
  border-color: var(--color-primary-light);
}

.btn-lg {
  padding: 0.9rem 2.5rem;
  font-size: 1.15rem;
}

.btn-outline {
  background: transparent;
  color: var(--color-primary);
  border-color: var(--color-primary);
}

.btn-outline:hover {
  background: var(--color-primary);
  color: white;
}

/* Process */
.process {
  padding: 2rem 1.5rem;
}

.process h2 {
  margin-bottom: 1.5rem;
}

.process-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
}

.process-card {
  text-align: center;
  padding: 1.25rem 0.75rem;
  border-radius: 8px;
  background: #f8fafd;
  border: 1px solid var(--color-border);
}

.process-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--color-primary);
  color: white;
  font-weight: 700;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 0.75rem;
}

.process-card h3 {
  font-size: 0.95rem;
  margin-bottom: 0.4rem;
  color: var(--color-text);
}

.process-card p {
  font-size: 0.8rem;
  color: #777;
  margin: 0;
  line-height: 1.4;
}

/* Activities */
.activities-section {
  padding: 1rem 1.5rem 2rem;
  border-top: 1px solid var(--color-border);
}

.activities-section h2 {
  margin-bottom: 1.25rem;
}

.activities-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 1rem;
}

.activity-card {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  transition: box-shadow 0.2s ease;
}

.activity-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.activity-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.activity-header h3 {
  font-size: 1rem;
  margin: 0;
  color: var(--color-text);
  text-align: left;
}

.activity-badge {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.15rem 0.5rem;
  border-radius: 10px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.badge-child {
  background: #e8f5e9;
  color: #2e7d32;
}

.badge-adult {
  background: #e3f2fd;
  color: #1565c0;
}

.activity-desc {
  font-size: 0.85rem;
  color: #666;
  margin: 0;
}

.activity-location {
  font-size: 0.8rem;
  color: #999;
  margin: 0;
}

.activity-footer {
  margin-top: auto;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.activity-prices {
  display: flex;
  gap: 0.75rem;
}

.price {
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--color-primary);
}

.price small {
  font-weight: 400;
  font-size: 0.75rem;
  color: #999;
}

.activity-status {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.2rem;
}

.status-closed {
  font-size: 0.8rem;
  font-weight: 600;
  color: #c62828;
}

.status-open {
  font-size: 0.8rem;
  color: #2e7d32;
}

.status-deadline {
  font-size: 0.75rem;
  color: #999;
}

/* Responsive */
@media (max-width: 768px) {
  .hero h1 {
    font-size: 1.5rem;
  }

  .process-cards {
    grid-template-columns: repeat(2, 1fr);
  }

  .activities-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .process-cards {
    grid-template-columns: 1fr;
  }
}
</style>
