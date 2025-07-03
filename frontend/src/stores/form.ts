import { defineStore } from 'pinia';

export const useFormStore = defineStore('form', {
  state: () => ({
    step: 1,
    formData: {
      email: '',
      nom: '',
      prenom: '',
      date_naissance: '',
      numero_rue: '',
      nom_rue: '',
      code_postal: '',
      ville: '',
      activites: [] as string[],
      code: null as string | null,
      status: 'pending' as string,
    },
    lastGeneratedCode: null as string | null, // Nouveau champ pour le code généré
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
        status: 'pending',
      };
      this.lastGeneratedCode = null;
    },
  },
});
