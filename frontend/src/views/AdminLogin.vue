<template>
  <Card style="max-width: 400px; margin: 50px auto">
    <template #title>Connexion Administrateur</template>
    <template #content>
      <form @submit.prevent="login" style="display: flex; flex-direction: column; gap: 1rem">
        <div>
          <label for="username" style="display: block; margin-bottom: 0.5rem; font-weight: bold">Nom d'utilisateur :</label>
          <InputText v-model="username" id="username" fluid />
        </div>
        <div>
          <label for="password" style="display: block; margin-bottom: 0.5rem; font-weight: bold">Mot de passe :</label>
          <Password v-model="password" id="password" :feedback="false" toggleMask fluid />
        </div>
        <Button label="Se connecter" :loading="loading" type="submit" fluid />
        <Message severity="error" v-if="error">{{ error }}</Message>
      </form>
    </template>
  </Card>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { login as apiLogin } from '@/api';
import Card from 'primevue/card';
import InputText from 'primevue/inputtext';
import Password from 'primevue/password';
import Button from 'primevue/button';
import Message from 'primevue/message';

const username = ref('');
const password = ref('');
const loading = ref(false);
const error = ref<string | null>(null);
const router = useRouter();

const login = async () => {
  loading.value = true;
  error.value = null;
  try {
    await apiLogin({
      username: username.value,
      password: password.value,
    });
    router.push('/admin'); // Redirect to admin dashboard
  } catch (err: any) {
    console.error("Login error:", err);
    error.value = err.response?.data?.detail || 'Erreur de connexion.';
  } finally {
    loading.value = false;
  }
};
</script>
