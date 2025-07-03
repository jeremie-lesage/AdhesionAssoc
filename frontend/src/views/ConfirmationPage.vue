<template>
  <div>
    <h2>Confirmation de votre demande d'adhésion</h2>
    <p>Votre demande d'adhésion a été enregistrée avec succès !</p>
    <p>Votre code d'accès unique est : <strong>{{ formStore.lastGeneratedCode }}</strong></p>
    <p>
      Veuillez conserver ce code précieusement. Il vous permettra de recharger et de modifier votre demande ultérieurement,
      tant qu'elle n'a pas été validée par l'association.
    </p>
    <p>
      Une confirmation de votre inscription, incluant ce code, vous sera envoyée par email à l'adresse que vous avez fournie.
    </p>
    <button @click="goToHome">Nouvelle demande</button>
  </div>
</template>

<script setup lang="ts">
import { useFormStore } from '@/stores/form';
import { useRouter } from 'vue-router';

const formStore = useFormStore();
const router = useRouter();

const goToHome = () => {
  formStore.resetForm();
  router.push('/');
};
</script>
