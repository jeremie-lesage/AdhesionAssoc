<template>
  <div>
    <component :is="currentStepComponent" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useFormStore } from '@/stores/form';
import Etape1_Contact from '@/components/steps/Etape1_Contact.vue';
import Etape2_InfosPersonnelles from '@/components/steps/Etape2_InfosPersonnelles.vue';
import Etape3_Activites from '@/components/steps/Etape3_Activites.vue';
import Etape4_Resume from '@/components/steps/Etape4_Resume.vue';

const store = useFormStore();

const currentStepComponent = computed(() => {
  switch (store.step) {
    case 1:
      return Etape1_Contact;
    case 2:
      return Etape2_InfosPersonnelles;
    case 3:
      return Etape3_Activites;
    case 4:
      return Etape4_Resume;
    default:
      return Etape1_Contact;
  }
});
</script>