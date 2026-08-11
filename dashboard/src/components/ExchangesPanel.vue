<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { ExchangesResponse } from '../types'

defineProps<{ data: ExchangesResponse | null }>()
const { t } = useI18n()
</script>

<template>
  <section v-if="data" class="exchanges card">
    <h2>{{ t('exchanges.title') }}</h2>
    <p class="hint">{{ t('exchanges.hint', { example: 'EUNL.DE' }) }}</p>
    <div class="scroll">
      <table class="data-table">
        <thead>
          <tr>
            <th>{{ t('exchanges.colSuffix') }}</th><th>{{ t('exchanges.colExchange') }}</th>
            <th>{{ t('exchanges.colRegion') }}</th><th>{{ t('exchanges.colCurrency') }}</th><th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ex in data.exchanges" :key="ex.mic"
              :class="{ 'is-default': ex.mic === data.default_exchange }">
            <td class="mono suffix">{{ ex.suffix || t('exchanges.noSuffix') }}</td>
            <td>{{ ex.name }}</td>
            <td class="dim">{{ t(`exchanges.regions.${ex.region}`) }}</td>
            <td class="mono">{{ ex.currency }}</td>
            <td>
              <span v-if="ex.mic === data.default_exchange" class="badge std">{{ t('exchanges.default') }}</span>
              <span v-if="ex.currency === 'GBp'" class="badge warn">{{ t('exchanges.penceNote') }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.hint { color: $color-muted; margin: 0 0 1rem; font-size: 0.85rem; }
.hint code { font-family: $font-mono; color: $color-text; }
.scroll { overflow-x: auto; }

td { padding: 0.45rem 0.7rem; border-bottom: 1px solid color-mix(in srgb, $color-border 55%, transparent); }
.suffix { font-weight: 600; color: $color-accent; }
.dim { color: $color-muted; }

tr.is-default td { background: color-mix(in srgb, $color-accent 8%, transparent); }

// Varianten der globalen .badge-Pill
.badge {
  &.std { color: $color-accent; background: color-mix(in srgb, $color-accent 15%, transparent); }
  &.warn { color: $health-warn; background: color-mix(in srgb, $health-warn 18%, transparent); }
}
</style>
