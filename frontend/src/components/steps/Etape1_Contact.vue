<template>
  <div>
    <h2>Étape 1: Contact</h2>
    <p class="info-text">
      Vous devez faire une demande d'adhésion par personne, mais nous vous recommandons d'utiliser la même adresse email de contact pour chaque membre d'une même famille.
    </p>
    <form @submit.prevent="nextStep">
      <div>
        <label for="email">Adresse Email de contact:</label>
        <input type="email" id="email" v-model="email" required autocomplete="email">
      </div>
      <button type="submit">Suivant</button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useFormStore } from '@/stores/form';

const store = useFormStore();
const email = ref(store.formData.email);

const nextStep = () => {
  store.formData.email = email.value;
  store.nextStep();
};
</script>

<style scoped>
.info-text {
  background-color: #e7f3fe;
  border-left: 6px solid #2196F3;
  padding: 1rem;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}
</style>
