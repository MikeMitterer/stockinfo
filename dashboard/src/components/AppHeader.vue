<script setup lang="ts">
import type { TabKey } from '../types'

defineProps<{ active: TabKey }>()

const emit = defineEmits<{
  (event: 'navigate', tab: TabKey): void
}>()

const tabs: { key: TabKey; label: string }[] = [
  { key: 'instruments', label: 'Instrumente' },
  { key: 'environment', label: 'Environment' },
  { key: 'links', label: 'API & Links' },
]
</script>

<template>
  <header class="appheader">
    <div class="brand">
      <img class="logo" src="/logo.svg" alt="MangoLila" />
      <span class="app">StockInfo</span>
    </div>
    <nav>
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab"
        :class="{ active: tab.key === active }"
        @click="emit('navigate', tab.key)"
      >
        {{ tab.label }}
      </button>
    </nav>
  </header>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.appheader {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: $header-h;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  padding: 0 1.25rem;
  background: rgba(20, 16, 25, 0.85);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid $color-border;

  .brand { display: flex; align-items: center; gap: 0.75rem; min-width: 0; }
  .logo { height: 30px; }
  .app {
    font-weight: 700;
    letter-spacing: 0.04em;
    padding-left: 0.75rem;
    border-left: 1px solid $color-border;
    color: $color-muted;
  }

  nav { display: flex; gap: 0.35rem; }
  .tab {
    background: transparent;
    border: none;
    color: $color-muted;
    padding: 0.4rem 0.85rem;
    border-radius: $radius;
    position: relative;

    &:hover { color: $color-text; background: $color-surface-2; }
    &.active {
      color: $color-text;
      background: $color-surface;
    }
    &.active::after {
      content: '';
      position: absolute;
      left: 0.85rem;
      right: 0.85rem;
      bottom: -0.42rem;
      height: 2px;
      background: $brand-gradient;
      border-radius: 2px;
    }
  }
}
</style>
