<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import { LOCALES, setLanguage } from '../i18n'
import { SETTINGS_TABS } from '../composables/useHashTab'
import type { EnvInfo, SettingsTab } from '../types'
import EnvironmentPanel from './EnvironmentPanel.vue'
import LinksPanel from './LinksPanel.vue'
import ThemesPanel from './ThemesPanel.vue'

defineProps<{ tab: SettingsTab; env: EnvInfo | null }>()

const emit = defineEmits<{
  (event: 'update:tab', tab: SettingsTab): void
}>()

const { t, locale } = useI18n()
</script>

<template>
  <section class="settings">
    <h2 class="settings__title">{{ t('settings.title') }}</h2>

    <nav class="settings__tabs" role="tablist" :aria-label="t('settings.title')">
      <button
        v-for="key in SETTINGS_TABS"
        :key="key"
        class="settings__tab"
        :class="{ active: key === tab, 'settings__tab--diag': key === 'environment' }"
        role="tab"
        :aria-selected="key === tab"
        @click="emit('update:tab', key)"
      >
        {{ t(`settings.tab.${key}`) }}
      </button>
    </nav>

    <div class="settings__body">
      <ThemesPanel v-if="tab === 'appearance'" />

      <div v-else-if="tab === 'language'" class="settings__lang">
        <p class="settings__hint">{{ t('settings.language.hint') }}</p>
        <div class="lang-choice" role="group" :aria-label="t('language.title')">
          <button
            v-for="lang in LOCALES"
            :key="lang"
            class="lang-choice__btn"
            :class="{ active: locale === lang }"
            @click="setLanguage(lang)"
          >
            {{ t(`language.${lang}`) }}
          </button>
        </div>
      </div>

      <LinksPanel v-else-if="tab === 'links'" />

      <EnvironmentPanel v-else-if="tab === 'environment'" :env="env" />
    </div>
  </section>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.settings {
  &__title {
    font-size: 1.25rem;
    font-weight: 600;
    margin: 0 0 1rem;
  }

  &__tabs {
    display: flex;
    gap: 0.25rem;
    border-bottom: 1px solid $color-border;
    margin-bottom: 1.25rem;
  }

  &__tab {
    background: transparent;
    border: none;
    color: $color-muted;
    padding: 0.5rem 0.9rem;
    border-radius: $radius $radius 0 0;
    white-space: nowrap;
    position: relative;
    cursor: pointer;

    &:hover { color: $color-text; }

    &.active {
      color: $color-text;

      // messungsfreier Unterstrich am aktiven Reiter — verrutscht nicht beim Sprachwechsel
      &::after {
        content: '';
        position: absolute;
        left: 0.9rem;
        right: 0.9rem;
        bottom: -1px;
        height: 2px;
        background: $brand-gradient;
        border-radius: 2px;
      }
    }

    // Diagnose-Reiter (Environment) sichtbar abgesetzt ganz rechts
    &--diag { margin-left: auto; }
  }

  &__hint {
    color: $color-muted;
    font-size: 0.875rem;
    margin: 0 0 0.75rem;
  }
}

.lang-choice {
  display: inline-flex;
  gap: 2px;
  padding: 3px;
  border-radius: $radius;
  background: $color-surface;
  border: 1px solid $color-border;

  &__btn {
    background: transparent;
    border: none;
    color: $color-muted;
    padding: 0.35rem 0.8rem;
    border-radius: 7px;
    cursor: pointer;

    &:hover { color: $color-text; }
    &.active { color: #fff; background: $brand-gradient; }
  }
}
</style>
