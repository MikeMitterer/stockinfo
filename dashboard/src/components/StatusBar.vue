<script setup lang="ts">
import { computed } from 'vue'
import { NButton } from 'naive-ui'
import { REPOSITORY_URL } from '../config'
import { useI18n } from 'vue-i18n'
import { UxStatusBar, type BackendState } from '@mmit/ux-foundation'

import type { HealthStatus } from '../composables/useHealth'

/**
 * Die Statuszeile dieser App.
 *
 * Aussehen und Aufbau liefert das Fundament (`UxStatusBar`). Hier bleibt die
 * Verdrahtung: wie der Gesundheitszustand des Backends heißt und wie er auf
 * die drei Zustände abgebildet wird, die eine Statuszeile kennt.
 */
const props = defineProps<{
  status: HealthStatus
  version: string | null
  /** Anzahl der geführten Papiere — der aktive Kontext dieser App. */
  instrumentCount?: number
  /** Die einsatzbereite Kurskette in Rangfolge; leer, wenn keine bekannt ist. */
  quoteChain?: string[]
}>()

const emit = defineEmits<{
  (event: 'open-status'): void
}>()

const { t } = useI18n()

/*
 * Der Gesundheitszustand der App heißt anders als der Zustand, den eine
 * Statuszeile kennt: `degraded` ist ein Prüfen, `down` ein Ausfall. Die
 * Abbildung steht hier und nicht im Paket — wie eine App ihre Gegenstelle
 * nennt, weiß nur sie.
 */
const backendState = computed<BackendState>(() => {
  if (props.status === 'ok') return 'online'
  if (props.status === 'degraded') return 'checking'
  return 'offline'
})

/*
 * Der Kontext ist **eine** Zeile aus mehreren Angaben. Fehlt eine Angabe, fällt sie samt ihrem Trenner weg — ein
 * Trenner ins Leere sieht nach einem Ladefehler aus.
 */
const context = computed(() => {
  const parts: string[] = []
  if (props.instrumentCount !== undefined) {
    parts.push(
      t('status.instruments', props.instrumentCount, { named: { count: props.instrumentCount } }),
    )
  }
  const chain = props.quoteChain ?? []
  if (chain.length > 0) {
    parts.push(t('status.quoteChain', { chain: chain.join(' → ') }))
  }
  return parts.join(' · ')
})
</script>

<template>
  <UxStatusBar
    app-name="StockInfo"
    :powered-by-label="t('status.poweredBy')"
    origin-name="MangoLila"
    origin-href="https://www.mangolila.at/"
    :version="version ? t('status.version', { version }) : ''"
    :backend-state="backendState"
    :backend-state-label="t(`status.${status}`)"
    @backend-click="emit('open-status')"
  >
    <template #left>
      <NButton
        class="status__repo" text tag="a" :href="REPOSITORY_URL"
        target="_blank" rel="noopener noreferrer" :aria-label="t('links.repo')" :title="t('links.repo')"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.9a3.4 3.4 0 0 0-1-2.7c3.3-.4 6.7-1.6 6.7-7.3A5.7 5.7 0 0 0 20.2 4a5.3 5.3 0 0 0-.1-4s-1.2-.4-4.1 1.5a13.4 13.4 0 0 0-7 0C6.1-.4 4.9 0 4.9 0a5.3 5.3 0 0 0-.1 4 5.7 5.7 0 0 0-1.5 4c0 5.7 3.4 6.9 6.7 7.3a3.4 3.4 0 0 0-1 2.7V22" />
        </svg>
      </NButton>
      <span v-if="context" class="status__context">{{ context }}</span>
    </template>
  </UxStatusBar>
</template>

<style scoped lang="scss">
.status {
  &__repo {
    color: token(--text-bar-accent);
    svg { inline-size: var(--font-base); block-size: var(--font-base); }
  }
  &__context { color: token(--text-bar-secondary); }
}
</style>
