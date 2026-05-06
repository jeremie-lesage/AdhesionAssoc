<template>
  <Dialog v-model:visible="dialogVisible" header="Choisir la méthode de paiement" modal :style="{ width: '400px' }">
    <p>Sélectionnez la méthode de paiement utilisée pour cette adhésion.</p>
    <div style="display: flex; justify-content: center; gap: 1rem; margin-top: 1.5rem;">
      <Button label="Chèque" icon="pi pi-money-bill" severity="info" @click="selectMethod('Chèque')" />
      <Button label="Virement" icon="pi pi-wallet" severity="success" @click="selectMethod('Virement')" />
      <Button label="Annuler" icon="pi pi-times" severity="secondary" @click="dialogVisible = false" />
    </div>
  </Dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'pay', method: 'Chèque' | 'Virement'): void
  (e: 'close'): void
}>()

const dialogVisible = computed({
  get: () => props.visible,
  set: (val: boolean) => {
    if (!val) emit('close')
  }
})

const selectMethod = (method: 'Chèque' | 'Virement') => {
  emit('pay', method)
}
</script>
