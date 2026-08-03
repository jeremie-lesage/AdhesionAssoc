<template>
  <div
    v-if="visible"
    class="modal-overlay"
    @click.self="close"
  >
    <div
      class="modal-content"
      :class="`variant-${variant}`"
      role="alertdialog"
      aria-modal="true"
      :aria-labelledby="visible ? titleId : undefined"
    >
      <div class="icon-container" aria-hidden="true">
        <span class="icon">{{ variant === 'error' ? '!' : variant === 'warning' ? '!' : 'i' }}</span>
      </div>
      <h3 :id="titleId">{{ title }}</h3>
      <p class="message">{{ message }}</p>
      <slot />
      <button ref="closeButton" type="button" class="close-button" @click="close">
        {{ closeLabel }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, useId, watch } from 'vue';

const props = withDefaults(defineProps<{
  visible: boolean,
  title?: string,
  message: string,
  variant?: 'info' | 'warning' | 'error',
  closeLabel?: string
}>(), {
  title: 'Information',
  variant: 'info',
  closeLabel: 'Fermer'
})

const emit = defineEmits<{
  (e: 'close'): void
}>()

const titleId = useId()
const closeButton = ref<HTMLButtonElement | null>(null)

const close = () => {
  emit('close')
}

// Échap ferme la modale, comme le ferait un alert() natif avec la touche Entrée.
const onKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape') close()
}

watch(() => props.visible, async (isVisible) => {
  if (isVisible) {
    window.addEventListener('keydown', onKeydown)
    await nextTick()
    closeButton.value?.focus()
  } else {
    window.removeEventListener('keydown', onKeydown)
  }
}, { immediate: true })

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
})
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
  max-width: 420px;
  width: 90%;
  --accent: var(--color-primary);
}

.modal-content.variant-warning {
  --accent: #b9770e;
}

.modal-content.variant-error {
  --accent: #c0392b;
}

.icon-container {
  margin-bottom: 1rem;
}

.icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  margin: 0 auto;
  border-radius: 50%;
  border: 2px solid var(--accent);
  color: var(--accent);
  font-size: 1.8rem;
  font-weight: bold;
  font-family: Georgia, 'Times New Roman', serif;
  line-height: 1;
}

h3 {
  margin: 0 0 0.75rem;
  color: var(--color-text);
}

.message {
  margin: 0 0 1.5rem;
  color: #666;
  line-height: 1.6;
  white-space: pre-line;
}

.close-button {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  background-color: var(--accent);
  color: white;
  transition: filter 0.2s;
}

.close-button:hover {
  filter: brightness(0.9);
}
</style>
