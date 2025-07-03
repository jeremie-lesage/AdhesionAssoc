<template>
  <div>
    <h2>Étape 3: Choix des Activités</h2>
    <form @submit.prevent="nextStep">
      <div>
        <label>
          <input type="checkbox" value="danse" v-model="formData.activites">
          Danse
        </label>
      </div>
      <div>
        <label>
          <input type="checkbox" value="gym" v-model="formData.activites">
          Gym
        </label>
      </div>
      <div>
        <label>
          <input type="checkbox" value="pilate" v-model="formData.activites">
          Pilate
        </label>
      </div>
      <button @click="prevStep">Précédent</button>
      <button type="submit">Suivant</button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { useFormStore } from '@/stores/form';

const store = useFormStore();
const formData = store.formData;

if (!formData.activites) {
  formData.activites = [];
}

const nextStep = () => {
  store.nextStep();
};

const prevStep = () => {
  store.prevStep();
};
</script>
