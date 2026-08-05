<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { useFormStore } from '@/stores/form';
import { getAdhesionByCode } from '@/api';
import { familyContact } from '@/family';
import FormStepper from '@/components/FormStepper.vue';
import Etape1_Contact from '@/components/steps/Etape1_Contact.vue';
import Etape2_InfosPersonnelles from '@/components/steps/Etape2_InfosPersonnelles.vue';
import Etape3_Activites from '@/components/steps/Etape3_Activites.vue';
import Etape4_Resume from '@/components/steps/Etape4_Resume.vue';

const store = useFormStore();
const route = useRoute();
const isLoading = ref(false);

const allStepLabels = ['Contact', 'Informations personnelles', 'Activités', 'Récapitulatif'];

/**
 * Le stepper numérote ses entrées par leur position. En mode famille, l'étape 1
 * n'est pas affichée : il faut donc traduire l'étape du store en position dans la
 * liste réduite, et l'inverse à la navigation.
 */
const stepOffset = computed(() => store.minStep - 1);
const stepLabels = computed(() => allStepLabels.slice(stepOffset.value));
const stepperStep = computed(() => store.step - stepOffset.value);

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

const onNavigate = (position: number) => {
  const target = position + stepOffset.value;
  if (target < store.step) {
    store.step = target;
  }
};

onMounted(async () => {
  const code = route.query.code as string;
  const source = route.query.source as string;
  // Code du membre de référence d'une famille : on repart d'un formulaire vierge
  // dont seules les coordonnées sont recopiées, pas une reprise de cette adhésion.
  const family = route.query.family as string;

  if (family) {
    isLoading.value = true;
    try {
      const reference = await getAdhesionByCode(family);
      store.startFamilyMember(familyContact(reference));
    } catch (error) {
      // Sans les coordonnées de référence, le formulaire complet reste utilisable.
      console.error("Failed to load family reference:", error);
      store.resetForm();
    } finally {
      isLoading.value = false;
    }
  } else if (code) {
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
  <div class="public-view form-layout">
    <aside class="form-sidebar">
      <FormStepper :steps="stepLabels" :current-step="stepperStep" @navigate="onNavigate" />
    </aside>
    <main class="form-content">
      <div v-if="isLoading">Chargement du formulaire...</div>
      <component v-else :is="currentStepComponent" />
    </main>
  </div>
</template>

<style scoped>
.form-layout {
  display: flex;
  gap: 2rem;
  align-items: flex-start;
}

.form-sidebar {
  flex-shrink: 0;
  position: sticky;
  top: 1rem;
}

.form-content {
  flex: 1;
  min-width: 0;
}

@media (max-width: 768px) {
  .form-layout {
    flex-direction: column;
    gap: 0;
  }

  .form-sidebar {
    position: static;
    width: 100%;
  }
}
</style>
