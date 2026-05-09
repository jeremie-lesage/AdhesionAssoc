<template>
  <div class="stepper">
    <div
      v-for="(step, index) in steps"
      :key="index"
      class="stepper-item"
      :class="{
        active: currentStep === index + 1,
        completed: currentStep > index + 1,
        clickable: currentStep > index + 1,
      }"
      @click="goToStep(index + 1)"
    >
      <div class="stepper-indicator">
        <span v-if="currentStep > index + 1" class="stepper-check">✓</span>
        <span v-else>{{ index + 1 }}</span>
      </div>
      <div class="stepper-label">{{ step }}</div>
      <div v-if="index < steps.length - 1" class="stepper-connector" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  steps: string[];
  currentStep: number;
}>();

const emit = defineEmits<{
  (e: 'navigate', step: number): void;
}>();

const goToStep = (step: number) => {
  emit('navigate', step);
};
</script>

<style scoped>
.stepper {
  display: flex;
  flex-direction: column;
  gap: 0;
  min-width: 200px;
  padding: 1.5rem 1rem;
}

.stepper-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  position: relative;
  padding-bottom: 2rem;
}

.stepper-item:last-child {
  padding-bottom: 0;
}

.stepper-item:last-child .stepper-connector {
  display: none;
}

.stepper-connector {
  position: absolute;
  left: 17px;
  top: 38px;
  width: 2px;
  bottom: 0;
  background-color: var(--color-border);
}

.stepper-item.completed .stepper-connector {
  background-color: var(--color-primary);
}

.stepper-indicator {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.9rem;
  flex-shrink: 0;
  border: 2px solid var(--color-border);
  background: white;
  color: #999;
  transition: all 0.2s ease;
}

.stepper-item.active .stepper-indicator {
  border-color: var(--color-primary);
  background: var(--color-primary);
  color: white;
}

.stepper-item.completed .stepper-indicator {
  border-color: var(--color-primary);
  background: white;
  color: var(--color-primary);
}

.stepper-check {
  font-size: 1rem;
}

.stepper-label {
  font-size: 0.9rem;
  color: #999;
  font-weight: 400;
  line-height: 1.3;
  transition: color 0.2s ease;
}

.stepper-item.active .stepper-label {
  color: var(--color-primary);
  font-weight: 600;
}

.stepper-item.completed .stepper-label {
  color: var(--color-text);
  font-weight: 500;
}

.stepper-item.clickable {
  cursor: pointer;
}

.stepper-item.clickable:hover .stepper-indicator {
  background: var(--color-primary);
  color: white;
}

.stepper-item.clickable:hover .stepper-label {
  color: var(--color-primary);
}

/* Mobile: horizontal layout */
@media (max-width: 768px) {
  .stepper {
    flex-direction: row;
    min-width: unset;
    padding: 1rem 0;
    justify-content: center;
    gap: 0;
  }

  .stepper-item {
    flex-direction: column;
    align-items: center;
    padding-bottom: 0;
    flex: 1;
    gap: 0.4rem;
  }

  .stepper-connector {
    position: absolute;
    left: calc(50% + 20px);
    top: 17px;
    width: calc(100% - 40px);
    height: 2px;
    bottom: unset;
  }

  .stepper-indicator {
    width: 32px;
    height: 32px;
    font-size: 0.8rem;
  }

  .stepper-label {
    font-size: 0.7rem;
    text-align: center;
  }
}
</style>
