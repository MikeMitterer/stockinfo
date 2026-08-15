<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import type { NavIconName, TabKey } from '../types'
import NavIcon from './NavIcon.vue'

defineProps<{ active: TabKey }>()

const emit = defineEmits<{
  (event: 'navigate', tab: TabKey): void
}>()

const { t } = useI18n()

const isOpen = ref(false)

const tabs = computed<{ key: TabKey; label: string; icon: NavIconName }[]>(() => [
  { key: 'assets', label: t('nav.assets'), icon: 'assets' },
  { key: 'exchanges', label: t('nav.exchanges'), icon: 'exchanges' },
  { key: 'fx', label: t('nav.fx'), icon: 'fx' },
  { key: 'analysis', label: t('nav.analysis'), icon: 'analysis' },
])

/** Navigiert zum Tab und schließt das mobile Menü. */
function selectTab(key: TabKey): void {
  emit('navigate', key)
  isOpen.value = false
}

/** Schließt das mobile Menü bei Escape. */
function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') isOpen.value = false
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <header class="appheader">
    <button class="brand" :title="t('nav.home')" @click="emit('navigate', 'assets')">
      <img class="logo" src="/stockinfo-logo.svg" alt="StockInfo" />
    </button>

    <button
      class="hamburger"
      :aria-label="t('nav.menu')"
      :aria-expanded="isOpen"
      aria-controls="mobile-nav"
      @click="isOpen = !isOpen"
    >
      ☰
    </button>

    <div v-if="isOpen" class="backdrop" @click="isOpen = false" />

    <nav id="mobile-nav" class="nav-tabs" :class="{ open: isOpen }">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab"
        :class="{ active: tab.key === active }"
        @click="selectTab(tab.key)"
      >
        <NavIcon :name="tab.icon" />
        <span>{{ tab.label }}</span>
      </button>
    </nav>

    <button
      class="settings-btn"
      :class="{ active: active === 'settings' }"
      :title="t('nav.settings')"
      :aria-label="t('nav.settings')"
      @click="emit('navigate', 'settings')"
    >
      <NavIcon name="settings" />
    </button>
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
  // Logo links, Navigation + Zahnrad als Gruppe rechts
  gap: 0.75rem;
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
    padding: 0;
    border-radius: $radius;
    &:hover { opacity: 0.85; }
  }
  .logo { height: 40px; display: block; }

  .nav-tabs { display: flex; gap: 0.25rem; }

  .hamburger {
    display: none; // Desktop: versteckt
    background: transparent;
    border: none;
    color: $color-text;
    font-size: 1.4rem;
    line-height: 1;
    padding: 0.3rem 0.55rem;
    border-radius: $radius;
    cursor: pointer;
    &:hover { background: $color-surface-2; }
  }

  .backdrop { display: none; } // Desktop: nie

  .tab {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    white-space: nowrap; // Label nie umbrechen (z.B. "API & Links")
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

  .settings-btn {
    display: inline-flex;
    align-items: center;
    margin-left: auto;
    background: transparent;
    border: none;
    color: $color-muted;
    padding: 0.4rem 0.5rem;
    border-radius: $radius;
    cursor: pointer;

    &:hover { color: $color-text; background: $color-surface-2; }
    &.active { color: $color-text; background: $color-surface; }
  }

  @media (max-width: $header-bp) {
    .nav-tabs {
      display: none; // geschlossen
      &.open {
        display: flex;
        flex-direction: column;
        align-items: stretch;
        gap: 0.15rem;
        position: fixed;
        top: $header-h;
        left: 0;
        right: 0;
        margin-left: 0;
        padding: 0.5rem 1.25rem 0.75rem;
        background: color-mix(in srgb, $color-bg 96%, transparent);
        backdrop-filter: blur(8px);
        border-bottom: 1px solid $color-border;
        z-index: 19;

        .tab { width: 100%; justify-content: flex-start; }
        .tab.active::after { display: none; } // Unterstrich im Drawer weglassen
      }
    }

    // ☰ nach links (Drawer-Konvention), Zahnrad bleibt rechts
    .hamburger { display: inline-flex; align-items: center; order: -1; }
    .settings-btn { margin-left: auto; }

    .backdrop {
      display: block;
      position: fixed;
      inset: $header-h 0 0 0;
      z-index: 18;
      background: transparent;
    }
  }
}
</style>
