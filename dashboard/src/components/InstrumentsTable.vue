<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { NButton, NSelect } from 'naive-ui'

import { UxCaret, useIsCompact } from '@mmit/ux-foundation'
import { useTableSort, type SortKey } from '../composables/useTableSort'
import InfoHint from './InfoHint.vue'
import InstrumentCard from './InstrumentCard.vue'
import InstrumentDrilldown from './InstrumentDrilldown.vue'
import IsinEditor from './IsinEditor.vue'
import MetricValue from './MetricValue.vue'
import type { InstrumentOverrides, InstrumentSummary, OverrideField } from '../types'

const props = defineProps<{
  instruments: InstrumentSummary[]
  selectedSymbol: string | null
  refreshingSymbol: string | null
  /** Papier, dessen manuelle Kennzahlen gerade gespeichert werden. */
  savingSymbol: string | null
  extraetfEtfUrl: string
  extraetfStockUrl: string
  yahooUrl: string
  /** Vorschläge je Textfeld für die Schublade — einmal weiter oben gebildet. */
  fieldOptions?: Partial<Record<OverrideField, string[]>>
}>()

const emit = defineEmits<{
  (event: 'select', item: InstrumentSummary): void
  (event: 'refresh', item: InstrumentSummary): void
  (event: 'remove', item: InstrumentSummary): void
  (event: 'set-isin', payload: { symbol: string; isin: string }): void
  (event: 'json', item: InstrumentSummary): void
  (
    event: 'override',
    payload: { item: InstrumentSummary; patch: Partial<InstrumentOverrides> },
  ): void
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

/*
 * Die Schublade (Task 8): höchstens eine gleichzeitig offen, gehalten über das
 * Symbol des Papiers — nicht über einen Index, der bei jeder Umsortierung ein
 * anderes Papier träfe.
 */
const openSymbol = ref<string | null>(null)

/** Ist die Schublade dieses Papiers gerade offen? */
function isOpen(item: InstrumentSummary): boolean {
  return openSymbol.value === item.symbol
}

/**
 * Öffnet/schließt die Schublade eines Papiers — ausgelöst von Symbol oder Name.
 *
 * Eigener Name statt `toggle`: Das ist schon die Spaltensortierung von
 * `useTableSort()`, ein zweiter `toggle` für etwas ganz anderes wäre hier
 * verwirrend.
 */
function toggleDrawer(item: InstrumentSummary): void {
  openSymbol.value = isOpen(item) ? null : item.symbol
}

/**
 * Naive UI meldet eine offene Auswahlliste über diese Klasse am Feld.
 *
 * Sie ist im Browser gemessen, nicht aus der Dokumentation abgeschrieben:
 * geschlossen trägt das Feld `n-base-selection`, offen zusätzlich
 * `n-base-selection--active`. Dass hier ein fremder Klassenname steht, ist der
 * Preis dafür, dass Naive den Zustand sonst nirgends nach außen gibt — weder
 * über `aria-expanded` noch über ein Event. Benennt Naive sie um, fällt der
 * zugehörige Test, nicht die Oberfläche: Die Schublade schlösse dann wieder
 * eine Taste zu früh.
 */
const NAIVE_SELECT_OPEN = 'n-base-selection--active'

/**
 * War beim letzten Escape eine Auswahlliste offen?
 *
 * Der Umweg über ein Merkfeld ist **erzwungen**, und zwar durch eine Messung:
 * Naive schließt die Liste in der Ziel-Phase, also nach dem Capture und vor
 * jedem Handler weiter oben. Am Wurzelelement angekommen ist die Klasse
 * bereits weg — dort lässt sich nicht mehr feststellen, dass gerade eine Liste
 * zuging.
 *
 * | Phase                     | Liste offen |
 * |---------------------------|-------------|
 * | `document`, Capture       | ja          |
 * | `section`, Capture        | ja          |
 * | `section`, Bubble         | **nein**    |
 *
 * Also wird im Capture gemerkt und im Bubble entschieden. Beides in den
 * Capture zu ziehen geht nicht: `defaultPrevented` von `UxInlineNumber` steht
 * dort noch nicht, das Feld setzt es erst am Ziel.
 */
let selectWasOpen = false

/** Hält im Capture fest, was im Bubble nicht mehr zu sehen ist. */
function onEscapeCapture(event: KeyboardEvent): void {
  selectWasOpen =
    event.target instanceof Element && event.target.closest(`.${NAIVE_SELECT_OPEN}`) !== null
}

/**
 * Escape schließt die offene Schublade — der Ausweg, den die Teststrategie
 * verlangt.
 *
 * Der Handler sitzt am Wurzelelement der Komponente, nicht am `document`:
 * Öffnen und Schließen betreffen nur diese Tabelle, und ein globaler Listener
 * müsste eigens wieder abgeräumt werden. Aus dem Knopf wie aus der Schublade
 * steigt die Taste ohnehin hierher hoch.
 *
 * Zwei Dinge halten die Schublade offen, und sie prüfen dasselbe auf zwei
 * Wegen, weil die Bedienelemente sich unterschiedlich verhalten:
 *
 * 1. `defaultPrevented` — so meldet sich `UxInlineNumber`, das mit Escape
 *    seinen Entwurf verwirft.
 * 2. Eine **offene** Auswahlliste darüber, festgehalten in `selectWasOpen`.
 *    Die vier Textfelder der Schublade (Anbieter, Replikationsart,
 *    Fondsdomizil, Fondswährung) sind `NSelect`, und Naive ruft bei Escape
 *    kein `preventDefault()` — die Taste stieg unverbraucht hierher hoch und
 *    nahm Liste und Schublade auf einmal weg.
 *
 * Gemerkt wird ausdrücklich **offen**, nicht „kam aus einem Auswahlfeld": Bei
 * geschlossener Liste gehört die Taste wieder der Schublade, sonst käme man
 * mit dem Fokus im Feld per Tastatur nicht mehr heraus.
 */
function onEscape(event: KeyboardEvent): void {
  const listeWarOffen = selectWasOpen
  selectWasOpen = false

  if (event.defaultPrevented) return
  if (listeWarOffen) return
  openSymbol.value = null
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


</script>

<template>
  <section class="table card" @keydown.esc.capture="onEscapeCapture" @keydown.esc="onEscape">
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
          :saving="item.symbol === savingSymbol"
          :extraetf-url="extraetfLink(item)"
          :yahoo-url="yahooLink(item)"
          :field-options="fieldOptions"
          @select="emit('select', $event)"
          @refresh="emit('refresh', $event)"
          @remove="emit('remove', $event)"
          @json="emit('json', $event)"
          @set-isin="emit('set-isin', $event)"
          @override="emit('override', { item, patch: $event })"
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
              <!--
                `@click.stop`: Der Spaltenkopf sortiert bei jedem Klick — ohne
                das würde schon das Antippen des Fragezeichens die Tabelle
                umsortieren.
              -->
              <span v-if="column.key === 'history_count'" class="th-hint" @click.stop>
                <InfoHint :text="t('hints.points')" settings-tab="environment" />
              </span>
              <span v-if="sortKey === column.key" class="arrow">
                {{ direction === 'asc' ? '▲' : '▼' }}
              </span>
            </th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <template v-for="item in sortedInstruments" :key="item.symbol">
            <tr
              :class="{ selected: item.symbol === selectedSymbol }"
              @click="emit('select', item)"
            >
              <td class="sym mono">
                <!--
                  Kennung öffnet die Zeile (ux-standards): Symbol und Name sind
                  eigene Schaltflächen und klinken sich mit `@click.stop` aus dem
                  Zeilen-Klick aus — der bleibt fürs Chart zuständig.
                -->
                <button
                  type="button"
                  class="row-toggle"
                  :aria-expanded="isOpen(item)"
                  :aria-controls="`drawer-${item.symbol}`"
                  @click.stop="toggleDrawer(item)"
                >
                  <UxCaret :open="isOpen(item)" />{{ item.symbol }}
                </button>
              </td>
              <td class="mono dim isin-cell">
                <span v-if="item.isin">{{ item.isin }}</span>
                <IsinEditor v-else :symbol="item.symbol" @save="emit('set-isin', $event)" />
              </td>
              <td class="name">
                <button
                  type="button"
                  class="row-toggle"
                  :aria-expanded="isOpen(item)"
                  :aria-controls="`drawer-${item.symbol}`"
                  @click.stop="toggleDrawer(item)"
                >
                  {{ item.name ?? '—' }}
                </button>
              </td>
              <td>
                <span v-if="item.type" class="badge type" :class="item.type">{{ item.type }}</span>
                <span v-else class="dim">—</span>
              </td>
              <td class="num mono">
                {{ price(item.latest_price) }}
                <span class="ccy">{{ item.latest_currency ?? '' }}</span>
              </td>
              <!--
                Die drei Kennzahlen sind hier nur noch zu sehen (T-09) — gepflegt
                wird in der aufklappbaren Zeile (Task 8), nicht mehr an Ort und
                Stelle in der Zelle.
              -->
              <td class="num mono dim"><MetricValue :item="item" field="ter" /></td>
              <td class="num mono dim"><MetricValue :item="item" field="volatility" /></td>
              <td class="center"><MetricValue :item="item" field="accumulating" /></td>
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
                <NButton
                  v-if="extraetfLink(item)"
                  class="ext"
                  tag="a"
                  size="tiny"
                  quaternary
                  :href="extraetfLink(item)"
                  target="_blank"
                  rel="noopener"
                  :title="t('table.extraetfProfile')"
                >
                  eETF
                </NButton>
                <NButton
                  v-if="yahooLink(item)"
                  class="ext"
                  tag="a"
                  size="tiny"
                  quaternary
                  :href="yahooLink(item)"
                  target="_blank"
                  rel="noopener"
                  :title="t('table.yahooFinance')"
                >
                  Y!
                </NButton>
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
            <tr v-if="isOpen(item)" :id="`drawer-${item.symbol}`" class="drawer-row">
              <td :colspan="columns.length + 1">
                <InstrumentDrilldown
                  :item="item"
                  :busy="item.symbol === savingSymbol"
                  :field-options="fieldOptions"
                  @commit="emit('override', { item, patch: $event })"
                />
              </td>
            </tr>
          </template>
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

// `.visually-hidden` stand hier als scoped Kopie — die Annahme „im Projekt
// bislang keine geteilte Fassung vorhanden" stimmte schon damals nicht:
// `@mmit/ux-foundation/styles/reset.css` bringt die Klasse global mit (via
// `main.ts` geladen). Das Sortier-`<label>`, für das sie gedacht war, gibt es
// seit dem Umbau auf `NSelect` ohnehin nicht mehr.

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

// Nichts als die Ausrichtung: Größe, Fläche und Rundung bringt der Knopf
// selbst mit. Hier standen vorher Farbe, Hintergrund, Radius und ein
// negatives Margin — damit war er eine zweite Sorte Knopf und stand
// sichtbar höher als die Auswahl daneben.
.tsort__dir {
  flex: none;
}

thead th { font-weight: 600; }
thead th.sortable {
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
  &:hover { color: $color-accent; }
  .arrow { color: $color-accent; font-size: 0.6rem; }
  // Der Hinweis sortiert nicht — also auch kein Sortier-Zeiger darüber.
  .th-hint { cursor: default; margin-left: 0.25rem; }
}
/*
 * Etwas enger als sonst, und das ist gemessen: Mit `nowrap` in den
 * Zahlenspalten und dem Fragezeichen an „Pkt." brauchte die Tabelle 1150 px bei
 * 1123 verfügbaren — die letzten 27 px klemmten ausgerechnet den Löschen-Knopf
 * ab. Zehn Spalten mal 0.3 rem holen das zurück, ohne dass die Zeile gedrängt
 * aussieht.
 */
tbody td { padding: 0.5rem 0.55rem; border-bottom: 1px solid token(--border-default, 0.5); }
thead th { padding-inline: 0.55rem; }
tbody tr {
  cursor: pointer;
  transition: background 0.1s ease;
  &:hover { background: $color-surface-2; }
  &.selected { background: token(--accent, 0.12); box-shadow: inset 3px 0 0 $color-accent; }
}

/*
 * Zahlenspalten brechen nicht um. Ohne das drückt jede Spalte, die etwas
 * breiter wird — das Fragezeichen an „Pkt." reicht schon —, den Kurs auf zwei
 * Zeilen: die Zahl oben, die Währung darunter. Passt die Tabelle dann nicht
 * mehr, rollt sie waagrecht (`.scroll`), statt die Zahlen zu zerlegen.
 */
.num { text-align: right; white-space: nowrap; }
.center { text-align: center; }
.dim { color: $color-muted; }

.badge.thes {
  color: $color-muted;
  background: $color-surface-2;
  &.acc { color: $color-accent; background: token(--accent, 0.15); }
}
.sym { font-weight: 600; }
.name { max-width: 260px; }
.ccy { color: $color-muted; font-size: 0.75rem; margin-left: 0.2rem; }

.isin-cell { white-space: nowrap; }

/*
 * Kennung öffnet die Zeile (ux-standards): ein zurückgesetzter Knopf, der wie
 * der bisherige Text aussieht — Markierung erst beim Überfahren/Fokus, eine
 * gepunktete Linie statt einer dauerhaften Unterstreichung. Bei zwanzig Zeilen
 * wäre jede Kennung sonst ein durchgehend blauer Verweis.
 */
.row-toggle {
  display: inline;
  max-width: 100%;
  border: none;
  background: none;
  padding: 0;
  margin: 0;
  font: inherit;
  color: inherit;
  text-align: left;
  cursor: pointer;

  &:hover, &:focus-visible {
    text-decoration: underline dotted;
    text-underline-offset: 0.2em;
  }
}

/*
 * Aussehen und Drehung des Pfeils stehen in `UxCaret` (Fundament) — hier nur,
 * was die Umgebung angeht: Abstand zur Kennung und die Akzentfarbe. Das Symbol
 * zeichnet in `currentColor`, damit jede Umgebung selbst entscheidet.
 *
 * `display: inline-block` am Pfeil hält die gepunktete Linie des Knopfes von
 * ihm fern: Ein atomarer Kasten erbt die Unterstreichung des Textes nicht.
 */
.row-toggle .ux-caret {
  margin-right: 0.3rem;
  color: $color-accent;
}

// In der Namensspalte übernimmt der Knopf die Kürzung, die vorher an der
// Zelle selbst hing — die Zelle bleibt nur noch der Breitenrahmen dafür.
.name .row-toggle {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

// Die Schublade (Task 8): eigene Zeile unter der Instrumentenzeile, über die
// volle Spaltenbreite. Kein Zeilen-Hover/-Klick wie bei der Instrumentenzeile
// — sie öffnet nichts, es gibt nichts zu klicken außer den Bedienelementen
// darin.
.drawer-row {
  cursor: default;
  &:hover { background: none; }

  td {
    padding: 0;
    border-bottom: 1px solid token(--border-default, 0.5);
  }
}

// Varianten der globalen .badge-Pill
.badge.type {
  text-transform: uppercase;
  letter-spacing: 0.03em;
  &.etf { color: $color-accent; background: token(--accent, 0.15); }
  &.stock { color: $color-stock; background: token(--asset-stocks, 0.16); }
}

.actions { display: flex; gap: 0.3rem; justify-content: flex-end; align-items: center; }

@keyframes spin { to { transform: rotate(360deg); } }
</style>
