<script setup lang="ts">
import { computed } from 'vue'
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
 * Der Kontext ist **eine** Zeile aus mehreren Angaben: Das Fundament nimmt
 * einen Text. Fehlt eine Angabe, fällt sie samt ihrem Trenner weg — ein
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
    :context="context"
    :version="version ? t('status.version', { version }) : ''"
    :backend-state="backendState"
    :backend-state-label="t(`status.${status}`)"
    @backend-click="emit('open-status')"
  />
</template>
