<script setup lang="ts">
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
}>()

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

/** Formatiert die TER als Prozent (oder '—'). */
function ter(value: number | null): string {
  return value === null ? '—' : `${value.toFixed(2)} %`
}
</script>

<template>
  <section class="table card">
    <h2>Assets</h2>
    <p v-if="instruments.length === 0" class="empty">
      Noch keine Wertpapiere gecacht — oben per ISIN oder Symbol hinzufügen.
    </p>
    <div v-else class="scroll">
      <table>
        <thead>
          <tr>
            <th>Symbol</th><th>ISIN</th><th>Name</th><th>Typ</th>
            <th class="num">Kurs</th><th class="num">TER</th><th class="num">Pkt.</th><th></th>
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
            <td class="mono dim">{{ item.isin ?? '—' }}</td>
            <td class="name">{{ item.name ?? '—' }}</td>
            <td>
              <span v-if="item.type" class="badge" :class="item.type">{{ item.type }}</span>
              <span v-else class="dim">—</span>
            </td>
            <td class="num mono">
              {{ price(item.latest_price) }}
              <span class="ccy">{{ item.latest_currency ?? '' }}</span>
            </td>
            <td class="num mono dim">{{ ter(item.ter) }}</td>
            <td class="num mono dim">{{ item.history_count }}</td>
            <td class="actions" @click.stop>
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

.card {
  background: $color-surface;
  border: 1px solid $color-border;
  border-radius: $radius;
  padding: 1rem 1.1rem;
  margin: 0 0 1.1rem;
}

.empty { color: $color-muted; margin: 0.25rem 0 0; }
.scroll { overflow-x: auto; }

table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
thead th {
  text-align: left;
  padding: 0.35rem 0.7rem;
  color: $color-muted;
  font-weight: 600;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border-bottom: 1px solid $color-border;
}
tbody td { padding: 0.5rem 0.7rem; border-bottom: 1px solid rgba(56, 44, 70, 0.5); }
tbody tr {
  cursor: pointer;
  transition: background 0.1s ease;
  &:hover { background: $color-surface-2; }
  &.selected { background: color-mix(in srgb, $color-accent 12%, transparent); box-shadow: inset 3px 0 0 $color-accent; }
}

.num { text-align: right; }
.dim { color: $color-muted; }
.sym { font-weight: 600; }
.name { max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ccy { color: $color-muted; font-size: 0.75rem; margin-left: 0.2rem; }

.badge {
  display: inline-block;
  padding: 0.1rem 0.5rem;
  border-radius: 999px;
  font-size: 0.68rem;
  font-weight: 700;
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
