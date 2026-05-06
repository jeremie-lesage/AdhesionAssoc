<template>
  <div>
    <h2>Charger un formulaire existant</h2>
    <form @submit.prevent="loadForm">
      <div>
        <label for="code">Votre code d'accès:</label>
        <input type="text" id="code" v-model="code" required>
      </div>
      <button type="submit">Charger</button>
    </form>
    <div v-if="recentAdhesions.length > 0" class="recent-codes">
      <h3>Codes récents</h3>
      <ul>
        <li v-for="adhesion in recentAdhesions" :key="adhesion.code">
          <a href="#" @click.prevent="useCode(adhesion.code)">
            {{ adhesion.code }} - {{ adhesion.prenom }} {{ adhesion.nom }}
          </a>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from "@/api.ts";
import type { Adhesion } from '@/types';

const router = useRouter();
const code = ref('');
const recentAdhesions = ref<{ code: string; nom: string; prenom: string }[]>([]);

onMounted(async () => {
  const codesJson = localStorage.getItem('recentCodes');
  if (codesJson) {
    const codes: string[] = JSON.parse(codesJson);
    const adhesionPromises = codes.map(async (code) => {
      try {
        const response = await api.get<Adhesion>(`/api/adhesions/${code}`);
        return {
          code: response.data.code,
          nom: response.data.nom,
          prenom: response.data.prenom
        };
      } catch (error) {
        console.error(`Impossible de charger les détails pour le code ${code}`, error);
        return null;
      }
    });

    const results = await Promise.all(adhesionPromises);
    recentAdhesions.value = results.filter(Boolean) as typeof recentAdhesions.value;
  }
});

const useCode = (selectedCode: string) => {
  code.value = selectedCode;
};

const loadForm = async () => {
  if (!code.value) return;
  try {
    const response = await api.get(`/api/adhesions/${code.value}`);
    if (response.data.status === 'validated' || response.data.status === 'paid') {
      alert('Ce formulaire a déjà été finalisé et ne peut plus être modifié.');
      return;
    }
    router.push({ name: 'adhesion', query: { code: code.value } });
  } catch (error) {
    console.error(error);
    alert('Code invalide ou formulaire non trouvé.');
  }
};
</script>

<style scoped>
.recent-codes {
  margin-top: 20px;
}
.recent-codes ul {
  list-style: none;
  padding: 0;
}
.recent-codes li {
  margin-bottom: 8px;
}
.recent-codes a {
  text-decoration: none;
  color: #007bff;
  cursor: pointer;
  font-weight: bold;
}
.recent-codes a:hover {
  text-decoration: underline;
}
</style>
