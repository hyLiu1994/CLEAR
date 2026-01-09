<template>
  <!-- Root node fixed at the bottom center, always stationary -->
  <div class="filter-root">
    <!-- Blue circular button at the bottom center -->
    <button
      type="button"
      class="filter-toggle"
      @click.stop="toggle"
    >
      <svg viewBox="0 0 24 24" class="filter-icon" aria-hidden="true">
        <path d="M4 6h16v2H4V6zm3 5h10v2H7v-2zm3 5h4v2h-4v-2z" />
      </svg>
    </button>

    <!-- Floating panel: above the button -->
    <transition name="panel-fade">
      <div
        v-if="internalVisible"
        class="filter-panel"
        @click.stop
      >
        <header class="filter-header">
          <div class="filter-title">{{ title }}</div>
          <button
            class="filter-close"
            type="button"
            @click="close"
          >
            ✕
          </button>
        </header>

        <div class="filter-body">
          <slot />
        </div>

        <footer class="filter-footer">
          <button
            type="button"
            class="btn btn-secondary"
            @click="onReset"
          >
            Reset
          </button>
          <button
            type="button"
            class="btn btn-primary"
            @click="onApply"
          >
            Apply
          </button>
        </footer>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: 'Filter'
  }
})

const emit = defineEmits(['update:modelValue', 'apply', 'reset', 'toggle'])

// Use internal state to synchronize external state
const internalVisible = ref(props.modelValue)

// Watch for external state changes
watch(() => props.modelValue, (newVal) => {
  internalVisible.value = newVal
})

// Watch for internal state changes and synchronize with external
watch(internalVisible, (newVal) => {
  emit('update:modelValue', newVal)
})

const toggle = () => {
  internalVisible.value = !internalVisible.value
  emit('toggle')
}

const close = () => {
  internalVisible.value = false
}

const onApply = () => {
  emit('apply')
  internalVisible.value = false
}

const onReset = () => {
  emit('reset')
}
</script>

<style scoped>
.filter-root {
  position: fixed;
  left: 50%;
  bottom: 40px;
  transform: translateX(-50%);
  z-index: 40;
}

.filter-toggle {
  width: 54px;
  height: 54px;
  border-radius: 999px;
  border: none;
  outline: none;
  cursor: pointer;
  background: #2563eb;
  box-shadow: 0 10px 25px rgba(37, 99, 235, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
}

.filter-toggle:hover {
  background: #1d4ed8;
}

.filter-icon {
  width: 24px;
  height: 24px;
  fill: #ffffff;
}

.filter-panel {
  position: absolute;
  left: 50%;
  bottom: 66px;
  transform: translateX(-50%);
  width: 360px;
  max-width: calc(100vw - 32px);
  background: rgba(15, 23, 42, 0.97);
  color: #e5e7eb;
  border-radius: 14px;
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(16px);
  display: flex;
  flex-direction: column;
  max-height: 70vh;
  z-index: 50;
}

.filter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.35);
}

.filter-title {
  font-size: 30px;
  font-weight: 600;
}

.filter-close {
  border: none;
  background: transparent;
  color: #9ca3af;
  font-size: 14px;
  cursor: pointer;
}

.filter-close:hover {
  color: #e5e7eb;
}

.filter-body {
  padding: 10px 12px 8px;
  overflow-y: auto;
}

.filter-footer {
  padding: 8px 10px 10px;
  border-top: 1px solid rgba(148, 163, 184, 0.35);
  display: flex;
  justify-content: center;
  gap: 10px;
}

.btn {
  border-radius: 999px;
  padding: 6px 18px;
  font-size: 12px;
  border: none;
  cursor: pointer;
}

.btn-secondary {
  background: rgba(31, 41, 55, 0.95);
  color: #e5e7eb;
}

.btn-secondary:hover {
  background: rgba(55, 65, 81, 0.98);
}

.btn-primary {
  background: #3b82f6;
  color: #ffffff;
}

.btn-primary:hover {
  background: #2563eb;
}

.panel-fade-enter-active,
.panel-fade-leave-active {
  transition: opacity 0.18s ease-out, transform 0.18s ease-out;
}

.panel-fade-enter-from,
.panel-fade-leave-to {
  opacity: 0;
  transform: translate(-50%, 4px);
}
</style>