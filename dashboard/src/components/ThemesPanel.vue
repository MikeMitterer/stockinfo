<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import { THEMES, useTheme } from '../composables/useTheme'

const { current, setTheme } = useTheme()
const { t } = useI18n()
</script>

<template>
  <section class="themes card">
    <h2>{{ t('themes.title') }}</h2>
    <p class="hint">{{ t('themes.hint') }}</p>
    <div class="grid">
      <button
        v-for="theme in THEMES"
        :key="theme.key"
        class="swatch"
        :class="{ active: current === theme.key }"
        :data-theme="theme.key"
        @click="setTheme(theme.key)"
      >
        <span class="preview">
          <i class="bar grad" />
          <i class="dot a" />
          <i class="dot b" />
        </span>
        <span class="label">{{ theme.label }}</span>
      </button>
    </div>
  </section>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.hint { color: $color-muted; margin: 0 0 1rem; font-size: 0.82rem; }

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 0.9rem;
}

.swatch {
  // data-theme auf dem Button → die var(--c-*) darin zeigen die Theme-Farben
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  padding: 0.8rem;
  border-radius: $radius;
  border: 1px solid var(--c-border);
  background: var(--c-bg);
  text-align: left;

  &.active { border-color: var(--c-accent); box-shadow: 0 0 0 2px var(--c-accent); }

  .preview {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    height: 26px;
  }
  .bar {
    flex: 1;
    height: 100%;
    border-radius: 6px;
    background: var(--c-grad);
  }
  .dot { width: 14px; height: 26px; border-radius: 6px; }
  .dot.a { background: var(--c-surface-2); }
  .dot.b { background: var(--c-accent-2); }

  .label { color: var(--c-text); font-weight: 600; font-size: 0.85rem; }
}
</style>
