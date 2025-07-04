<template>
  <div>
    <h2>Étape 1: Contact</h2>
    <form @submit.prevent="nextStep">
      <div>
        <label for="email">Adresse Email:</label>
        <input type="email" id="email" v-model="formData.email" required autocomplete="email">
      </div>
      <button type="submit">Suivant</button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { useFormStore } from '@/stores/form';

const store = useFormStore();
const formData = store.formData;

const nextStep = () => {
  store.nextStep();
};
</script>
