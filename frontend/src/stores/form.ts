import { defineStore } from 'pinia';
import type {Activity} from "@/types.ts";

export const useFormStore = defineStore('form', {
  state: () => ({
    step: 1,
    formData: {
      email: '',
      telephone: '',
      nom: '',
      prenom: '',
      date_naissance: '',
      numero_rue: '',
      nom_rue: '',
      code_postal: '',
      ville: '',
      activities: [] as Activity[],
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
        telephone: '',
        nom: '',
        prenom: '',
        date_naissance: '',
        numero_rue: '',
        nom_rue: '',
        code_postal: '',
        ville: '',
        activities: [],
        adhesion_amount: null,
        adhesion_selected: false,
        code: null,
        status: 'pending',
      };
      this.lastGeneratedCode = null;
    },
    setFormData(data: any) {
      this.formData = { ...this.formData, ...data };
      if (data.activities && Array.isArray(data.activities)) {
        this.formData.activities = data.activities;
      }
    },
    setFormDataForEdit(data: any) {
      this.resetForm();
      this.formData = { ...this.formData, ...data };
      if (data.activities && Array.isArray(data.activities)) {
        this.formData.activities = data.activities;
      }
      this.step = 1;
    },
  },
});
