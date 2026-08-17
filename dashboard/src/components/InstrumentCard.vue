<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { NButton } from 'naive-ui'

import InstrumentDrilldown from './InstrumentDrilldown.vue'
import IsinEditor from './IsinEditor.vue'
import type { InstrumentOverrides, InstrumentSummary, OverrideField } from '../types'

const props = defineProps<{
  item: InstrumentSummary
  selected: boolean
  refreshing: boolean
  extraetfUrl: string
  yahooUrl: string
  /** Wird gerade gespeichert? Dann nichts anfassen. */
  saving: boolean
  /** Vorschläge je Textfeld für die Schublade — einmal weiter oben gebildet. */
  fieldOptions?: Partial<Record<OverrideField, string[]>>
}>()

const emit = defineEmits<{
  (event: 'select', item: InstrumentSummary): void
  (event: 'refresh', item: InstrumentSummary): void
  (event: 'remove', item: InstrumentSummary): void
  (event: 'json', item: InstrumentSummary): void
  (event: 'set-isin', payload: { symbol: string; isin: string }): void
  (event: 'override', patch: Partial<InstrumentOverrides>): void
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

/*
 * Die beiden Formatierer standen hier als „Mirror von InstrumentsTable" — also
 * zweimal dieselbe Regel. Beide sind mit `ManualMetric` weggefallen: Dort steht
 * die Darstellung einer Kennzahl jetzt an genau einer Stelle.
 */
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
      <NButton
        class="icard__toggle"
        quaternary
        size="small"
        :aria-expanded="expanded"
        :aria-controls="detailsId"
        @click.stop="toggle"
      >
        <span class="icard__chevron" :class="{ 'icard__chevron--open': expanded }">⌄</span>
        {{ expanded ? t('table.less') : t('table.more') }}
      </NButton>

      <div class="icard__actions" @click.stop>
        <NButton
          class="icard__action icard__action--json"
          size="tiny"
          quaternary
          :title="t('table.showJson')"
          @click="emit('json', item)"
        >
          JSON
        </NButton>
        <NButton
          v-if="extraetfUrl"
          class="icard__action icard__action--extraetf"
          tag="a"
          size="tiny"
          quaternary
          :href="extraetfUrl"
          target="_blank"
          rel="noopener"
          :title="t('table.extraetfProfile')"
        >
          eETF
        </NButton>
        <NButton
          v-if="yahooUrl"
          class="icard__action icard__action--yahoo"
          tag="a"
          size="tiny"
          quaternary
          :href="yahooUrl"
          target="_blank"
          rel="noopener"
          :title="t('table.yahooFinance')"
        >
          Y!
        </NButton>
        <NButton
          class="icard__action icard__action--refresh"
          size="tiny"
          quaternary
          :loading="refreshing"
          :disabled="refreshing"
          :title="t('table.refresh')"
          @click="emit('refresh', item)"
        >
          ↻
        </NButton>
        <NButton
          class="icard__action icard__action--remove"
          size="tiny"
          quaternary
          type="error"
          :title="t('table.remove')"
          @click="emit('remove', item)"
        >
          ✕
        </NButton>
      </div>
    </div>

    <div v-if="expanded" :id="detailsId" class="icard__expanded">
      <!--
        Auch mobil bearbeitbar: „Voll bedienbar ist die Vorgabe" — eine reine
        Leseansicht bräuchte einen Grund, und den gibt es hier nicht.
      -->
      <dl class="icard__details" :aria-label="t('table.details')">
        <dt>{{ t('table.colIsin') }}</dt>
        <dd>
          <span v-if="item.isin" class="mono">{{ item.isin }}</span>
          <IsinEditor v-else :symbol="item.symbol" @save="emit('set-isin', $event)" />
        </dd>
        <dt>{{ t('table.colPoints') }}</dt>
        <dd class="mono">{{ item.history_count }}</dd>
      </dl>

      <!--
        Dieselbe Schublade wie am Schreibtisch (Task 8) — acht Felder statt
        der bisherigen drei `ManualMetric`, an derselben Stelle wie bisher.
      -->
      <InstrumentDrilldown
        :item="item"
        :busy="saving"
        :field-options="fieldOptions"
        @commit="emit('override', $event)"
      />
    </div>
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
}

.icard__symbol { font-weight: 600; }

.icard__type {
  text-transform: uppercase;
  letter-spacing: 0.03em;
  &.etf { color: $color-accent; background: token(--accent, 0.15); }
  &.stock { color: $color-stock; background: token(--asset-stocks, 0.16); }
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
  // Bei 375 px passen Toggle und Aktionen nicht in eine Zeile. Statt die
  // Trefferflächen zu quetschen, bricht die Fußzeile um — rechtsbündig
  // bleiben die Aktionen trotzdem, solange Platz ist.
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 0.5rem;
  margin-top: 0.4rem;
}

// Nur der Abstand zum Pfeil — alles Übrige ist Sache des Knopfes.
.icard__toggle {
  gap: 0.3rem;
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
  // Sicherheitsnetz: auch die Aktionen selbst dürfen umbrechen — schmalere
  // Schirme, längere Übersetzungen.
  flex-wrap: wrap;
  justify-content: flex-end;
}

// Umschließt die Detail-Liste (ISIN, Pkt.) und die Schublade darunter — trägt
// die Trennlinie zum Kopf der Karte, die vorher an `.icard__details` selbst hing.
.icard__expanded {
  margin: 0.6rem 0 0;
  padding-top: 0.5rem;
  border-top: 1px solid token(--border-default, 0.5);
}

.icard__details {
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
