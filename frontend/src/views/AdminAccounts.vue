<template>
  <div style="max-width: 800px; margin: 1.5rem auto">
    <h1>Gérer les comptes administrateurs</h1>
    <Button label="Ajouter un administrateur" icon="pi pi-plus" @click="openAddModal" class="mb-3" />

    <DataTable :value="admins">
      <Column field="username" header="Nom d'utilisateur" />
      <Column header="Actions">
        <template #body="{ data }">
          <div style="display: flex; gap: 0.5rem">
            <Button label="Modifier" icon="pi pi-pencil" severity="info" size="small" @click="startEdit(data)" />
            <Button label="Supprimer" icon="pi pi-trash" severity="danger" size="small" @click="confirmDelete(data.id)" />
          </div>
        </template>
      </Column>
    </DataTable>

    <ConfirmDialog />

    <Dialog
      v-model:visible="showModal"
      :header="editingAdmin ? 'Modifier un administrateur' : 'Ajouter un administrateur'"
      modal
      :style="{ width: '400px' }"
    >
      <form @submit.prevent="saveAdmin" style="display: flex; flex-direction: column; gap: 1rem">
        <div>
          <label for="username" style="display: block; margin-bottom: 0.5rem; font-weight: bold">Nom d'utilisateur :</label>
          <InputText v-model="form.username" id="username" fluid required />
        </div>
        <div>
          <label for="password" style="display: block; margin-bottom: 0.5rem; font-weight: bold">Mot de passe :</label>
          <Password v-model="form.password" id="password" :feedback="false" fluid :required="!editingAdmin" />
          <small v-if="editingAdmin">Laissez vide pour ne pas changer</small>
        </div>
        <div style="display: flex; gap: 0.5rem; justify-content: flex-end">
          <Button label="Annuler" severity="secondary" @click="cancel" type="button" />
          <Button label="Enregistrer" type="submit" />
        </div>
      </form>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getAdmins, createAdmin, updateAdmin, deleteAdmin as apiDeleteAdmin } from '@/api';
import type { AdminUser, AdminUserCreate } from '@/types';
import { useConfirm } from 'primevue/useconfirm';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Button from 'primevue/button';
import Dialog from 'primevue/dialog';
import InputText from 'primevue/inputtext';
import Password from 'primevue/password';
import ConfirmDialog from 'primevue/confirmdialog';

const confirm = useConfirm();
const admins = ref<AdminUser[]>([]);
const showModal = ref(false);
const editingAdmin = ref<AdminUser | null>(null);
const form = ref<AdminUserCreate>({
  username: '',
  password: '',
});

onMounted(async () => {
  await fetchAdmins();
});

async function fetchAdmins() {
  try {
    admins.value = await getAdmins();
  } catch (error) {
    console.error("Erreur lors de la récupération des administrateurs:", error);
    alert("Impossible de charger les administrateurs.");
  }
}

function startEdit(admin: AdminUser) {
  editingAdmin.value = admin;
  form.value.username = admin.username;
  form.value.password = '';
  showModal.value = true;
}

async function saveAdmin() {
  try {
    if (editingAdmin.value) {
      await updateAdmin(editingAdmin.value.id, form.value);
    } else {
      await createAdmin(form.value);
    }
    await fetchAdmins();
    cancel();
  } catch (error) {
    console.error("Erreur lors de l'enregistrement de l'administrateur:", error);
    alert("Erreur lors de l'enregistrement.");
  }
}

function confirmDelete(id: number) {
  confirm.require({
    message: 'Êtes-vous sûr de vouloir supprimer cet administrateur ?',
    header: 'Confirmation de suppression',
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: 'Supprimer',
    rejectLabel: 'Annuler',
    acceptClass: 'p-button-danger',
    accept: async () => {
      try {
        await apiDeleteAdmin(id);
        await fetchAdmins();
      } catch (error) {
        console.error("Erreur lors de la suppression de l'administrateur:", error);
        alert("Erreur lors de la suppression.");
      }
    },
  });
}

function openAddModal() {
  editingAdmin.value = null;
  form.value.username = '';
  form.value.password = '';
  showModal.value = true;
}

function cancel() {
  showModal.value = false;
  editingAdmin.value = null;
  form.value.username = '';
  form.value.password = '';
}
</script>
