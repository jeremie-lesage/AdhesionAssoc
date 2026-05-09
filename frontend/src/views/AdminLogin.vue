<template>
  <div class="login-page">
    <div class="login-card">
      <img src="@/assets/images/logo_foyer_rural.png" alt="Logo Foyer Rural" class="login-logo">
      <h1>Administration</h1>
      <p class="login-subtitle">Foyer Rural de Fauverney</p>
      <form @submit.prevent="login" style="display: flex; flex-direction: column; gap: 1rem;">
        <div>
          <label for="username" style="display: block; margin-bottom: 0.5rem; font-weight: 600;">Nom d'utilisateur</label>
          <InputText v-model="username" id="username" fluid />
        </div>
        <div>
          <label for="password" style="display: block; margin-bottom: 0.5rem; font-weight: 600;">Mot de passe</label>
          <Password v-model="password" id="password" :feedback="false" toggleMask fluid />
        </div>
        <Button label="Se connecter" :loading="loading" type="submit" fluid />
        <Message severity="error" v-if="error">{{ error }}</Message>
      </form>
      <div class="login-footer">
        <RouterLink to="/" class="back-link">← Retour à l'accueil</RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { RouterLink, useRouter } from 'vue-router';
import { login as apiLogin } from '@/api';
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
    router.push('/admin');
  } catch (err: any) {
    console.error("Login error:", err);
    error.value = err.response?.data?.detail || 'Erreur de connexion.';
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e8f0fe 0%, #f0f7ff 100%);
  padding: 1rem;
}

.login-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
  padding: 2.5rem 2rem;
  width: 100%;
  max-width: 400px;
  text-align: center;
}

.login-logo {
  max-width: 5rem;
  height: auto;
  margin-bottom: 0.75rem;
}

.login-card h1 {
  font-size: 1.5rem;
  color: var(--color-primary);
  margin: 0 0 0.25rem;
}

.login-subtitle {
  color: #888;
  font-size: 0.9rem;
  margin: 0 0 1.5rem;
}

.login-card form {
  text-align: left;
}

.login-footer {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
}

.back-link {
  color: var(--color-primary);
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 500;
}

.back-link:hover {
  text-decoration: underline;
}
</style>
