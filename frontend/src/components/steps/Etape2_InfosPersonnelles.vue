<template>
  <div>
    <h2>Étape 2: Informations Personnelles</h2>
    <p v-if="locked" class="family-notice">
      Nouveau membre de la famille <strong>{{ formData.email }}</strong>.
      Les coordonnées ci-dessous sont celles de la famille et ne sont pas modifiables ici :
      pour les corriger, reprenez le formulaire du premier membre inscrit.
    </p>
    <form @submit.prevent="nextStep">
      <div>
        <label for="nom">Nom:</label>
        <input type="text" id="nom" v-model="formData.nom" required autocomplete="family-name">
      </div>
      <div>
        <label for="prenom">Prénom:</label>
        <input type="text" id="prenom" v-model="formData.prenom" required autocomplete="given-name">
      </div>
      <div>
        <label for="date_naissance">Date de Naissance:</label>
        <input type="date" id="date_naissance" ref="dateNaissanceInput" v-model="formData.date_naissance" required autocomplete="bday"
               min="1900-01-01" :max="todayStr" @input="dateNaissanceInput?.setCustomValidity('')">
        <!-- Indication seule : la catégorie ne filtre pas les activités de l'étape 3 -->
        <p v-if="membership" class="membership-badge" :class="`badge-${membership}`">
          {{ membershipLabel(membership) }}
        </p>
      </div>
      <div>
        <label for="telephone">Téléphone:</label>
        <input type="tel" id="telephone" ref="telInput" v-model="formData.telephone" autocomplete="tel" placeholder="06 12 34 56 78"
               :readonly="locked" @input="telInput?.setCustomValidity('')">
      </div>
      <div>
        <label for="nom_rue">Adresse:</label>
        <input type="text" id="nom_rue" v-model="formData.nom_rue" required autocomplete="address-line1" placeholder="Numéro et nom de rue"
               :readonly="locked">
      </div>
      <div>
        <label for="code_postal">Code Postal:</label>
        <input type="text" id="code_postal" ref="codePostalInput" v-model="formData.code_postal" required autocomplete="postal-code"
               maxlength="5" :readonly="locked" @input="onCodePostalInput">
      </div>
      <div>
        <label for="ville">Ville:</label>
        <!-- `readonly` et non `disabled` : la valeur reste soumise et la contrainte
             `required` continue d'être satisfaite. Un `<select>` n'accepte pas
             `readonly`, d'où le champ texte figé en mode famille. -->
        <input v-if="locked" type="text" id="ville" v-model="formData.ville" required readonly>
        <select v-else-if="communes.length > 0" id="ville" v-model="formData.ville" required>
          <option value="" disabled>— Sélectionnez une commune —</option>
          <option v-for="commune in communes" :key="commune" :value="commune">{{ commune }}</option>
        </select>
        <input v-else type="text" id="ville" v-model="formData.ville" required autocomplete="address-level2">
      </div>
      <button v-if="!locked" @click="prevStep">Précédent</button>
      <button type="submit">Suivant</button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useFormStore } from '@/stores/form';
import { membershipCategory, membershipLabel } from '@/age';
import api from '@/api';

const store = useFormStore();
const formData = store.formData;
// Ajout d'un membre à une famille : coordonnées figées, pas d'étape 1 en arrière.
const locked = computed(() => store.familyLocked);
const telInput = ref<HTMLInputElement | null>(null);
const dateNaissanceInput = ref<HTMLInputElement | null>(null);
const codePostalInput = ref<HTMLInputElement | null>(null);
const postalCodePrefix = ref('');
// Défaut aligné sur `settings.ADULT_AGE_THRESHOLD`, remplacé par /api/config.
const adultAgeThreshold = ref(16);
const communes = ref<string[]>([]);
const todayStr = new Date().toISOString().split('T')[0];

const membership = computed(() =>
  membershipCategory(formData.date_naissance, adultAgeThreshold.value),
);

const communesCache: Record<string, string[]> = {};

