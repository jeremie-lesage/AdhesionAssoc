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

const store = useFormStore();
const router = useRouter();
const code = ref('');

const loadForm = async () => {
  try {
    const response = await axios.get(`http://localhost:8000/api/adhesions/${code.value}`);
    store.formData = response.data;
    store.formData.code = response.data.code; // Stocker le code
    router.push('/adhesion');
  } catch (error) {
    console.error(error);
    alert('Code invalide ou formulaire non trouvé.');
  }
};
</script>
