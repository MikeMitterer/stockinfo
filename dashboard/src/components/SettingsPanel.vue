<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { NButton, NButtonGroup, NTabPane, NTabs } from 'naive-ui'

import { LOCALES, setLanguage } from '../i18n'
import { SETTINGS_TABS } from '../composables/useHashTab'
import type { EnvInfo, SettingsTab } from '../types'
import EnvironmentPanel from './EnvironmentPanel.vue'
import LinksPanel from './LinksPanel.vue'
import ThemesPanel from './ThemesPanel.vue'

/**
 * Die Einstellungsseite: eine Seite, darin Reiter.
 *
 * Reiter und Knöpfe kommen von Naive UI. Der aktive Reiter bleibt über die
 * Adresse ansteuerbar (`#/settings?tab=…`) — nur so kann ein Hinweis irgendwo
 * in der App auf die zugehörige Einstellung verweisen, statt "steht irgendwo
 * in den Einstellungen" zu sagen.
 */
defineProps<{ tab: SettingsTab; env: EnvInfo | null }>()

const emit = defineEmits<{
  (event: 'update:tab', tab: SettingsTab): void
}>()

const { t, locale } = useI18n()
</script>

<template>
  <section class="settings">
    <h2 class="settings__title">{{ t('settings.title') }}</h2>

    <NTabs
      :value="tab"
      type="line"
      @update:value="emit('update:tab', $event as SettingsTab)"
    >
      <NTabPane
        v-for="key in SETTINGS_TABS"
        :key="key"
        :name="key"
        :tab="t(`settings.tab.${key}`)"
      >
        <ThemesPanel v-if="key === 'appearance'" />

        <div
          v-else-if="key === 'language'"
          class="settings__lang"
        >
          <p class="settings__hint">
            {{ t('settings.language.hint') }}
          </p>
          <!--
            Eine Gruppe: Die Sprachen schließen einander aus, genau das zeigt
            die zusammenhängende Form.
          -->
          <NButtonGroup :aria-label="t('language.title')">
            <NButton
              v-for="lang in LOCALES"
              :key="lang"
              class="lang-choice__btn"
              :type="locale === lang ? 'primary' : 'default'"
              @click="setLanguage(lang)"
            >
              {{ t(`language.${lang}`) }}
            </NButton>
          </NButtonGroup>
        </div>

        <LinksPanel v-else-if="key === 'links'" />

        <EnvironmentPanel
          v-else-if="key === 'environment'"
          :env="env"
        />
      </NTabPane>
    </NTabs>
  </section>
</template>

<style scoped lang="scss">
/*
 * Reiter und Knöpfe bringen ihre Gestaltung von Naive UI mit — hier bleibt
 * nur, was diese Seite ausmacht.
 */

.settings {
  &__title {
    font-family: var(--font-display);
    font-size: 1.25rem;
    font-weight: 600;
    margin: 0 0 1rem;
  }

  &__hint {
    @include muted(0.85rem);
    max-width: 72ch;
    margin: 0 0 1rem;
  }

  &__lang {
    @include stack(var(--space-3));
    align-items: flex-start;
  }
}
</style>
