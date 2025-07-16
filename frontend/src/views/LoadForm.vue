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
    <div v-if="recentCodes.length > 0" class="recent-codes">
      <h3>Codes récents</h3>
      <ul>
        <li v-for="recentCode in recentCodes" :key="recentCode">
          <a href="#" @click.prevent="useCode(recentCode)">{{ recentCode }}</a>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useFormStore } from '@/stores/form';
import { useRouter } from 'vue-router';
import api from "@/api.ts";

const store = useFormStore();
const router = useRouter();
const code = ref('');
const recentCodes = ref<string[]>([]);

onMounted(() => {
  const codes = localStorage.getItem('recentCodes');
  if (codes) {
    recentCodes.value = JSON.parse(codes);
  }
});

const useCode = (selectedCode: string) => {
  code.value = selectedCode;
};

const loadForm = async () => {
  try {
    const response = await api.get(`/api/adhesions/${code.value}`);
    if (response.data.status === 'validated') {
      alert('Ce formulaire a déjà été validé et ne peut plus être modifié.');
      return;
    }
    store.formData = response.data;
    store.formData.code = response.data.code; // Assurez-vous que le code est bien stocké
    router.push('/adhesion');
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
  display: inline-block;
  margin-right: 10px;
}
.recent-codes a {
  text-decoration: none;
  color: #007bff;
  cursor: pointer;
}
.recent-codes a:hover {
  text-decoration: underline;
}
</style>
