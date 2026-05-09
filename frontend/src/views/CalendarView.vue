<template>
  <div class="public-view calendar-page">
    <h1>Planning des activités</h1>

    <div class="filter-bar">
      <button :class="{ active: filter === 'all' }" @click="filter = 'all'">Toutes</button>
      <button :class="{ active: filter === 'adult' }" @click="filter = 'adult'">Adultes</button>
      <button :class="{ active: filter === 'child' }" @click="filter = 'child'">Enfants</button>
    </div>

    <p v-if="loading">Chargement...</p>

    <template v-else>
      <!-- Desktop -->
      <div class="schedule-scroll hide-mobile">
        <div class="schedule" :style="{ height: totalHeight + 'px' }">
          <!-- Colonne horaires -->
          <div class="time-col">
            <div class="col-header"></div>
            <div class="time-body" :style="{ height: bodyHeight + 'px' }">
              <div
                v-for="hour in hours"
                :key="hour"
                class="time-tick"
                :style="{ top: (hour - startHour) * HOUR_HEIGHT + 'px' }"
              >{{ hour }}h</div>
            </div>
          </div>

          <!-- Colonnes jours -->
          <div v-for="day in days" :key="day.value" class="day-col">
            <div class="col-header">{{ day.label }}</div>
            <div class="day-body" :style="{ height: bodyHeight + 'px' }">
              <!-- Lignes horaires -->
              <div
                v-for="hour in hours"
                :key="'line-' + hour"
                class="hour-line"
                :style="{ top: (hour - startHour) * HOUR_HEIGHT + 'px' }"
              />
              <!-- Blocs activités -->
              <div
                v-for="activity in activitiesForDay(day.value)"
                :key="activity.id!"
                class="activity-block"
                :class="blockClass(activity)"
                :style="blockStyle(activity)"
              >
                <div class="block-time">{{ fmt(activity.start_time!) }}–{{ fmt(activity.end_time!) }}</div>
                <div class="block-name">{{ activity.name }}</div>
                <div v-if="activity.location" class="block-location">{{ activity.location }}</div>
                <span v-if="isFull(activity)" class="block-badge full">Complet</span>
                <span v-else-if="isDeadlinePassed(activity)" class="block-badge full">Fermé</span>
                <span v-else-if="activity.max_participants > 0" class="block-badge open">
                  {{ activity.max_participants - (activity.current_participants || 0) }} place(s)
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Mobile -->
      <div class="hide-desktop">
        <div v-for="day in days" :key="'m-' + day.value" class="m-day">
          <div class="m-header">{{ day.label }}</div>
          <div v-if="activitiesForDay(day.value).length === 0" class="m-empty">—</div>
          <div
            v-for="activity in activitiesForDay(day.value)"
            :key="activity.id!"
            class="m-slot"
            :class="blockClass(activity)"
          >
            <span class="m-time">{{ fmt(activity.start_time!) }}–{{ fmt(activity.end_time!) }}</span>
            <span class="m-name">{{ activity.name }}</span>
            <span v-if="activity.location" class="m-loc">{{ activity.location }}</span>
          </div>
        </div>
      </div>
    </template>

    <div style="text-align: center; margin-top: 2rem;">
      <RouterLink to="/adhesion" class="btn-cta">S'inscrire</RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { RouterLink } from 'vue-router';
import api from '@/api';
import type { Activity } from '@/types';

const HOUR_HEIGHT = 60;
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

const scheduled = computed(() => {
  let r = activities.value.filter(a => a.day_of_week != null && a.start_time && a.end_time);
  if (filter.value === 'adult') r = r.filter(a => a.is_adult_activity);
  if (filter.value === 'child') r = r.filter(a => a.is_child_activity);
  return r;
});

const toDecimal = (t: string) => { const [h, m] = t.split(':').map(Number); return h + m / 60; };

const startHour = computed(() => {
  if (!scheduled.value.length) return 8;
  return Math.floor(Math.min(...scheduled.value.map(a => toDecimal(a.start_time!))));
});

const endHour = computed(() => {
  if (!scheduled.value.length) return 20;
  return Math.ceil(Math.max(...scheduled.value.map(a => toDecimal(a.end_time!))));
});

const hours = computed(() => {
  const r = [];
  for (let h = startHour.value; h <= endHour.value; h++) r.push(h);
  return r;
});

const bodyHeight = computed(() => (endHour.value - startHour.value) * HOUR_HEIGHT);
const totalHeight = computed(() => bodyHeight.value + 40);

const activitiesForDay = (day: number) =>
  scheduled.value.filter(a => a.day_of_week === day).sort((a, b) => a.start_time!.localeCompare(b.start_time!));

const blockStyle = (a: Activity) => ({
  top: (toDecimal(a.start_time!) - startHour.value) * HOUR_HEIGHT + 'px',
  height: (toDecimal(a.end_time!) - toDecimal(a.start_time!)) * HOUR_HEIGHT + 'px',
});

