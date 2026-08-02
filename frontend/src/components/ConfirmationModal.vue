<template>
  <div v-if="visible" class="modal-overlay" @click.self="close">
    <div class="modal-content">
      <div class="icon-container">
        <svg class="success-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
          <circle class="success-icon__circle" cx="26" cy="26" r="25" fill="none"/>
          <path class="success-icon__check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
        </svg>
      </div>
      <h3>Demande enregistrée !</h3>
      <p>
        Votre demande a bien été enregistrée.
        <br>
        Un email vous sera envoyé dans les prochains jours pour confirmer l'inscription et le montant à régler.
      </p>
      <div class="code-section">
        <p>Pour toute modification, conservez votre code de dossier :</p>
        <p class="form-id"><strong>{{ formId }}</strong></p>
      </div>
      <div v-if="documents.length" class="documents-section">
        <p><strong>Documents à imprimer et signer</strong></p>
        <p class="documents-hint">
          À remplir et à remettre au responsable de l'activité lors de la première
          séance. Les liens figurent aussi dans l'email que vous allez recevoir.
        </p>
        <ul>
          <li v-for="activity in documents" :key="activity.id!">
            <a :href="documentUrl(activity)" target="_blank">{{ activity.name }}</a>
          </li>
        </ul>
      </div>
      <button @click="close" class="close-button">Fermer</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Activity } from '@/types';
import { documentUrl } from '@/documents';

withDefaults(defineProps<{
  visible: boolean,
  formId: string,
  documents?: Activity[]
}>(), { documents: () => [] })

const emit = defineEmits<{
  (e: 'close'): void
}>()

const close = () => {
  emit('close')
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  padding: 2rem 3rem;
  border-radius: 8px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
  text-align: center;
  max-width: 450px;
  width: 90%;
}

.icon-container {
  margin-bottom: 1.5rem;
}

.success-icon {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: block;
  stroke-width: 2;
  stroke: #4CAF50;
  stroke-miterlimit: 10;
  margin: 0 auto;
  box-shadow: inset 0px 0px 0px #4CAF50;
  animation: fill .4s ease-in-out .4s forwards, scale .3s ease-in-out .9s both;
}

.success-icon__circle {
  stroke-dasharray: 166;
  stroke-dashoffset: 166;
  stroke-width: 2;
  stroke-miterlimit: 10;
  stroke: #4CAF50;
  fill: #fff;
  animation: stroke 0.6s cubic-bezier(0.65, 0, 0.45, 1) forwards;
}

.success-icon__check {
  transform-origin: 50% 50%;
  stroke-dasharray: 48;
  stroke-dashoffset: 48;
  animation: stroke 0.3s cubic-bezier(0.65, 0, 0.45, 1) 0.8s forwards;
}

@keyframes stroke {
  100% {
    stroke-dashoffset: 0;
  }
}

@keyframes scale {
  0%, 100% {
    transform: none;
  }
  50% {
    transform: scale3d(1.1, 1.1, 1);
  }
}

@keyframes fill {
  100% {
    box-shadow: inset 0px 0px 0px 40px #4CAF50;
  }
}

h3 {
  margin-top: 0;
  margin-bottom: 1rem;
  color: #333;
}

p {
  margin-bottom: 1rem;
  color: #666;
  line-height: 1.6;
}

.code-section {
  margin: 1.5rem 0;
  padding: 1rem;
  background-color: #f2f2f2;
  border-radius: 4px;
}

.code-section p {
  margin: 0;
}

.documents-section {
  margin: 1.5rem 0;
  padding: 1rem;
  border-left: 4px solid #b9770e;
  background-color: #fdf6e3;
  text-align: left;
}

.documents-section p {
  margin: 0 0 0.5rem;
}

.documents-hint {
  font-size: 0.9rem;
}

.documents-section ul {
  margin: 0;
  padding-left: 1.2rem;
}

.form-id {
  font-size: 1.2rem;
  font-weight: bold;
  color: #333;
  background-color: #e0e0e0;
  padding: 0.5rem;
  border-radius: 4px;
  display: inline-block;
  letter-spacing: 2px;
  margin-top: 0.5rem;
}

.close-button {
  margin-top: 1rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  background-color: #4CAF50;
  color: white;
  transition: background-color 0.2s;
}

.close-button:hover {
  background-color: #45a049;
}
</style>
