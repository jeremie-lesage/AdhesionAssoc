<template>
  <div class="public-view calendar-page">
    <h1>Planning des activités</h1>

    <div class="filter-bar">
      <button :class="{ active: filter === 'all' }" @click="filter = 'all'">Toutes</button>
      <button :class="{ active: filter === 'adult' }" @click="filter = 'adult'">Adultes</button>
      <button :class="{ active: filter === 'child' }" @click="filter = 'child'">Enfants</button>
    </div>

    <p v-if="loading">Chargement...</p>

    <div v-else class="calendar">
      <div v-for="day in days" :key="day.value" class="calendar-day">
        <div class="day-header">{{ day.label }}</div>
        <div class="day-slots">
          <div
            v-for="activity in activitiesForDay(day.value)"
            :key="activity.id!"
            class="activity-slot"
            :class="{ child: activity.is_child_activity && !activity.is_adult_activity, adult: activity.is_adult_activity && !activity.is_child_activity }"
          >
            <div class="slot-time" v-if="activity.start_time">
              {{ formatTime(activity.start_time) }}<span v-if="activity.end_time"> – {{ formatTime(activity.end_time) }}</span>
            </div>
            <div class="slot-name">{{ activity.name }}</div>
            <div class="slot-details">
              <span v-if="activity.location" class="slot-location">{{ activity.location }}</span>
              <span v-if="isFull(activity)" class="slot-full">Complet</span>
              <span v-else-if="isDeadlinePassed(activity)" class="slot-full">Inscriptions closes</span>
              <span v-else-if="activity.max_participants > 0" class="slot-places">
                {{ activity.max_participants - (activity.current_participants || 0) }} place(s)
              </span>
            </div>
          </div>
          <div v-if="activitiesForDay(day.value).length === 0" class="no-activity">—</div>
        </div>
      </div>
    </div>

    <div style="text-align: center; margin-top: 2rem;">
      <RouterLink to="/adhesion" class="btn btn-primary">S'inscrire</RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { RouterLink } from 'vue-router';
import api from '@/api';
import type { Activity } from '@/types';

const activities = ref<Activity[]>([]);
const loading = ref(true);
const filter = ref<'all' | 'adult' | 'child'>('all');

const days = [
  { label: 'Lundi', value: 0 },
  { label: 'Mardi', value: 1 },
  { label: 'Mercredi', value: 2 },
  { label: 'Jeudi', value: 3 },
  { label: 'Vendredi', value: 4 },
  { label: 'Samedi', value: 5 },
  { label: 'Dimanche', value: 6 },
];

const filteredActivities = computed(() => {
  let result = activities.value.filter(a => a.day_of_week !== null);
  if (filter.value === 'adult') result = result.filter(a => a.is_adult_activity);
  if (filter.value === 'child') result = result.filter(a => a.is_child_activity);
  return result;
});

const activitiesForDay = (day: number) => {
  return filteredActivities.value
    .filter(a => a.day_of_week === day)
    .sort((a, b) => (a.start_time || '').localeCompare(b.start_time || ''));
};

const formatTime = (t: string) => t.substring(0, 5);

const isFull = (a: Activity) => a.max_participants > 0 && a.current_participants >= a.max_participants;

const isDeadlinePassed = (a: Activity) => {
  if (!a.registration_deadline) return false;
  return new Date(a.registration_deadline) < new Date(new Date().toDateString());
};

onMounted(async () => {
  try {
    const res = await api.get('/api/activities');
    activities.value = res.data;
  } catch {
    // silencieux
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.calendar-page h1 {
  text-align: center;
  margin-bottom: 1rem;
}

.filter-bar {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.filter-bar button {
  padding: 0.5rem 1.25rem;
  border: 2px solid var(--color-border);
  border-radius: 20px;
  background: white;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--color-text);
}

.filter-bar button.active {
  border-color: var(--color-primary);
  background: var(--color-primary);
  color: white;
}

.filter-bar button:hover:not(.active) {
  border-color: var(--color-primary-light);
}

.calendar {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 0;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
}

.calendar-day {
  border-right: 1px solid var(--color-border);
  min-height: 120px;
}

.calendar-day:last-child {
  border-right: none;
}

.day-header {
  background: var(--color-primary);
  color: white;
  text-align: center;
  padding: 0.6rem 0.25rem;
  font-weight: 600;
  font-size: 0.85rem;
}

.day-slots {
  padding: 0.35rem;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.activity-slot {
  background: #f0f7ff;
  border-left: 3px solid var(--color-primary);
  border-radius: 4px;
  padding: 0.5rem;
  font-size: 0.78rem;
  line-height: 1.3;
}

.activity-slot.child {
  background: #e8f5e9;
  border-left-color: #2e7d32;
}

.activity-slot.adult {
  background: #e3f2fd;
  border-left-color: #1565c0;
}

.slot-time {
  font-weight: 700;
  color: #555;
  margin-bottom: 0.15rem;
}

.slot-name {
  font-weight: 600;
  color: var(--color-text);
}

.slot-details {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  margin-top: 0.2rem;
}

.slot-location {
  color: #888;
  font-size: 0.72rem;
}

.slot-places {
  color: #2e7d32;
  font-size: 0.72rem;
}

.slot-full {
  color: #c62828;
  font-weight: 600;
  font-size: 0.72rem;
}

.no-activity {
  text-align: center;
  color: #ccc;
  padding: 1rem 0;
}

.btn {
  display: inline-block;
  padding: 0.75rem 1.75rem;
  border-radius: 6px;
  font-weight: 600;
  font-size: 1rem;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary {
  background: var(--color-primary);
  color: white;
}

.btn-primary:hover {
  background: var(--color-primary-light);
}

/* Mobile : affichage en colonne */
@media (max-width: 768px) {
  .calendar {
    grid-template-columns: 1fr;
  }

  .calendar-day {
    border-right: none;
    border-bottom: 1px solid var(--color-border);
    min-height: unset;
  }

  .calendar-day:last-child {
    border-bottom: none;
  }
}
</style>
