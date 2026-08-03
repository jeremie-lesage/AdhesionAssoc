<template>
  <div>
    <h2>Étape 3: Choix des Activités</h2>
    <p>
      Affichage des activités pour {{ adherentAge < 16 ? 'enfants' : 'adultes' }}.
    </p>
    <p v-if="formData.ville">
      Tarif appliqué: {{ formData.ville.toLowerCase() === 'fauverney' ? 'résident' : 'extérieur' }}.
    </p>
    <p v-if="loadingActivities">Chargement des activités...</p>
    <p v-if="activitiesError">Erreur lors du chargement des activités: {{ activitiesError }}</p>
    <form v-if="!loadingActivities && !activitiesError" @submit.prevent="nextStep">
      <h3>Adhésion Obligatoire</h3>
      <div class="adhesion-section">
        <label>
          Montant de l'adhésion:
        </label>
        <div>
          <template v-if="adherentAge >= 16">
            <label>
              <input v-model="formData.adhesion_amount" :value="12" name="adult_adhesion_amount" type="radio"> 12€
            </label>
          </template>
          <template v-else>
            <label>
              <input v-model="formData.adhesion_amount" :value="8" name="first_child_adhesion_amount" type="radio"> 8€
              (Premier enfant)
            </label>
            <label>
              <input v-model="formData.adhesion_amount" :value="6" name="child_adhesion_amount" type="radio"> 6€
              (Deuxième enfant et suivants)
            </label>
          </template>
        </div>
      </div>

      <h3>Liste des activités proposées</h3>
      <p v-if="adherentAge < 16">Détails des activités sur <a
          href="https://foyerruralfauverney.fr/activites/activites-enfant/" target="_blank">notre site internet</a></p>
      <p v-else> Détails des activités sur <a href="https://foyerruralfauverney.fr/activites/activites-adulte/"
                                              target="_blank">notre site internet</a></p>
      <fieldset v-for="group in activityGroups" :key="group.key" class="day-group">
        <legend v-if="group.label">{{ group.label }}</legend>

        <label v-for="activity in group.activities" :key="activity.id!"
               :class="{ unavailable: isActivityUnavailable(activity) }"
               class="activity-option">
          <input v-model="selectedActivityIds"
                 :disabled="isActivityUnavailable(activity)"
                 :value="activity.id"
                 class="activity-checkbox"
                 type="checkbox">

          <div class="activity-main">
            <span class="activity-name">{{ activity.name }}</span>
            <span v-if="activity.description" class="activity-desc">{{ activity.description }}</span>
            <span v-if="activityContext(activity)" class="activity-context">{{ activityContext(activity) }}</span>
            <span v-if="hasDocument(activity)" class="activity-document">
              📄 Document à remplir et signer —
              <a :href="documentUrl(activity)" target="_blank" @click.stop>télécharger</a>
            </span>
          </div>

          <div class="activity-meta">
            <span v-if="getPrice(activity) !== null" class="activity-price">{{ getPrice(activity) }}€</span>
            <span v-if="isFull(activity)" class="badge badge-closed">Complet</span>
            <span v-else-if="isDeadlinePassed(activity)" class="badge badge-closed">Inscriptions closes</span>
            <template v-else>
              <span v-if="activity.max_participants > 0" class="badge badge-open">
                {{ activity.max_participants - (activity.current_participants || 0) }} place(s)
              </span>
              <span v-if="activity.registration_deadline" class="badge badge-deadline">
                Avant le {{ formatDate(activity.registration_deadline) }}
              </span>
            </template>
          </div>
        </label>
      </fieldset>

      <div class="step-actions">
        <!-- type="button" impératif : sans lui le bouton vaut submit, donc
             `prevStep` était immédiatement annulé par le `nextStep` du form. -->
        <button type="button" @click="prevStep">Précédent</button>
        <button type="submit">Suivant</button>
      </div>
    </form>
    <MessageModal
      :visible="isAdhesionWarningVisible"
      message="Sélectionnez le montant de l'adhésion avant de continuer : elle est obligatoire pour toute inscription, même sans activité."
      title="Adhésion obligatoire"
      variant="warning"
      @close="isAdhesionWarningVisible = false"
    />
  </div>
</template>

<script lang="ts" setup>
import {ref, onMounted, computed, watch} from 'vue';
import {useFormStore} from '@/stores/form';
import api from '@/api';
import type {Activity} from '@/types';
import { activityPrice } from '@/pricing';
import { hasDocument, documentUrl } from '@/documents';
import { formatSchedule, groupByDay } from '@/schedule';
import { errorDetail } from '@/errors';
import MessageModal from '../MessageModal.vue';

const store = useFormStore();
const formData = store.formData;

const allActivities = ref<Activity[]>([]);
const loadingActivities = ref(true);
const activitiesError = ref<string | null>(null);
const selectedActivityIds = ref<number[]>([]);
const isAdhesionWarningVisible = ref(false);

const adherentAge = computed<number>(() => {
  if (!formData.date_naissance) return 0;
  const birthDate = new Date(formData.date_naissance);
  const today = new Date();
  let age = today.getFullYear() - birthDate.getFullYear();
  const m = today.getMonth() - birthDate.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
    age--;
  }
  return age;
});

// Set initial adhesion amount for children if not already set
watch(adherentAge, (newAge) => {
  if (newAge !== null && newAge < 16 && formData.adhesion_amount === null) {
    formData.adhesion_amount = 8; // Default to 8€ for first child
  }
}, {immediate: true});

