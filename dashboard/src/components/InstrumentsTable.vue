<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { NButton, NSelect } from 'naive-ui'

import { useIsCompact } from '@mikemitterer/ux-foundation'
import { useTableSort, type SortKey } from '../composables/useTableSort'
import InstrumentCard from './InstrumentCard.vue'
import IsinEditor from './IsinEditor.vue'
import type { InstrumentSummary } from '../types'

const props = defineProps<{
  instruments: InstrumentSummary[]
  selectedSymbol: string | null
  refreshingSymbol: string | null
  extraetfEtfUrl: string
  extraetfStockUrl: string
  yahooUrl: string
}>()

const emit = defineEmits<{
  (event: 'select', item: InstrumentSummary): void
  (event: 'refresh', item: InstrumentSummary): void
  (event: 'remove', item: InstrumentSummary): void
  (event: 'set-isin', payload: { symbol: string; isin: string }): void
  (event: 'json', item: InstrumentSummary): void
}>()

const { t, locale } = useI18n()

const compact = useIsCompact()

const { sortKey, direction, toggle, setSortKey, setDirection, sort, init: initSort } = useTableSort()
initSort()

// Sortierbare Spaltenköpfe (Label-Key aus dem Katalog + optionale Zellklasse).
const columns: { key: SortKey; label: string; align?: string }[] = [
  { key: 'symbol', label: 'table.colSymbol' },
  { key: 'isin', label: 'table.colIsin' },
  { key: 'name', label: 'table.colName' },
  { key: 'type', label: 'table.colType' },
  { key: 'latest_price', label: 'table.colPrice', align: 'num' },
  { key: 'ter', label: 'table.colTer', align: 'num' },
  { key: 'volatility', label: 'table.colVola', align: 'num' },
  { key: 'accumulating', label: 'table.colAccumulating', align: 'center' },
  { key: 'history_count', label: 'table.colPoints', align: 'num' },
]

const sortedInstruments = computed(() => sort(props.instruments))

/**
 * Auswahlliste der mobilen Sortierzeile.
 *
 * Der erste Eintrag ist der Leerlauf: Ohne ihn ließe sich eine einmal gesetzte
 * Sortierung nicht mehr abschalten. Er trägt den leeren Wert, damit die
 * Auswahl ihn als „nichts gewählt" zeigt.
 */
const sortOptions = computed(() => [
  { value: '', label: t('table.sortNone') },
  ...columns.map((column) => ({ value: column.key, label: t(column.label) })),
])

/**
 * Kehrt die Sortierrichtung in der Kartenansicht um (nur auf/ab). `toggle()`
 * kann das nicht liefern — bei gleichbleibendem Schlüssel schaltet es beim
 * zweiten Aufruf die Sortierung ganz aus, was ein eigener Richtungsknopf
 * nicht soll. `setDirection()` persistiert dabei wie ein Header-Klick.
 */
function toggleSortDirection(): void {
  setDirection(direction.value === 'asc' ? 'desc' : 'asc')
}

/** Übernimmt die Auswahl der mobilen Sortierleiste (leer = aus). */
function onSortSelect(value: string): void {
  setSortKey(value === '' ? null : (value as SortKey))
}

/** Baut den extraETF-Profil-Link (ISIN-basiert, ETF/Stock unterschieden). */
function extraetfLink(item: InstrumentSummary): string {
  if (!item.isin) return ''
  const template = item.type === 'etf' ? props.extraetfEtfUrl : props.extraetfStockUrl
  return template ? template.replace('{isin}', item.isin) : ''
}

/** Baut den Yahoo-Finance-Link (Symbol-basiert). */
function yahooLink(item: InstrumentSummary): string {
  return props.yahooUrl ? props.yahooUrl.replace('{symbol}', item.symbol) : ''
}

