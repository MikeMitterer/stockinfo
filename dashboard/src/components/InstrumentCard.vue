<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import IsinEditor from './IsinEditor.vue'
import type { InstrumentSummary } from '../types'

const props = defineProps<{
  item: InstrumentSummary
  selected: boolean
  refreshing: boolean
  extraetfUrl: string
  yahooUrl: string
}>()

const emit = defineEmits<{
  (event: 'select', item: InstrumentSummary): void
  (event: 'refresh', item: InstrumentSummary): void
  (event: 'remove', item: InstrumentSummary): void
  (event: 'json', item: InstrumentSummary): void
  (event: 'set-isin', payload: { symbol: string; isin: string }): void
}>()

const { t, locale } = useI18n()

// Auf-/Zuklappen der Kennzahlen — pro Karte lokal, ID muss eindeutig sein.
const expanded = ref<boolean>(false)
const detailsId = computed(() => `icard-details-${props.item.symbol}`)

function toggle(): void {
  expanded.value = !expanded.value
}

/** Formatiert einen Kurs mit zwei Nachkommastellen (oder '—'), sprachabhängig. Mirror von InstrumentsTable. */
function price(value: number | null): string {
  return value === null
    ? '—'
    : value.toLocaleString(locale.value, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

/** Formatiert einen Prozentwert mit zwei Nachkommastellen (oder '—'). Mirror von InstrumentsTable. */
function formatPercent(value: number | null): string {
  return value === null ? '—' : `${value.toFixed(2)} %`
}

/** Thesaurierend-Anzeige: Ja / Nein / '—' bei unbekannt. Mirror von InstrumentsTable. */
function accumulating(value: boolean | null): string {
  if (value === null) return '—'
  return value ? t('table.yes') : t('table.no')
}
</script>

<template>
  <article class="icard card" :class="{ 'icard--selected': selected }">
    <div class="icard__head" @click="emit('select', item)">
      <span class="icard__symbol mono">{{ item.symbol }}</span>
      <span v-if="item.type" class="icard__type badge" :class="item.type">{{ item.type }}</span>
      <span class="icard__price mono">
        {{ price(item.latest_price) }}
        <span class="icard__ccy">{{ item.latest_currency ?? '' }}</span>
      </span>
      <span class="icard__name">{{ item.name ?? '—' }}</span>
    </div>

    <div class="icard__foot">
      <button
        class="icard__toggle"
        :aria-expanded="expanded"
        :aria-controls="detailsId"
        @click.stop="toggle"
      >
        <span class="icard__chevron" :class="{ 'icard__chevron--open': expanded }">⌄</span>
        {{ expanded ? t('table.less') : t('table.more') }}
      </button>

      <div class="icard__actions" @click.stop>
        <button class="icard__action icard__action--json" :title="t('table.showJson')" @click="emit('json', item)">
          JSON
        </button>
        <a
          v-if="extraetfUrl"
          class="icard__action icard__action--extraetf"
          :href="extraetfUrl"
          target="_blank"
          rel="noopener"
          :title="t('table.extraetfProfile')"
        >eETF</a>
        <a
          v-if="yahooUrl"
          class="icard__action icard__action--yahoo"
          :href="yahooUrl"
          target="_blank"
          rel="noopener"
          :title="t('table.yahooFinance')"
        >Y!</a>
        <button
          class="icard__action icard__action--refresh"
          :class="{ spin: refreshing }"
          :disabled="refreshing"
          :title="t('table.refresh')"
          @click="emit('refresh', item)"
        >↻</button>
        <button
          class="icard__action icard__action--remove"
          :title="t('table.remove')"
          @click="emit('remove', item)"
        >✕</button>
      </div>
    </div>

    <dl v-if="expanded" :id="detailsId" class="icard__details" :aria-label="t('table.details')">
      <dt>{{ t('table.colIsin') }}</dt>
      <dd>
        <span v-if="item.isin" class="mono">{{ item.isin }}</span>
        <IsinEditor v-else :symbol="item.symbol" @save="emit('set-isin', $event)" />
      </dd>
      <dt>{{ t('table.colTer') }}</dt>
      <dd class="mono">{{ formatPercent(item.ter) }}</dd>
      <dt>{{ t('table.colVola') }}</dt>
      <dd class="mono">{{ formatPercent(item.volatility) }}</dd>
      <dt>{{ t('table.colAccumulating') }}</dt>
      <dd>{{ accumulating(item.accumulating) }}</dd>
      <dt>{{ t('table.colPoints') }}</dt>
      <dd class="mono">{{ item.history_count }}</dd>
    </dl>
  </article>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.icard {
  padding: 0.85rem 0.9rem;
  margin: 0 0 0.6rem;
  &--selected { background: token(--accent, 0.12); box-shadow: inset 3px 0 0 $color-accent; }
}

.icard__head {
  display: grid;
  grid-template-columns: auto auto 1fr;
  align-items: center;
  gap: 0 0.5rem;
  cursor: pointer;
  min-height: 44px;
}

.icard__symbol { font-weight: 600; }

.icard__type {
  text-transform: uppercase;
  letter-spacing: 0.03em;
  &.etf { color: $color-accent; background: token(--accent, 0.15); }
  &.stock { color: $color-accent-2; background: token(--accent-2, 0.16); }
}

.icard__price {
  grid-column: 3;
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.icard__ccy { color: $color-muted; font-size: 0.75rem; margin-left: 0.2rem; }

.icard__name {
  grid-column: 1 / -1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: $color-muted;
}

.icard__foot {
  display: flex;
  align-items: center;
  // Toggle + Actions passen bei 375px-Breite nicht in eine Zeile (5×44px-Ziele
  // + Toggle > verfügbare Kartenbreite). Statt die Tap-Targets zu verkleinern
  // (nicht verhandelbar), bricht die Fußzeile um — Actions bleiben dank
  // justify-content dennoch rechtsbündig, solange genug Platz ist.
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 0.5rem;
  margin-top: 0.4rem;
}

.icard__toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  min-height: 44px;
  padding: 0 0.6rem;
  background: transparent;
  color: $color-muted;
  font-weight: 600;
  font-size: 0.8rem;
  &:hover { color: $color-accent; }
}
.icard__chevron {
  display: inline-block;
  transition: transform 0.12s ease;
  &--open { transform: rotate(180deg); }
}

.icard__actions {
  display: flex;
  gap: 0.3rem;
  align-items: center;
  // Sicherheitsnetz: auch die Actions selbst dürfen umbrechen (schmalere
  // Screens, längere Übersetzungen) statt die 44px-Ziele zu quetschen.
  flex-wrap: wrap;
  justify-content: flex-end;
}
.icard__action {
  min-height: 44px;
  min-width: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.2rem 0.5rem;
  border-radius: $radius;
  text-decoration: none;
  color: $color-accent;
  background: $color-surface-2;
  white-space: nowrap;
  &:hover:not(:disabled) { background: $color-accent; color: #fff; }
  &--remove:hover:not(:disabled) { background: $color-danger; color: #fff; }
  &--refresh.spin { animation: spin 0.7s linear infinite; color: $color-accent; }
}

.icard__details {
  margin: 0.6rem 0 0;
  padding-top: 0.5rem;
  border-top: 1px solid token(--border-default, 0.5);
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.3rem 0.6rem;
  font-size: 0.85rem;

  dt { color: $color-muted; }
  dd {
    margin: 0;
    text-align: right;
    font-variant-numeric: tabular-nums;
  }
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>
