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
      activites: [] as number[],
      adhesion_amount: null as number | null,
      adhesion_selected: false,
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
        numero_rue: '',
        nom_rue: '',
        code_postal: '',
        ville: '',
        activites: [],
        adhesion_amount: null,
        adhesion_selected: false,
        code: null,
        status: 'pending',
      };
      this.lastGeneratedCode = null;
    },
  },
});
