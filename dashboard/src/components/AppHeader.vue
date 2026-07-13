<script setup lang="ts">
import type { TabKey } from '../types'
import NavIcon from './NavIcon.vue'

defineProps<{ active: TabKey }>()

const emit = defineEmits<{
  (event: 'navigate', tab: TabKey): void
}>()

const tabs: { key: TabKey; label: string; icon: string }[] = [
  { key: 'instruments', label: 'Instrumente', icon: 'instruments' },
  { key: 'environment', label: 'Environment', icon: 'environment' },
  { key: 'links', label: 'API & Links', icon: 'links' },
  { key: 'themes', label: 'Themes', icon: 'themes' },
]
</script>

<template>
  <header class="appheader">
    <button class="brand" title="Zur Startseite" @click="emit('navigate', 'instruments')">
      <img class="logo" src="/logo.svg" alt="MangoLila" />
      <span class="app">StockInfo</span>
    </button>
    <nav>
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab"
        :class="{ active: tab.key === active }"
        @click="emit('navigate', tab.key)"
      >
        <NavIcon :name="tab.icon" />
        <span>{{ tab.label }}</span>
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
  background: color-mix(in srgb, $color-bg 85%, transparent);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid $color-border;

  .brand {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    min-width: 0;
    background: transparent;
    border: none;
    padding: 0.2rem 0.3rem;
    border-radius: $radius;
    &:hover { background: $color-surface-2; }
  }
  .logo { height: 30px; }
  .app {
    font-weight: 700;
    letter-spacing: 0.04em;
    padding-left: 0.75rem;
    border-left: 1px solid $color-border;
    color: $color-muted;
  }

  nav { display: flex; gap: 0.25rem; }
  .tab {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    background: transparent;
    border: none;
    color: $color-muted;
    padding: 0.4rem 0.8rem;
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
      left: 0.8rem;
      right: 0.8rem;
      bottom: -0.42rem;
      height: 2px;
      background: $brand-gradient;
      border-radius: 2px;
    }
  }
}
</style>
