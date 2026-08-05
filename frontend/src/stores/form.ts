import { defineStore } from 'pinia';
import type {Activity} from "@/types.ts";
import type {FamilyContact} from "@/family.ts";

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
    /**
     * Vrai quand on ajoute un membre à une famille existante : les coordonnées
     * viennent du premier membre et ne sont plus modifiables, l'étape 1 (contact)
     * n'a plus lieu d'être. Volontairement hors de `formData`, qui part telle
     * quelle vers l'API : un drapeau d'affichage n'a rien à y faire.
     */
    familyLocked: false,
  }),
  getters: {
    /** Première étape atteignable : l'étape 1 disparaît en mode famille. */
    minStep: (state) => (state.familyLocked ? 2 : 1),
  },
  actions: {
    nextStep() {
      if (this.step < 4) {
        this.step++;
      }
    },
    prevStep() {
      if (this.step > this.minStep) {
        this.step--;
      }
    },
    resetForm() {
      this.step = 1;
      this.formData = emptyFormData();
      this.lastGeneratedCode = null;
      this.familyLocked = false;
    },
    /**
     * Démarre l'inscription d'un nouveau membre dans une famille existante :
     * formulaire vierge, coordonnées recopiées et verrouillées, saisie à l'étape 2.
     * Pas de `code` : c'est bien une création, pas la reprise d'une adhésion.
     */
    startFamilyMember(contact: FamilyContact) {
      this.resetForm();
      this.formData = { ...this.formData, ...contact };
      this.familyLocked = true;
      this.step = 2;
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
