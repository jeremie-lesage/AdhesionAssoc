import { defineStore } from 'pinia';
import type {Activity} from "@/types.ts";

/**
 * Données du formulaire en cours de saisie. Volontairement distinct d'`Adhesion` :
 * les champs sont vides ou nuls tant que l'adhérent n'a pas rempli l'étape
 * correspondante, et `adhesion_selected` n'existe que côté formulaire.
 */
export interface FormData {
  email: string;
  telephone: string;
  nom: string;
  prenom: string;
  date_naissance: string;
  nom_rue: string;
  code_postal: string;
  ville: string;
  activities: Activity[];
  adhesion_amount: number | null;
  adhesion_selected: boolean;
  code: string | null;
  status: string;
}

const emptyFormData = (): FormData => ({
  email: '',
  telephone: '',
  nom: '',
  prenom: '',
  date_naissance: '',
  nom_rue: '',
  code_postal: '',
  ville: '',
  activities: [],
  adhesion_amount: null,
  adhesion_selected: false,
  code: null,
  status: 'pending',
});

export const useFormStore = defineStore('form', {
  state: () => ({
    step: 1,
    formData: emptyFormData(),
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
      this.formData = emptyFormData();
      this.lastGeneratedCode = null;
    },
    setFormData(data: Partial<FormData>) {
      this.formData = { ...this.formData, ...data };
      if (data.activities && Array.isArray(data.activities)) {
        this.formData.activities = data.activities;
      }
    },
    setFormDataForEdit(data: Partial<FormData>) {
      this.resetForm();
      this.formData = { ...this.formData, ...data };
      if (data.activities && Array.isArray(data.activities)) {
        this.formData.activities = data.activities;
      }
      this.step = 1;
    },
  },
});