/** Formatiert einen Kurs mit zwei Nachkommastellen (oder '—'), sprachabhängig. */
function price(value: number | null): string {
  return value === null
    ? '—'
    : value.toLocaleString(locale.value, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

/** Formatiert einen Prozentwert mit zwei Nachkommastellen (oder '—'). */
function formatPercent(value: number | null): string {
  return value === null ? '—' : `${value.toFixed(2)} %`
}

/** Thesaurierend-Anzeige: Ja / Nein / '—' bei unbekannt. */
function accumulating(value: boolean | null): string {
  if (value === null) return '—'
  return value ? t('table.yes') : t('table.no')
}
</script>

<template>
  <section class="table card">
    <div class="table__head" :class="{ 'table__head--compact': compact }">
      <h2>{{ t('table.title') }}</h2>
      <div v-if="compact && instruments.length > 0" class="tsort">
        <!--
          Naives Auswahlliste statt eines nativen `select`: Sie bringt Tastatur
          und Beschriftung selbst mit, und die Oberfläche bleibt in einer
          Formensprache. Die frühere Lösung legte ein transparentes `select`
          über einen eigenen Trigger — zwei Elemente für eine Aufgabe.
        -->
        <NSelect
          class="tsort__select"
          size="small"
          :value="sortKey ?? ''"
          :options="sortOptions"
          :aria-label="t('table.sortBy')"
          @update:value="onSortSelect"
        />
        <NButton
          v-if="sortKey !== null"
          class="tsort__dir"
          size="small"
          :title="direction === 'asc' ? t('table.sortAsc') : t('table.sortDesc')"
          @click="toggleSortDirection"
        >
          {{ direction === 'asc' ? '▲' : '▼' }}
        </NButton>
      </div>
    </div>
    <p v-if="instruments.length === 0" class="empty">
      {{ t('table.empty') }}
    </p>
    <template v-else-if="compact">
      <div class="cards">
        <InstrumentCard
          v-for="item in sortedInstruments"
          :key="item.symbol"
          :item="item"
          :selected="item.symbol === selectedSymbol"
          :refreshing="item.symbol === refreshingSymbol"
          :extraetf-url="extraetfLink(item)"
          :yahoo-url="yahooLink(item)"
          @select="emit('select', $event)"
          @refresh="emit('refresh', $event)"
          @remove="emit('remove', $event)"
          @json="emit('json', $event)"
          @set-isin="emit('set-isin', $event)"
        />
      </div>
    </template>
    <div v-else class="scroll">
      <table class="data-table">
        <thead>
          <tr>
            <th
              v-for="column in columns"
              :key="column.key"
              class="sortable"
              :class="column.align"
              :aria-sort="
                sortKey === column.key
                  ? direction === 'asc' ? 'ascending' : 'descending'
                  : undefined
              "
              @click="toggle(column.key)"
            >
              {{ t(column.label) }}
              <span v-if="sortKey === column.key" class="arrow">
                {{ direction === 'asc' ? '▲' : '▼' }}
              </span>
            </th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in sortedInstruments"
            :key="item.symbol"
            :class="{ selected: item.symbol === selectedSymbol }"
            @click="emit('select', item)"
          >
            <td class="sym mono">{{ item.symbol }}</td>
            <td class="mono dim isin-cell">
              <span v-if="item.isin">{{ item.isin }}</span>
              <IsinEditor v-else :symbol="item.symbol" @save="emit('set-isin', $event)" />
            </td>
            <td class="name">{{ item.name ?? '—' }}</td>
            <td>
              <span v-if="item.type" class="badge type" :class="item.type">{{ item.type }}</span>
              <span v-else class="dim">—</span>
            </td>
            <td class="num mono">
              {{ price(item.latest_price) }}
              <span class="ccy">{{ item.latest_currency ?? '' }}</span>
            </td>
            <td class="num mono dim">{{ formatPercent(item.ter) }}</td>
            <td class="num mono dim">{{ formatPercent(item.volatility) }}</td>
            <td class="center">
              <span v-if="item.accumulating !== null" class="badge thes" :class="{ acc: item.accumulating }">
                {{ accumulating(item.accumulating) }}
              </span>
              <span v-else class="dim">—</span>
            </td>
            <td class="num mono dim">{{ item.history_count }}</td>
            <td class="actions" @click.stop>
              <NButton
                class="ext"
                size="tiny"
                quaternary
                :title="t('table.showJson')"
                @click="emit('json', item)"
              >
                JSON
              </NButton>
              <a
                v-if="extraetfLink(item)"
                class="ext"
                :href="extraetfLink(item)"
                target="_blank"
                rel="noopener"
                :title="t('table.extraetfProfile')"
              >eETF</a>
              <a
                v-if="yahooLink(item)"
                class="ext"
                :href="yahooLink(item)"
                target="_blank"
                rel="noopener"
                :title="t('table.yahooFinance')"
              >Y!</a>
              <NButton
                class="icon"
                size="tiny"
                quaternary
                :loading="item.symbol === refreshingSymbol"
                :disabled="item.symbol === refreshingSymbol"
                :title="t('table.refresh')"
                @click="emit('refresh', item)"
              >
                ↻
              </NButton>
              <NButton
                class="icon"
                size="tiny"
                quaternary
                type="error"
                :title="t('table.remove')"
                @click="emit('remove', item)"
              >
                ✕
              </NButton>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.table {
  // globale .card-Basis — kompakteres Padding + Abstand zum Chart darunter
  padding: 1rem 1.1rem;
  margin: 0 0 1.1rem;
}

// Kopfzeile der Komponente (Überschrift + ggf. Sortierzeile). Ab Desktop bleibt
// dies ein reiner Block-Wrapper ohne eigene Margin/Padding — die h2 sieht
// exakt so aus wie zuvor (globale Regel aus base.scss, hier unangetastet).
// Erst in der Kartenansicht (T-11c-Feedback) wird daraus eine Flex-Zeile,
// damit die Sortierzeile rechts neben statt unter der Überschrift sitzt.
.table__head--compact {
  display: flex;
  // Icon + Text der Sortierzeile liegen selbst in einem inline-flex und haben
  // keine sauber gemeinsame Baseline mit der h2 — vertikal zentriert liest
  // sich verlässlicher als eine zusammengehörige Zeile.
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.empty { color: $color-muted; margin: 0.25rem 0 0; }
.scroll { overflow-x: auto; }

.cards { display: flex; flex-direction: column; }

// Utility fürs Sortier-<label>: bleibt für Screenreader vorhanden, ist aber
// visuell nicht vorhanden — nur ⇅-Symbol + Spaltenname tragen die Bedeutung
// für sehende Nutzer. Im Projekt bislang keine geteilte Fassung vorhanden,
// deshalb hier lokal (scoped) statt in variables.scss/base.scss ergänzt.
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

// Leise, rechtsbündige Zeile statt Formularleiste (T-11c). Die Auswahl selbst
// bringt ihre Gestaltung von Naive UI mit — hier steht nur, wo sie sitzt und
// wie breit sie sein darf.
.tsort {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  // Sitzt jetzt als Flex-Item in .table__head--compact neben der h2 —
  // keine eigene Außen-Margin mehr nötig, der Abstand zu den Karten darunter
  // kommt weiterhin von der (unveränderten) globalen h2-Margin.
  flex: none;
  max-width: 100%;
}

.tsort__select {
  // Ohne feste Breite schrumpft die Auswahl im Flex-Container auf ihren
  // Mindestinhalt — von "Marktwert" bliebe ein "M".
  width: 11rem;
}

.tsort__dir {
  flex: none;
  min-height: 44px;
  min-width: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: none;
  color: $color-muted;
  border-radius: $radius;
  font-size: 0.8rem;
  transition: background 0.1s ease, color 0.1s ease;
  // Gleicher Grund wie beim Trigger: 44px Trefferfläche bleibt, zählt aber
  // nicht komplett für die Höhe der Kopfzeile.
  margin: -0.5rem 0;
  &:hover { background: $color-surface-2; color: $color-text; }
}

thead th { font-weight: 600; }
thead th.sortable {
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
  &:hover { color: $color-accent; }
  .arrow { color: $color-accent; font-size: 0.6rem; }
}
tbody td { padding: 0.5rem 0.7rem; border-bottom: 1px solid token(--border-default, 0.5); }
tbody tr {
  cursor: pointer;
  transition: background 0.1s ease;
  &:hover { background: $color-surface-2; }
  &.selected { background: token(--accent, 0.12); box-shadow: inset 3px 0 0 $color-accent; }
}

.num { text-align: right; }
.center { text-align: center; }
.dim { color: $color-muted; }

.badge.thes {
  color: $color-muted;
  background: $color-surface-2;
  &.acc { color: $color-accent; background: token(--accent, 0.15); }
}
.sym { font-weight: 600; }
.name { max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ccy { color: $color-muted; font-size: 0.75rem; margin-left: 0.2rem; }

.isin-cell { white-space: nowrap; }

// Varianten der globalen .badge-Pill
.badge.type {
  text-transform: uppercase;
  letter-spacing: 0.03em;
  &.etf { color: $color-accent; background: token(--accent, 0.15); }
  &.stock { color: $color-stock; background: token(--asset-stocks, 0.16); }
}

.actions { display: flex; gap: 0.3rem; justify-content: flex-end; align-items: center; }
.ext {
  font-size: 0.68rem;
  font-weight: 700;
  padding: 0.2rem 0.4rem;
  border-radius: 6px;
  text-decoration: none;
  color: $color-accent;
  background: $color-surface-2;
  white-space: nowrap;
  &:hover { background: $color-accent; color: #fff; }
}
.icon {
  padding: 0.2rem 0.5rem;
  background: $color-surface-2;
  &.danger:hover { background: $color-danger; color: #fff; }
  &.spin { animation: spin 0.7s linear infinite; color: $color-accent; }
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>
