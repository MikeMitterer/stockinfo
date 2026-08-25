<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import InfoHint from './InfoHint.vue'
import type { CatalogEntry, ExchangesResponse } from '../types'

defineProps<{ data: ExchangesResponse | null }>()
const { t } = useI18n()

/**
 * Die Kennung eines Katalogeintrags — MIC bei einer Börse, Code bei einem
 * Sammelcode.
 *
 * Ein Sammelcode hat bewusst **kein** `mic`-Feld: Er ist keiner, und bis
 * T-21 Teil 3 kam er trotzdem als `mic: 'US'` herein.
 */
function entryCode(entry: CatalogEntry): string {
  return entry.kind === 'exchange' ? entry.mic : entry.code
}
</script>

<template>
  <section v-if="data" class="exchanges card">
    <h2>{{ t('exchanges.title') }}</h2>
    <p class="hint">
      {{ t('exchanges.hint', { example: 'EUNL.DE' }) }}
      <!--
        Die markierte Standard-Börse ist nur die halbe Auskunft: Ob daneben
        überhaupt ausgewichen wird, entscheidet „Strikte Börse" — und die steht
        eine Seite weiter. Deshalb der Verweis genau hier.
      -->
      <InfoHint :text="t('env.strictExchangeHint')" settings-tab="environment" />
    </p>
    <div class="scroll">
      <table class="data-table">
        <thead>
          <tr>
            <th>{{ t('exchanges.colSuffix') }}</th><th>{{ t('exchanges.colExchange') }}</th>
            <th>{{ t('exchanges.colRegion') }}</th><th>{{ t('exchanges.colCurrency') }}</th><th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="entry in data.catalog" :key="entryCode(entry)"
              :class="{ 'is-default': entryCode(entry) === data.default_exchange }">
            <td class="mono suffix">
              {{ entry.kind === 'exchange' ? entry.alias || t('exchanges.noSuffix') : entryCode(entry) }}
            </td>
            <td>{{ entry.name }}</td>
            <td class="dim">{{ t(`exchanges.regions.${entry.region}`) }}</td>
            <td class="mono">{{ entry.currency }}</td>
            <td>
              <span v-if="entryCode(entry) === data.default_exchange" class="badge std">{{ t('exchanges.default') }}</span>
              <span v-if="entry.kind === 'collector'" class="badge warn"
                    :title="entry.members.join(', ')">{{ t('exchanges.collector') }}</span>
              <span v-if="entry.currency === 'GBp'" class="badge warn">{{ t('exchanges.penceNote') }}</span>
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

td { padding: 0.45rem 0.7rem; border-bottom: 1px solid token(--border-default, 0.55); }
.suffix { font-weight: 600; color: $color-accent; }
.dim { color: $color-muted; }

tr.is-default td { background: token(--accent, 0.08); }

// Varianten der globalen .badge-Pill
.badge {
  &.std { color: $color-accent; background: token(--accent, 0.15); }
  &.warn { color: $health-warn; background: token(--status-near, 0.18); }
}
</style>
