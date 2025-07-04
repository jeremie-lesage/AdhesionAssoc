<template>
  <div>
    <h2>Charger un formulaire existant</h2>
    <form @submit.prevent="loadForm">
      <div>
        <label for="code">Votre code d'accès:</label>
        <input type="text" id="code" v-model="code" required>
      </div>
      <button type="submit">Charger</button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useFormStore } from '@/stores/form';
import axios from 'axios';
import { useRouter } from 'vue-router';
import api from "@/api.ts";

const store = useFormStore();
const router = useRouter();
const code = ref('');

const loadForm = async () => {
  try {
    const response = await api.get(`/api/adhesions/${code.value}`);
    if (response.data.status === 'validated') {
      alert('Ce formulaire a déjà été validé et ne peut plus être modifié.');
      return;
    }
    store.formData = response.data;
    store.formData.code = response.data.code; // Assurez-vous que le code est bien stocké
    router.push('/');
  } catch (error) {
    console.error(error);
    alert('Code invalide ou formulaire non trouvé.');
  }
};
</script>
