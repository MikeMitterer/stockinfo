<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { useFx } from '../composables/useFx'
import { formatDateTime } from '../utils/datetime'

defineProps<{ currencies: string[] }>()

const { t, locale } = useI18n()
const { result, loading, error, convert } = useFx()

const base = ref<string>('EUR')
const quote = ref<string>('USD')
const amount = ref<string>('1')

// Betrag defensiv: leer/ungültig/negativ → Fallback 1 (kein Crash).
// `Number('')` ist 0 → leeren String separat abfangen; `String()`, weil ein
// number-Input auch eine Zahl liefern kann.
const amountNum = computed<number>(() => {
  const raw = String(amount.value ?? '').trim()
  if (raw === '') return 1
  const n = Number(raw)
  return Number.isFinite(n) && n >= 0 ? n : 1
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
</script>

<template>
  <section class="fx card">
    <h2>{{ t('fx.title') }}</h2>
    <p class="hint">{{ t('fx.hint') }}</p>

    <div class="controls">
      <input
        v-model="amount"
        type="number"
        min="0"
        step="any"
        class="amount"
        :aria-label="t('fx.amount')"
        @keyup.enter="run"
      />
      <select v-model="base" class="code" :aria-label="t('fx.base')">
        <option v-for="c in currencies" :key="c" :value="c">{{ c }}</option>
      </select>
      <button class="swap" :title="t('fx.swap')" @click="swap">⇄</button>
      <select v-model="quote" class="code" :aria-label="t('fx.quote')">
        <option v-for="c in currencies" :key="c" :value="c">{{ c }}</option>
      </select>
      <button :disabled="loading" @click="run">
        {{ loading ? t('fx.converting') : t('fx.convert') }}
      </button>
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
  .amount { width: 7rem; padding: 0.4rem 0.6rem; border-radius: $radius; border: 1px solid $color-border; background: $color-surface; color: $color-text; font-family: $font-mono; font-variant-numeric: tabular-nums; }
  .code { width: 5rem; text-transform: uppercase; text-align: center; padding: 0.4rem; border-radius: $radius; border: 1px solid $color-border; background: $color-surface; color: $color-text; font-family: $font-mono; }
  .swap { background: $color-surface-2; border: 1px solid $color-border; border-radius: $radius; padding: 0.4rem 0.6rem; }
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
