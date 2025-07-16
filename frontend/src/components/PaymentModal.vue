<template>
  <div v-if="visible" class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <h3>Choisir la méthode de paiement</h3>
      <p>Sélectionnez la méthode de paiement utilisée pour cette adhésion.</p>
      <div class="modal-actions">
        <button @click="selectMethod('Chèque')" class="payment-button cheque">Chèque</button>
        <button @click="selectMethod('Virement')" class="payment-button virement">Virement</button>
        <button @click="$emit('close')" class="payment-button cancel">Annuler</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'pay', method: 'Chèque' | 'Virement'): void
  (e: 'close'): void
}>()

const selectMethod = (method: 'Chèque' | 'Virement') => {
  emit('pay', method)
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
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
  text-align: center;
  max-width: 400px;
  width: 90%;
}

h3 {
  margin-top: 0;
  margin-bottom: 1rem;
}

p {
  margin-bottom: 2rem;
  color: #666;
}

.modal-actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
}

.payment-button {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
  color: white;
}

.cheque {
  background-color: #007bff;
}
.cheque:hover {
  background-color: #0056b3;
}

.virement {
  background-color: #28a745;
}
.virement:hover {
  background-color: #1e7e34;
}

.cancel {
  background-color: #6c757d;
}
.cancel:hover {
  background-color: #5a6268;
}
</style>
