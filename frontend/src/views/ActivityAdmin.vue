<template>
  <div>
    <h2>Administration des Activités</h2>

    <div style="display: flex; justify-content: flex-end; margin-bottom: 1rem;">
      <Button label="Ajouter une activité" icon="pi pi-plus" @click="openDialog()" />
    </div>

    <p v-if="loading">Chargement des activités...</p>
    <p v-if="error">Erreur lors du chargement des activités: {{ error }}</p>
    <DataTable v-if="activities.length" :value="activities" stripedRows sortField="name" :sortOrder="1">
      <Column field="name" header="Nom" sortable />
      <Column field="description" header="Description" />
      <Column header="Horaire" sortable sortField="day_of_week">
        <template #body="{ data }">
          <template v-if="data.day_of_week != null">
            {{ dayLabels[data.day_of_week] }}
            <span v-if="data.start_time"> {{ data.start_time.substring(0, 5) }}<span v-if="data.end_time"> – {{ data.end_time.substring(0, 5) }}</span></span>
          </template>
          <span v-else>—</span>
        </template>
      </Column>
      <Column field="location" header="Lieu" sortable />
      <Column field="resident_price" header="Tarif Résident" sortable>
        <template #body="{ data }">{{ data.resident_price }} €</template>
      </Column>
      <Column field="external_price" header="Tarif Extérieur" sortable>
        <template #body="{ data }">{{ data.external_price }} €</template>
      </Column>
      <Column field="is_child_activity" header="Enfant" sortable>
        <template #body="{ data }">{{ data.is_child_activity ? 'Oui' : 'Non' }}</template>
      </Column>
      <Column field="is_adult_activity" header="Adulte" sortable>
        <template #body="{ data }">{{ data.is_adult_activity ? 'Oui' : 'Non' }}</template>
      </Column>
      <Column header="Inscrits / Places">
        <template #body="{ data }">
          <span v-if="data.max_participants > 0">{{ data.current_participants }} / {{ data.max_participants }}</span>
          <span v-else>Illimité</span>
        </template>
      </Column>
      <Column field="registration_deadline" header="Date limite" sortable>
        <template #body="{ data }">
          <span v-if="data.registration_deadline">{{ new Date(data.registration_deadline).toLocaleDateString('fr-FR') }}</span>
          <span v-else>—</span>
        </template>
      </Column>
      <Column header="Actions">
        <template #body="{ data }">
          <Button icon="pi pi-pencil" severity="info" text rounded size="small" @click="openDialog(data)" />
          <Button icon="pi pi-trash" severity="danger" text rounded size="small" @click="deleteActivity(data.id)" />
        </template>
      </Column>
    </DataTable>
    <p v-else-if="!loading && !error">Aucune activité définie.</p>

    <Dialog v-model:visible="dialogVisible" :header="isEditing ? 'Modifier une activité' : 'Ajouter une activité'" modal :style="{ width: '500px' }">
      <form @submit.prevent="isEditing ? updateActivity() : addActivity()" style="display: flex; flex-direction: column; gap: 1rem;">
        <div style="display: flex; flex-direction: column; gap: 0.5rem;">
          <label for="name">Nom de l'activité:</label>
          <InputText id="name" v-model="editingActivity.name" placeholder="Nom de l'activité" required />
        </div>
        <div style="display: flex; flex-direction: column; gap: 0.5rem;">
          <label for="description">Description:</label>
          <Textarea id="description" v-model="editingActivity.description" placeholder="Description" rows="3" />
        </div>
        <div style="display: flex; flex-direction: column; gap: 0.5rem;">
          <label for="location">Lieu (École ou Foyer):</label>
          <InputText id="location" v-model="editingActivity.location" placeholder="Lieu (École ou Foyer)" />
        </div>
        <div style="display: flex; flex-direction: column; gap: 0.5rem;">
          <label for="resident_price">Tarif Résident:</label>
          <InputNumber id="resident_price" v-model="editingActivity.resident_price" mode="currency" currency="EUR" locale="fr-FR" />
        </div>
        <div style="display: flex; flex-direction: column; gap: 0.5rem;">
          <label for="external_price">Tarif Extérieur:</label>
          <InputNumber id="external_price" v-model="editingActivity.external_price" mode="currency" currency="EUR" locale="fr-FR" />
        </div>
        <div style="display: flex; flex-direction: column; gap: 0.5rem;">
          <label for="max_participants">Nombre de places disponibles:</label>
          <InputNumber id="max_participants" v-model="editingActivity.max_participants" :min="0" />
        </div>
        <div style="display: flex; flex-direction: column; gap: 0.5rem;">
          <label for="registration_deadline">Date limite d'inscription:</label>
          <DatePicker id="registration_deadline" :modelValue="deadlineAsDate" @update:modelValue="onDeadlineChange" dateFormat="dd/mm/yy" showIcon showButtonBar />
        </div>
        <div style="display: flex; flex-direction: column; gap: 0.5rem;">
          <label for="day_of_week">Jour de la semaine:</label>
          <Select id="day_of_week" v-model="editingActivity.day_of_week" :options="dayOptions" optionLabel="label" optionValue="value" placeholder="— Aucun —" showClear />
        </div>
        <div style="display: flex; gap: 1rem;">
          <div style="display: flex; flex-direction: column; gap: 0.5rem; flex: 1;">
            <label for="start_time">Heure début:</label>
            <InputText id="start_time" v-model="editingActivity.start_time" type="time" />
          </div>
          <div style="display: flex; flex-direction: column; gap: 0.5rem; flex: 1;">
            <label for="end_time">Heure fin:</label>
            <InputText id="end_time" v-model="editingActivity.end_time" type="time" />
          </div>
        </div>
        <div style="display: flex; gap: 2rem; align-items: center;">
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <Checkbox inputId="is_child" v-model="editingActivity.is_child_activity" binary />
            <label for="is_child">Activité Enfant</label>
          </div>
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <Checkbox inputId="is_adult" v-model="editingActivity.is_adult_activity" binary />
            <label for="is_adult">Activité Adulte</label>
          </div>
        </div>
        <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
          <Button :label="isEditing ? 'Modifier' : 'Ajouter'" :icon="isEditing ? 'pi pi-check' : 'pi pi-plus'" type="submit" />
          <Button label="Annuler" icon="pi pi-times" severity="secondary" type="button" @click="dialogVisible = false" />
        </div>
      </form>
    </Dialog>

    <ConfirmDialog />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, type Ref } from 'vue';
