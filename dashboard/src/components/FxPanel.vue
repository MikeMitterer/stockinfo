<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { NButton, NInputNumber, NSelect } from 'naive-ui'

import { useFx } from '../composables/useFx'
import { formatDateTime } from '../utils/datetime'

const props = defineProps<{ currencies: string[] }>()

const { t, locale } = useI18n()
const { result, loading, error, convert } = useFx()

const base = ref<string>('EUR')
const quote = ref<string>('USD')
// `NInputNumber` liefert eine Zahl oder `null`, wenn das Feld geleert wurde.
const amount = ref<number | null>(1)

/*
 * Betrag defensiv: geleert, ungültig oder negativ → 1. Ein leeres Feld soll
 * die Umrechnung nicht abstürzen lassen, sondern den Kurs für eine Einheit
 * zeigen — das ist die Frage dahinter.
 */
const amountNum = computed<number>(() => {
  const value = amount.value
  return value !== null && Number.isFinite(value) && value >= 0 ? value : 1
})

/** Geldbetrag lokalisiert mit 2 Nachkommastellen. */
function formatMoney(value: number): string {
  return value.toLocaleString(locale.value, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const amountText = computed(() =>
  amountNum.value.toLocaleString(locale.value, { maximumFractionDigits: 4 }),
)
// Umgerechneter Betrag = Betrag × Rate (reaktiv, ohne erneuten Abruf).
const convertedText = computed(() => {
  const r = result.value
  return r ? formatMoney(amountNum.value * r.rate) : ''
})

function swap(): void {
  ;[base.value, quote.value] = [quote.value, base.value]
}

async function run(): Promise<void> {
  const b = base.value.trim().toUpperCase()
  const q = quote.value.trim().toUpperCase()
  if (b.length === 3 && q.length === 3) await convert(b, q)
}

/** Rate lokalisiert mit höchstens 3 Nachkommastellen. */
function formatRate(rate: number): string {
  return rate.toLocaleString(locale.value, { maximumFractionDigits: 3 })
}

/** Währungen als Auswahlliste — Kennung ist zugleich Beschriftung. */
const currencyOptions = computed(() =>
  props.currencies.map((code) => ({ value: code, label: code })),
)
</script>

<template>
  <section class="fx card">
    <h2>{{ t('fx.title') }}</h2>
    <p class="hint">{{ t('fx.hint') }}</p>

    <div class="controls">
      <NInputNumber
        v-model:value="amount"
        class="amount"
        :min="0"
        :aria-label="t('fx.amount')"
        @keyup.enter="run"
      />
      <NSelect
        v-model:value="base"
        class="code"
        :options="currencyOptions"
        :aria-label="t('fx.base')"
      />
      <NButton
        quaternary
        :title="t('fx.swap')"
        @click="swap"
      >
        ⇄
      </NButton>
      <NSelect
        v-model:value="quote"
        class="code"
        :options="currencyOptions"
        :aria-label="t('fx.quote')"
      />
      <NButton
        type="primary"
        :disabled="loading"
        :loading="loading"
        @click="run"
      >
        {{ loading ? t('fx.converting') : t('fx.convert') }}
      </NButton>
    </div>

    <p v-if="error" class="err">{{ error }}</p>

    <div v-if="result" class="result">
      <p class="amount-result mono">
        {{ amountText }} {{ result.base }} = {{ convertedText }} {{ result.quote }}
      </p>
      <p class="rate mono" :title="String(result.rate)">
        1 {{ result.base }} = {{ formatRate(result.rate) }} {{ result.quote }}
      </p>
      <dl>
        <div><dt>{{ t('fx.quoteTime') }}</dt>
          <dd class="mono nowrap">{{ formatDateTime(result.quote_time, locale) }}</dd></div>
        <div><dt>{{ t('fx.source') }}</dt><dd class="mono">{{ result.source }}</dd></div>
        <div><dt>{{ t('fx.status') }}</dt>
          <dd><span :class="['badge', result.stale ? 'warn' : 'std']">
            {{ result.stale ? t('fx.stale') : t('fx.fresh') }}</span></dd></div>
      </dl>
    </div>
  </section>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.fx {
  .hint { color: $color-muted; margin: 0 0 1rem; font-size: 0.85rem; max-width: 72ch; }
  .controls { display: flex; gap: 0.6rem; align-items: center; flex-wrap: wrap; margin-bottom: 1rem; }
  /*
   * Rahmen, Fläche und Innenabstand kommen von Naive UI — hier steht nur noch
   * die Breite. Sie muss stehen: Ein `NSelect` ohne Breitenangabe schrumpft im
   * Flex-Container auf seinen Mindestinhalt, und von „EUR" bleibt ein „E".
   */
  .amount { width: 8rem; }
  .code { width: 7rem; }
  .err { color: $color-danger; }
  .amount-result { font-size: 1.4rem; font-weight: 700; margin: 0.5rem 0 0.15rem; font-variant-numeric: tabular-nums; }
  .rate { color: $color-muted; font-size: 0.95rem; margin: 0 0 1rem; }
  .nowrap { white-space: nowrap; }
  dl { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 0.9rem 1.5rem; }
  dt { color: $color-muted; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.04em; }
  dd { margin: 0; }
  .badge { &.std { color: $color-accent; background: token(--accent, 0.15); }
           &.warn { color: $health-warn; background: token(--status-near, 0.18); } }
}
</style>
