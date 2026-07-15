<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { LOCALES, setLanguage } from '../i18n'
import type { NavIconName, TabKey } from '../types'
import NavIcon from './NavIcon.vue'

defineProps<{ active: TabKey }>()

const emit = defineEmits<{
  (event: 'navigate', tab: TabKey): void
}>()

const { t, locale } = useI18n()

const tabs = computed<{ key: TabKey; label: string; icon: NavIconName }[]>(() => [
  { key: 'assets', label: t('nav.assets'), icon: 'assets' },
  { key: 'exchanges', label: t('nav.exchanges'), icon: 'exchanges' },
  { key: 'environment', label: t('nav.environment'), icon: 'environment' },
  { key: 'links', label: t('nav.links'), icon: 'links' },
  { key: 'themes', label: t('nav.themes'), icon: 'themes' },
])
</script>

<template>
  <header class="appheader">
    <button class="brand" :title="t('nav.home')" @click="emit('navigate', 'assets')">
      <img class="logo" src="/stockinfo-logo.svg" alt="StockInfo" />
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
    <div class="lang" role="group" :aria-label="t('language.title')">
      <button
        v-for="lang in LOCALES"
        :key="lang"
        class="lng"
        :class="{ active: locale === lang }"
        :title="t(`language.${lang}`)"
        @click="setLanguage(lang)"
      >
        {{ lang.toUpperCase() }}
      </button>
    </div>
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
    padding: 0;
    border-radius: $radius;
    &:hover { opacity: 0.85; }
  }
  .logo { height: 40px; display: block; }

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

  .lang {
    display: inline-flex;
    gap: 2px;
    padding: 3px;
    border-radius: $radius;
    background: $color-surface;
    border: 1px solid $color-border;

    .lng {
      background: transparent;
      border: none;
      color: $color-muted;
      padding: 0.2rem 0.5rem;
      border-radius: 7px;
      font-size: 0.75rem;
      font-weight: 700;

      &:hover { color: $color-text; }
      &.active { color: #fff; background: $brand-gradient; }
    }
  }
}
</style>
