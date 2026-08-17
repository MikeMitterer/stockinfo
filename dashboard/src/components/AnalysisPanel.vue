<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { NButton, NInput, NSelect } from 'naive-ui'

import { isIsin } from '../api/paths'
import { useAnalysis } from '../composables/useAnalysis'
import type { InstrumentRef, InstrumentSummary } from '../types'

const props = defineProps<{ instruments: InstrumentSummary[] }>()

const { t } = useI18n()
const { result, loading, error, analyze } = useAnalysis()

const selectedSymbol = ref<string>('')
const freeInput = ref<string>('')

// Freitext hat Vorrang; sonst das gewählte Listen-Instrument.
const target = computed<InstrumentRef | null>(() => {
  const raw = freeInput.value.trim()
  if (raw) {
    return isIsin(raw.toUpperCase())
      ? { isin: raw.toUpperCase(), symbol: raw }
      : { isin: null, symbol: raw }
  }
  const found = props.instruments.find((i) => i.symbol === selectedSymbol.value)
  return found ? { isin: found.isin, symbol: found.symbol } : null
})

async function run(): Promise<void> {
  if (target.value) await analyze(target.value)
}

/** Auswahlliste für Naive: Wert ist das Symbol, Beschriftung nennt den Namen. */
const instrumentOptions = computed(() =>
  props.instruments.map((instrument) => ({
    value: instrument.symbol,
    label: `${instrument.symbol} — ${instrument.name ?? instrument.isin}`,
  })),
)
</script>

<template>
  <section class="analysis card">
    <h2>{{ t('analysis.title') }}</h2>
    <p class="hint">{{ t('analysis.hint') }}</p>

    <div class="controls">
      <NSelect
        v-model:value="selectedSymbol"
        class="controls__pick"
        :options="instrumentOptions"
        :placeholder="t('analysis.pickInstrument')"
        :aria-label="t('analysis.pickInstrument')"
        clearable
      />
      <NInput
        v-model:value="freeInput"
        class="controls__free"
        :placeholder="t('analysis.placeholder')"
        :aria-label="t('analysis.orEnter')"
        @keyup.enter="run"
      />
      <NButton
        type="primary"
        :disabled="loading || !target"
        :loading="loading"
        @click="run"
      >
        {{ loading ? t('analysis.running') : t('analysis.run') }}
      </NButton>
    </div>

    <p v-if="error" class="err">{{ error }}</p>

    <table v-if="result" class="stages">
      <thead>
        <tr>
          <th>{{ t('analysis.colStage') }}</th>
          <th>{{ t('analysis.colSeconds') }}</th>
          <th>{{ t('analysis.colStatus') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="s in result.stages" :key="s.stage" :class="s.status">
          <td>{{ s.stage }}</td>
          <td class="num">{{ s.seconds.toFixed(2) }}s</td>
          <td>{{ s.status }}<span v-if="s.detail"> · {{ s.detail }}</span></td>
        </tr>
        <tr class="total">
          <td>{{ t('analysis.total') }}</td>
          <td class="num">{{ result.total.toFixed(2) }}s</td>
          <td></td>
        </tr>
      </tbody>
    </table>
    <p v-else class="hint">{{ t('analysis.empty') }}</p>
  </section>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.analysis {
  .hint { color: $color-muted; margin: 0 0 1rem; font-size: 0.85rem; max-width: 72ch; }
  .controls { display: flex; gap: 0.6rem; flex-wrap: wrap; margin-bottom: 1rem; }
  select, input { font: inherit; padding: 0.4rem 0.6rem; border-radius: $radius; border: 1px solid $color-border; background: $color-surface; color: $color-text; }
  input { flex: 1; min-width: 12rem; }
  // Select nie breiter als der Container (längste Option würde sonst überlaufen)
  select { min-width: 0; max-width: 100%; font-size: 1rem; }
  // Optionen explizit (nicht nur geerbt): App-Schrift + 16px (mobile-Standard, kein iOS-Zoom)
  select option { font-family: inherit; font-size: 1rem; }
  .err { color: $color-danger; margin: 0.5rem 0; }
  table.stages { width: 100%; border-collapse: collapse; font-family: $font-mono; font-variant-numeric: tabular-nums; }
  th, td { text-align: left; padding: 0.4rem 0.6rem; border-bottom: 1px solid $color-border; }
  .num { text-align: right; }
  tr.error td { color: $color-danger; }
  tr.total td { font-weight: 700; border-top: 2px solid $color-border; }
}
</style>