const fetchCommunes = async (codePostal: string) => {
  if (communesCache[codePostal]) {
    communes.value = communesCache[codePostal];
    autoSelectIfSingle();
    return;
  }

  const stored = localStorage.getItem(`cp_${codePostal}`);
  if (stored) {
    const parsed = JSON.parse(stored) as string[];
    communesCache[codePostal] = parsed;
    communes.value = parsed;
    autoSelectIfSingle();
    return;
  }

  try {
    const res = await fetch(`https://geo.api.gouv.fr/communes?codePostal=${codePostal}&fields=nom`);
    if (res.ok) {
      const data = await res.json() as { nom: string }[];
      const noms = data.map(c => c.nom).sort();
      communesCache[codePostal] = noms;
      localStorage.setItem(`cp_${codePostal}`, JSON.stringify(noms));
      communes.value = noms;
      autoSelectIfSingle();
    }
  } catch {
    communes.value = [];
  }
};

const autoSelectIfSingle = () => {
  if (communes.value.length === 1) {
    formData.ville = communes.value[0];
  } else if (!communes.value.includes(formData.ville)) {
    formData.ville = '';
  }
};

const onCodePostalInput = () => {
  codePostalInput.value?.setCustomValidity('');
  if (formData.code_postal.length === 5 && /^\d{5}$/.test(formData.code_postal)) {
    fetchCommunes(formData.code_postal);
  } else {
    communes.value = [];
  }
};

onMounted(async () => {
  try {
    const res = await api.get('/api/config');
    postalCodePrefix.value = res.data.postal_code_prefix;
    if (typeof res.data.adult_age_threshold === 'number') {
      adultAgeThreshold.value = res.data.adult_age_threshold;
    }
  } catch {
    // Pas de restriction si la config n'est pas disponible ; le seuil garde son défaut
  }

  // En mode famille, la ville est imposée : charger la liste des communes ne
  // servirait à rien et `autoSelectIfSingle` risquerait de l'effacer.
  if (!locked.value && formData.code_postal.length === 5 && /^\d{5}$/.test(formData.code_postal)) {
    fetchCommunes(formData.code_postal);
  }
});

const telPattern = /^(\+33|0)[1-9]\d{8}$/;

const nextStep = () => {
  for (const key of ['nom', 'prenom', 'nom_rue', 'code_postal', 'ville', 'telephone'] as const) {
    if (formData[key]) formData[key] = formData[key].trim();
  }
  if (formData.date_naissance) {
    const year = new Date(formData.date_naissance).getFullYear();
    if (year < 1900 || year > new Date().getFullYear()) {
      dateNaissanceInput.value?.setCustomValidity('Veuillez saisir une date de naissance valide (année entre 1900 et aujourd\'hui)');
      dateNaissanceInput.value?.reportValidity();
      return;
    }
  }
  if (postalCodePrefix.value && formData.code_postal && !formData.code_postal.startsWith(postalCodePrefix.value)) {
    codePostalInput.value?.setCustomValidity(`Le code postal doit commencer par ${postalCodePrefix.value}`);
    codePostalInput.value?.reportValidity();
    return;
  }
  if (formData.telephone) {
    const cleaned = formData.telephone.replace(/[\s.\-]/g, '');
    if (!telPattern.test(cleaned)) {
      telInput.value?.setCustomValidity('Veuillez saisir un numéro de téléphone valide (ex: 06 12 34 56 78)');
      telInput.value?.reportValidity();
      return;
    }
    formData.telephone = cleaned;
  }
  formData.nom = formData.nom.toLocaleUpperCase('fr-FR');
  formData.prenom = formData.prenom
    .toLocaleLowerCase('fr-FR')
    .replace(/(^|[\s\-])(\S)/g, (_m, sep, c) => sep + c.toLocaleUpperCase('fr-FR'));
  store.nextStep();
};

const prevStep = () => {
  store.prevStep();
};
</script>

<style scoped>
/* Même palette que les badges Enfant/Adulte de HomeView, pour que la catégorie
   se lise pareil d'un écran à l'autre. */
.family-notice {
  background-color: #e7f3fe;
  border-left: 6px solid #2196F3;
  padding: 1rem;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

input[readonly] {
  background-color: #f4f4f4;
  color: #555;
  cursor: not-allowed;
}

.membership-badge {
  display: inline-block;
  margin: 0.5rem 0 0;
  padding: 0.2rem 0.6rem;
  border-radius: 10px;
  font-size: 0.8rem;
  font-weight: 600;
}

.badge-child {
  background: #e8f5e9;
  color: #2e7d32;
}

.badge-adult {
  background: #e3f2fd;
  color: #1565c0;
}

select {
  width: calc(100% - 1.5rem);
  padding: 0.8rem;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 1rem;
  box-sizing: border-box;
  background-color: white;
}
</style>
