<template>
  <div>
    <h1>Gérer les comptes administrateurs</h1>
    <button @click="showAddModal = true">Ajouter un administrateur</button>

    <table>
      <thead>
        <tr>
          <th>Nom d'utilisateur</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="admin in admins" :key="admin.id">
          <td>{{ admin.username }}</td>
          <td>
            <button @click="startEdit(admin)">Modifier</button>
            <button @click="deleteAdmin(admin.id)">Supprimer</button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Add/Edit Modal -->
    <div v-if="showAddModal || editingAdmin">
      <div class="modal">
        <h2>{{ editingAdmin ? 'Modifier' : 'Ajouter' }} un administrateur</h2>
        <form @submit.prevent="saveAdmin">
          <div>
            <label for="username">Nom d'utilisateur:</label>
            <input type="text" id="username" v-model="form.username" required />
          </div>
          <div>
            <label for="password">Mot de passe:</label>
            <input type="password" id="password" v-model="form.password" :required="!editingAdmin" />
            <small v-if="editingAdmin">Laissez vide pour ne pas changer</small>
          </div>
          <button type="submit">Enregistrer</button>
          <button @click="cancel">Annuler</button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getAdmins, createAdmin, updateAdmin, deleteAdmin as apiDeleteAdmin } from '@/api';
import type { AdminUser, AdminUserCreate } from '@/types';

const admins = ref<AdminUser[]>([]);
const showAddModal = ref(false);
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
  showAddModal.value = true;
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

async function deleteAdmin(id: number) {
  if (confirm("Êtes-vous sûr de vouloir supprimer cet administrateur ?")) {
    try {
      await apiDeleteAdmin(id);
      await fetchAdmins();
    } catch (error) {
      console.error("Erreur lors de la suppression de l'administrateur:", error);
      alert("Erreur lors de la suppression.");
    }
  }
}

function cancel() {
  showAddModal.value = false;
  editingAdmin.value = null;
  form.value.username = '';
  form.value.password = '';
}
</script>

<style scoped>
.modal {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: white;
  padding: 20px;
  border: 1px solid #ccc;
  z-index: 1000;
}
</style>
