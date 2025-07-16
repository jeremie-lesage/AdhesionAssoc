<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { useFormStore } from '@/stores/form';
import { getAdhesionByCode } from '@/api';
import Etape1_Contact from '@/components/steps/Etape1_Contact.vue';
import Etape2_InfosPersonnelles from '@/components/steps/Etape2_InfosPersonnelles.vue';
import Etape3_Activites from '@/components/steps/Etape3_Activites.vue';
import Etape4_Resume from '@/components/steps/Etape4_Resume.vue';

const store = useFormStore();
const route = useRoute();
const isLoading = ref(false);

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

onMounted(async () => {
  const code = route.query.code as string;
  const source = route.query.source as string;

  if (code) {
    isLoading.value = true;
    try {
      const adhesion = await getAdhesionByCode(code);
      if (source === 'admin') {
        store.setFormDataForEdit(adhesion);
      } else {
        store.setFormData(adhesion);
      }
    } catch (error) {
      console.error("Failed to load adhesion data:", error);
    } finally {
      isLoading.value = false;
    }
  } else {
    store.resetForm();
  }
});
</script>

<template>
  <div>
    <div v-if="isLoading">Chargement du formulaire...</div>
    <component v-else :is="currentStepComponent" />
  </div>
</template>