const blockClass = (a: Activity) => ({
  child: a.is_child_activity && !a.is_adult_activity,
  adult: a.is_adult_activity && !a.is_child_activity,
});

const fmt = (t: string) => t.substring(0, 5);
const isFull = (a: Activity) => a.max_participants > 0 && a.current_participants >= a.max_participants;
const isDeadlinePassed = (a: Activity) => {
  if (!a.registration_deadline) return false;
  return new Date(a.registration_deadline) < new Date(new Date().toDateString());
};

onMounted(async () => {
  try { activities.value = (await api.get('/api/activities')).data; } catch {} finally { loading.value = false; }
});
</script>

<style scoped>
.calendar-page h1 { text-align: center; margin-bottom: 1rem; }

/* Filters */
.filter-bar { display: flex; justify-content: center; gap: 0.5rem; margin-bottom: 1.5rem; }
.filter-bar button {
  padding: 0.5rem 1.25rem; border: 2px solid var(--color-border); border-radius: 20px;
  background: white; font-size: 0.9rem; font-weight: 500; cursor: pointer; color: var(--color-text);
  transition: all 0.2s;
}
.filter-bar button.active { border-color: var(--color-primary); background: var(--color-primary); color: white; }
.filter-bar button:hover:not(.active) { border-color: var(--color-primary-light); }

/* Schedule grid */
.schedule-scroll { overflow-x: auto; }

.schedule {
  display: flex;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
  width: 100%;
}

.time-col { width: 50px; flex-shrink: 0; background: #f8fafd; border-right: 1px solid var(--color-border); }
.day-col { flex: 1; min-width: 0; border-right: 1px solid #f0f0f0; }
.day-col:last-child { border-right: none; }

.col-header {
  height: 40px; display: flex; align-items: center; justify-content: center;
  background: var(--color-primary); color: white; font-weight: 600; font-size: 0.85rem;
  position: sticky; top: 0; z-index: 2;
}

.time-body, .day-body { position: relative; }

.time-tick {
  position: absolute; left: 0; right: 0; height: 0;
  font-size: 0.7rem; color: #999; text-align: right; padding-right: 6px;
  transform: translateY(-0.4em);
}

.hour-line {
  position: absolute; left: 0; right: 0; height: 0;
  border-top: 1px solid #f0f0f0;
}

/* Blocks */
.activity-block {
  position: absolute; left: 2px; right: 2px;
  border-radius: 4px; padding: 0.25rem 0.35rem;
  font-size: 0.7rem; line-height: 1.3; overflow: hidden;
  background: #e3f2fd; border-left: 3px solid #1565c0;
  z-index: 1; transition: box-shadow 0.15s;
}
.activity-block:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.15); z-index: 3; }
.activity-block.child { background: #e8f5e9; border-left-color: #2e7d32; }
.activity-block.adult { background: #e3f2fd; border-left-color: #1565c0; }

.block-time { font-weight: 700; color: #555; }
.block-name { font-weight: 600; }
.block-location { color: #888; font-size: 0.65rem; }
.block-badge { font-size: 0.65rem; }
.block-badge.full { color: #c62828; font-weight: 600; }
.block-badge.open { color: #2e7d32; }

/* CTA */
.btn-cta {
  display: inline-block; padding: 0.75rem 1.75rem; border-radius: 6px;
  font-weight: 600; font-size: 1rem; text-decoration: none;
  background: var(--color-primary); color: white; transition: background 0.2s;
}
.btn-cta:hover { background: var(--color-primary-light); }

/* Mobile */
.hide-mobile { display: flex; }
.hide-desktop { display: none; }

.m-day { margin-bottom: 0.75rem; }
.m-header { background: var(--color-primary); color: white; padding: 0.5rem 1rem; font-weight: 600; border-radius: 6px 6px 0 0; }
.m-empty { padding: 0.75rem 1rem; color: #ccc; border: 1px solid var(--color-border); border-top: none; border-radius: 0 0 6px 6px; text-align: center; }
.m-slot {
  padding: 0.5rem 1rem; border: 1px solid var(--color-border); border-top: none;
  border-left: 3px solid #1565c0; display: flex; flex-wrap: wrap; gap: 0.25rem 0.75rem; align-items: baseline;
}
.m-slot:last-child { border-radius: 0 0 6px 6px; }
.m-slot.child { border-left-color: #2e7d32; }
.m-time { font-weight: 700; color: #555; font-size: 0.9rem; }
.m-name { font-weight: 600; font-size: 0.9rem; }
.m-loc { color: #888; font-size: 0.8rem; }

@media (max-width: 768px) {
  .hide-mobile { display: none !important; }
  .hide-desktop { display: block; }
}
</style>
