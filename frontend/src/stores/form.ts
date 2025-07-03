import { defineStore } from 'pinia';

export const useFormStore = defineStore('form', {
  state: () => ({
    step: 1,
    formData: {
      email: '',
      nom: '',
      prenom: '',
      date_naissance: '',
      adresse_postale: '',
      activites: [] as string[],
      code: null as string | null,
    },
  }),
  actions: {
    nextStep() {
      if (this.step < 4) {
        this.step++;
      }
    },
    prevStep() {
      if (this.step > 1) {
        this.step--;
      }
    },
    resetForm() {
      this.step = 1;
      this.formData = {
        email: '',
        nom: '',
        prenom: '',
        date_naissance: '',
        adresse_postale: '',
        activites: [],
        code: null,
      };
    },
  },
});
