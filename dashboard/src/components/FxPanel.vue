<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { useFx } from '../composables/useFx'

const { t } = useI18n()
const { result, loading, error, convert } = useFx()

const base = ref<string>('EUR')
const quote = ref<string>('USD')

function swap(): void {
  ;[base.value, quote.value] = [quote.value, base.value]
}

async function run(): Promise<void> {
  const b = base.value.trim().toUpperCase()
  const q = quote.value.trim().toUpperCase()
  if (b.length === 3 && q.length === 3) await convert(b, q)
}
</script>

<template>
  <section class="fx card">
    <h2>{{ t('fx.title') }}</h2>
    <p class="hint">{{ t('fx.hint') }}</p>

    <div class="controls">
      <input v-model="base" maxlength="3" class="code" :aria-label="t('fx.base')" />
      <button class="swap" :title="t('fx.swap')" @click="swap">⇄</button>
      <input v-model="quote" maxlength="3" class="code" :aria-label="t('fx.quote')" />
      <button :disabled="loading" @click="run">
        {{ loading ? t('fx.converting') : t('fx.convert') }}
      </button>
    </div>

    <p v-if="error" class="err">{{ error }}</p>

    <div v-if="result" class="result">
      <p class="rate mono">1 {{ result.base }} = {{ result.rate }} {{ result.quote }}</p>
      <dl>
        <div><dt>{{ t('fx.quoteTime') }}</dt><dd class="mono">{{ result.quote_time }}</dd></div>
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
  .code { width: 5rem; text-transform: uppercase; text-align: center; padding: 0.4rem; border-radius: $radius; border: 1px solid $color-border; background: $color-surface; color: $color-text; font-family: $font-mono; }
  .swap { background: $color-surface-2; border: 1px solid $color-border; border-radius: $radius; padding: 0.4rem 0.6rem; }
  .err { color: #e5484d; }
  .rate { font-size: 1.4rem; font-weight: 700; margin: 0.5rem 0 1rem; }
  dl { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 0.9rem 1.5rem; }
  dt { color: $color-muted; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.04em; }
  dd { margin: 0; }
  .badge { &.std { color: $color-accent; background: color-mix(in srgb, $color-accent 15%, transparent); }
           &.warn { color: $health-warn; background: color-mix(in srgb, $health-warn 18%, transparent); } }
}
</style>
