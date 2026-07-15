<script setup lang="ts">
import { ref, watch } from 'vue'

import { isIsin } from '../api/paths'
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

// Inline-Eingabe zum nachträglichen Erfassen einer ISIN
const editingSymbol = ref<string | null>(null)
const isinDraft = ref<string>('')
const isinInvalid = ref<boolean>(false)

// Fokussiert das Eingabefeld direkt beim Einblenden.
const vFocus = { mounted: (el: HTMLInputElement) => el.focus() }

// Fehlerhinweis zurücksetzen, sobald der Entwurf geändert wird.
watch(isinDraft, () => {
  isinInvalid.value = false
})

function startIsin(item: InstrumentSummary): void {
  editingSymbol.value = item.symbol
  isinDraft.value = ''
  isinInvalid.value = false
}

function cancelIsin(): void {
  editingSymbol.value = null
  isinDraft.value = ''
  isinInvalid.value = false
}

function confirmIsin(item: InstrumentSummary): void {
  const value = isinDraft.value.trim().toUpperCase()
  if (!value) {
    cancelIsin()
    return
  }
  if (!isIsin(value)) {
    isinInvalid.value = true // Hinweis zeigen, Eingabe offen lassen
    return
  }
  emit('set-isin', { symbol: item.symbol, isin: value })
  cancelIsin()
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

/** Formatiert einen Kurs mit zwei Nachkommastellen (oder '—'). */
function price(value: number | null): string {
  return value === null ? '—' : value.toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

/** Formatiert einen Prozentwert mit zwei Nachkommastellen (oder '—'). */
function formatPercent(value: number | null): string {
  return value === null ? '—' : `${value.toFixed(2)} %`
}

/** Thesaurierend-Anzeige: Ja / Nein / '—' bei unbekannt. */
function accumulating(value: boolean | null): string {
  if (value === null) return '—'
  return value ? 'Ja' : 'Nein'
}
</script>

<template>
  <section class="table card">
    <h2>Assets</h2>
    <p v-if="instruments.length === 0" class="empty">
      Noch keine Wertpapiere gecacht — oben per ISIN oder Symbol hinzufügen.
    </p>
    <div v-else class="scroll">
      <table class="data-table">
        <thead>
          <tr>
            <th>Symbol</th><th>ISIN</th><th>Name</th><th>Typ</th>
            <th class="num">Kurs</th><th class="num">TER</th><th class="num">Vola</th>
            <th class="center">Thes.</th><th class="num">Pkt.</th><th></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in instruments"
            :key="item.symbol"
            :class="{ selected: item.symbol === selectedSymbol }"
            @click="emit('select', item)"
          >
            <td class="sym mono">{{ item.symbol }}</td>
            <td class="mono dim isin-cell">
              <span v-if="item.isin">{{ item.isin }}</span>
              <span v-else-if="editingSymbol === item.symbol" class="isin-edit" @click.stop>
                <input
                  v-model="isinDraft"
                  v-focus
                  class="isin-input"
                  :class="{ invalid: isinInvalid }"
                  placeholder="ISIN eintragen"
                  @keyup.enter="confirmIsin(item)"
                  @keyup.esc="cancelIsin"
                />
                <button class="mini ok" title="Speichern" @click="confirmIsin(item)">✓</button>
                <button class="mini" title="Abbrechen" @click="cancelIsin">✕</button>
                <span v-if="isinInvalid" class="isin-err">ungültige ISIN</span>
              </span>
              <button v-else class="mini add" title="ISIN nachtragen" @click.stop="startIsin(item)">
                + ISIN
              </button>
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
              <button class="ext" title="JSON-Abfrage anzeigen" @click="emit('json', item)">JSON</button>
              <a
                v-if="extraetfLink(item)"
                class="ext"
                :href="extraetfLink(item)"
                target="_blank"
                rel="noopener"
                title="extraETF-Profil"
              >eETF</a>
              <a
                v-if="yahooLink(item)"
                class="ext"
                :href="yahooLink(item)"
                target="_blank"
                rel="noopener"
                title="Yahoo Finance"
              >Y!</a>
              <button
                class="icon"
                :class="{ spin: item.symbol === refreshingSymbol }"
                :disabled="item.symbol === refreshingSymbol"
                title="Aktualisieren"
                @click="emit('refresh', item)"
              >↻</button>
              <button class="icon danger" title="Löschen" @click="emit('remove', item)">✕</button>
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

.empty { color: $color-muted; margin: 0.25rem 0 0; }
.scroll { overflow-x: auto; }

thead th { font-weight: 600; }
tbody td { padding: 0.5rem 0.7rem; border-bottom: 1px solid rgba(56, 44, 70, 0.5); }
tbody tr {
  cursor: pointer;
  transition: background 0.1s ease;
  &:hover { background: $color-surface-2; }
  &.selected { background: color-mix(in srgb, $color-accent 12%, transparent); box-shadow: inset 3px 0 0 $color-accent; }
}

.num { text-align: right; }
.center { text-align: center; }
.dim { color: $color-muted; }

.badge.thes {
  color: $color-muted;
  background: $color-surface-2;
  &.acc { color: $color-accent; background: color-mix(in srgb, $color-accent 15%, transparent); }
}
.sym { font-weight: 600; }
.name { max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ccy { color: $color-muted; font-size: 0.75rem; margin-left: 0.2rem; }

.isin-cell { white-space: nowrap; }
.isin-edit { display: inline-flex; align-items: center; gap: 0.25rem; }
.isin-input {
  width: 140px;
  padding: 0.15rem 0.4rem;
  border-radius: 6px;
  border: 1px solid $color-accent;
  background: $color-bg;
  color: $color-text;
  font-family: $font-mono;
  font-size: 0.8rem;
  &:focus { outline: none; }
}
.mini {
  padding: 0.12rem 0.45rem;
  font-size: 0.72rem;
  background: $color-surface-2;
  &.add { color: $color-muted; }
  &.add:hover { color: $color-accent; }
  &.ok { color: $health-ok; }
}
.isin-input.invalid { border-color: $color-danger; }
.isin-err { color: $color-danger; font-size: 0.72rem; white-space: nowrap; }

// Varianten der globalen .badge-Pill
.badge.type {
  text-transform: uppercase;
  letter-spacing: 0.03em;
  &.etf { color: $color-accent; background: color-mix(in srgb, $color-accent 15%, transparent); }
  &.stock { color: $color-accent-2; background: color-mix(in srgb, $color-accent-2 16%, transparent); }
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