import api from '@/api';
import { useRouter } from 'vue-router';
import { useConfirm } from 'primevue/useconfirm';
import type { Activity } from '@/types';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import InputText from 'primevue/inputtext';
import Textarea from 'primevue/textarea';
import InputNumber from 'primevue/inputnumber';
import Checkbox from 'primevue/checkbox';
import Button from 'primevue/button';
import Dialog from 'primevue/dialog';
import DatePicker from 'primevue/datepicker';
import Select from 'primevue/select';
import ConfirmDialog from 'primevue/confirmdialog';

const dayLabels = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'];

const dayOptions = [
  { label: 'Lundi', value: 0 },
  { label: 'Mardi', value: 1 },
  { label: 'Mercredi', value: 2 },
  { label: 'Jeudi', value: 3 },
  { label: 'Vendredi', value: 4 },
  { label: 'Samedi', value: 5 },
  { label: 'Dimanche', value: 6 },
];

const confirm = useConfirm();
const activities = ref<Activity[]>([]);
const dialogVisible = ref(false);
const editingActivity: Ref<Activity> = ref({
  id: null,
  name: '',
  description: '',
  location: '',
  resident_price: undefined,
  external_price: undefined,
  is_child_activity: false,
  is_adult_activity: false,
  max_participants: 0,
  current_participants: 0,
  registration_deadline: null,
  day_of_week: null,
  start_time: null,
  end_time: null,
  document_filename: null,
});
const isEditing = ref(false);

const deadlineAsDate = computed<Date | null>(() => {
  if (!editingActivity.value.registration_deadline) return null;
  return new Date(editingActivity.value.registration_deadline);
});

const onDeadlineChange = (value: Date | Date[] | (Date | null)[] | null | undefined) => {
  if (!value || Array.isArray(value)) {
    editingActivity.value.registration_deadline = null;
  } else {
    const d = new Date(value);
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    editingActivity.value.registration_deadline = d.toISOString().split('T')[0];
  }
};

const loading = ref(true);
const error = ref(null);
const router = useRouter();

const openDialog = (activity?: Activity) => {
  if (activity) {
    editingActivity.value = { ...activity };
    isEditing.value = true;
  } else {
    resetForm();
  }
  dialogVisible.value = true;
};

const fetchActivities = async () => {
  loading.value = true;
  error.value = null;
  try {
    const response = await api.get('/api/activities');
    activities.value = response.data;
  } catch (err: any) {
    if (err.response && err.response.status === 401) {
      router.push({ name: 'admin-login' });
    } else {
      error.value = err.message;
    }
  } finally {
    loading.value = false;
  }
};

const addActivity = async () => {
  try {
    await api.post('/api/activities', editingActivity.value);
    dialogVisible.value = false;
    resetForm();
    fetchActivities();
  } catch (err: any) {
    alert(`Erreur lors de l'ajout de l'activité: ${err.response?.data?.detail || err.message}`);
    if (err.response && err.response.status === 401) {
      router.push({ name: 'admin-login' });
    }
  }
};

const updateActivity = async () => {
  try {
    await api.put(`/api/activities/${editingActivity.value.id}`, editingActivity.value);
    dialogVisible.value = false;
    resetForm();
    fetchActivities();
  } catch (err: any) {
    alert(`Erreur lors de la mise à jour de l'activité: ${err.response?.data?.detail || err.message}`);
    if (err.response && err.response.status === 401) {
      router.push({ name: 'admin-login' });
    }
  }
};

const resetForm = () => {
  editingActivity.value = {
    id: null,
    name: '',
    description: '',
    location: '',
    resident_price: undefined,
    external_price: undefined,
    is_child_activity: false,
    is_adult_activity: false,
    max_participants: 0,
    current_participants: 0,
    registration_deadline: null,
    day_of_week: null,
    start_time: null,
    end_time: null,
    document_filename: null,
  };
  isEditing.value = false;
};

const deleteActivity = (id: number | null) => {
  confirm.require({
    message: 'Êtes-vous sûr de vouloir supprimer cette activité ?',
    header: 'Confirmation',
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: 'Supprimer',
    rejectLabel: 'Annuler',
    acceptClass: 'p-button-danger',
    accept: async () => {
      try {
        await api.delete(`/api/activities/${id}`);
        fetchActivities();
      } catch (err: any) {
        alert(`Erreur lors de la suppression de l'activité: ${err.response?.data?.detail || err.message}`);
        if (err.response && err.response.status === 401) {
          router.push({ name: 'admin-login' });
        }
      }
    },
  });
};

onMounted(fetchActivities);
</script>