const filteredActivities = computed<Activity[]>(() => {
  if (adherentAge.value === null) return [];

  if (adherentAge.value < 16) {
    return allActivities.value.filter((activity: Activity) => activity.is_child_activity);
  } else {
    return allActivities.value.filter((activity: Activity) => activity.is_adult_activity);
  }
});

const activityGroups = computed(() => groupByDay(filteredActivities.value));

onMounted(async () => {
  try {
    loadingActivities.value = true;
    const response = await api.get('/api/activities');
    allActivities.value = response.data;

    // Now that allActivities is available, initialize selectedActivityIds
    if (formData.activities && Array.isArray(formData.activities)) {
      selectedActivityIds.value = formData.activities.map(activity => activity.id).filter(id => id !== null) as number[];
    }
  } catch (err) {
    activitiesError.value = errorDetail(err, 'Impossible de charger les activités.');
  } finally {
    loadingActivities.value = false;
  }
});

const updateStore = () => {
  formData.activities = allActivities.value.filter(activity => selectedActivityIds.value.includes(activity.id!));
}

const nextStep = () => {
  if (!formData.adhesion_amount) {
    isAdhesionWarningVisible.value = true;
    return;
  }
  updateStore(); // Commit changes to the store
  store.nextStep();
};

const prevStep = () => {
  updateStore(); // Commit changes to the store
  store.prevStep();
};

const isDeadlinePassed = (activity: Activity): boolean => {
  if (!activity.registration_deadline) return false;
  return new Date(activity.registration_deadline) < new Date(new Date().toDateString());
};

const isFull = (activity: Activity): boolean =>
  activity.max_participants > 0 && activity.current_participants >= activity.max_participants;

const isActivityUnavailable = (activity: Activity): boolean => {
  if (isFull(activity)) return true;
  return isDeadlinePassed(activity);
};

/** Lieu et horaire sur une seule ligne, l'un ou l'autre pouvant manquer. */
const activityContext = (activity: Activity): string =>
  [activity.location, formatSchedule(activity)].filter(Boolean).join(' · ');

const formatDate = (dateStr: string): string => {
  return new Date(dateStr).toLocaleDateString('fr-FR');
};

const getPrice = (activity: Activity) => activityPrice(activity, formData.ville);
</script>

<style scoped>
/* Groupe de jour : fieldset/legend plutôt qu'un div + titre, pour que le
   lecteur d'écran annonce le jour en entrant dans le groupe de cases. */
.day-group {
  border: none;
  padding: 0;
  margin: 0 0 1.5rem;
}

.day-group legend {
  padding: 0;
  margin-bottom: 0.5rem;
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-primary);
}

/* Une activité = une carte. La grille `auto 1fr auto` fixe les trois colonnes
   (case, contenu, méta) : leur alignement ne dépend plus de la longueur du nom,
   ce que l'ancien empilement d'inline-block en pourcentages ne garantissait pas. */
.activity-option {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 0.25rem 0.75rem;
  align-items: start;
  padding: 0.85rem 1rem;
  margin-bottom: 0.5rem;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  transition: border-color 0.15s ease, background-color 0.15s ease, box-shadow 0.15s ease;
}

.activity-option:hover:not(.unavailable) {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

/* Retour visuel de la sélection sur la carte entière, pas seulement la case. */
.activity-option:has(input:checked) {
  border-color: var(--color-primary);
  background: #f0f6ff;
}

.activity-option:focus-within {
  outline: 2px solid var(--color-primary-light);
  outline-offset: 2px;
}

.activity-checkbox {
  margin: 0.2rem 0 0;
}

.activity-main {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}

.activity-name {
  font-weight: 600;
  line-height: 1.3;
}

.activity-desc {
  font-size: 0.9rem;
  color: #555;
}

.activity-context {
  font-size: 0.85rem;
  color: #777;
}

.activity-document {
  font-size: 0.85rem;
  color: #b9770e;
}

/* Colonne droite : tarif puis statuts, alignés à droite et empilés. */
.activity-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.3rem;
  text-align: right;
  white-space: nowrap;
}

.activity-price {
  font-weight: 700;
  font-size: 1.05rem;
}

.badge {
  font-size: 0.75rem;
  padding: 0.15rem 0.5rem;
  border-radius: 10px;
  font-weight: 600;
}

.badge-open {
  background: #e8f5e9;
  color: #2e7d32;
}

.badge-closed {
  background: #ffebee;
  color: #c62828;
}

.badge-deadline {
  background: #fff8e1;
  color: #8d6e00;
}

.unavailable {
  background: #fafafa;
  color: #999;
  cursor: not-allowed;
}

.unavailable .activity-desc,
.unavailable .activity-context,
.unavailable .activity-document,
.unavailable .activity-price {
  color: #aaa;
}

.unavailable .activity-checkbox {
  cursor: not-allowed;
}

.step-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1.5rem;
}

/* Sous 768px la colonne méta n'a plus la place d'être à droite du contenu :
   elle passe sous le texte, en ligne, alignée sur la même indentation. */
@media (max-width: 768px) {
  .activity-option {
    grid-template-columns: auto 1fr;
  }

  .activity-meta {
    grid-column: 2;
    flex-direction: row;
    flex-wrap: wrap;
    align-items: center;
    justify-content: flex-start;
    margin-top: 0.35rem;
  }
}
</style>