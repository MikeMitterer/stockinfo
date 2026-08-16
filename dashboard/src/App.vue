<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  NConfigProvider,
  NDialogProvider,
  NMessageProvider,
  NNotificationProvider,
  darkTheme,
  dateDeDE,
  dateEnUS,
  deDE,
  enUS,
  type GlobalThemeOverrides,
} from 'naive-ui'
import { buildNaiveOverrides, THEMES, UxAppShell } from '@mikemitterer/ux-foundation'

import { useTheme } from './composables/useTheme'
import AnalysisPanel from './components/AnalysisPanel.vue'
import AppHeader from './components/AppHeader.vue'
import ConfirmDeleteDialog from './components/ConfirmDeleteDialog.vue'
import ErrorBanner from './components/ErrorBanner.vue'
import ExchangesPanel from './components/ExchangesPanel.vue'
import FxPanel from './components/FxPanel.vue'
import HistoryChart from './components/HistoryChart.vue'
import InstrumentsTable from './components/InstrumentsTable.vue'
import JsonModal from './components/JsonModal.vue'
import SettingsPanel from './components/SettingsPanel.vue'
import StatusBar from './components/StatusBar.vue'
import Toolbar from './components/Toolbar.vue'
import TopProgress from './components/TopProgress.vue'
import { useDaily } from './composables/useDaily'
import { useEnvironment } from './composables/useEnvironment'
import { useExchanges } from './composables/useExchanges'
import { useHashTab } from './composables/useHashTab'
import { useHealth } from './composables/useHealth'
import { useHistory } from './composables/useHistory'
import { useInstrumentActions } from './composables/useInstrumentActions'
import { useInstruments } from './composables/useInstruments'
import { useRefresh } from './composables/useRefresh'
import type { ErrorEntry, InstrumentSummary, RangeKey } from './types'
import { currenciesFromExchanges } from './utils/currencies'

const { locale } = useI18n()
const { current: currentTheme } = useTheme()

/*
 * Die Brücke zu Naive UI: Aus den Token dieser Seite werden dessen Overrides
 * gebaut. Die Richtung ist verbindlich — die Token sind die Quelle, Naive der
 * Verbraucher. Dass zur Laufzeit per `getComputedStyle` gelesen wird, ist
 * erzwungen: Naive rechnet Hover- und Pressed-Zustände selbst aus der
 * Grundfarbe und kann ein `var(--accent)` nicht auflösen.
 */
/*
 * Beim ersten Bild **synchron** gelesen: `main.ts` setzt `data-theme`, bevor
 * die App eingehängt wird, die Werte stehen also schon. Wartete man hier auf
 * `requestAnimationFrame`, blitzte für ein Bild Naives eigenes Grün auf, bevor
 * der Akzent der Palette greift.
 */
const naiveOverrides = ref<GlobalThemeOverrides>(buildNaiveOverrides())
const isDark = computed(() => THEMES[currentTheme.value].isDark)

/*
 * Naive mitziehen: Seine eingebauten Beschriftungen — „Bestätigen",
 * „Abbrechen" in jeder Rückfrage — kämen sonst englisch heraus, während die
 * Oberfläche deutsch ist.
 */
const naiveLocale = computed(() => (locale.value === 'de' ? deDE : enUS))
const naiveDateLocale = computed(() => (locale.value === 'de' ? dateDeDE : dateEnUS))

watch(currentTheme, () => {
  // Beim Wechsel erst im nächsten Bild lesen: `data-theme` muss am Element
  // stehen, bevor `getComputedStyle` die neuen Werte liefert.
  requestAnimationFrame(() => {
    naiveOverrides.value = buildNaiveOverrides()
  })
})

const { env, load: loadEnv } = useEnvironment()
const { data: exchanges, load: loadExchanges } = useExchanges()
const fxCurrencies = computed(() => currenciesFromExchanges(exchanges.value))
const { instruments, load: loadInstruments, error: instrumentsError } = useInstruments()
const {
  load: loadHistory,
  loading: historyLoading,
  clear: clearHistory,
  error: historyError,
  points,
} = useHistory()
const {
  load: loadDaily,
  loading: dailyLoading,
  clear: clearDaily,
  error: dailyError,
  daily,
} = useDaily()
const { refreshing, trigger, error: refreshError } = useRefresh()
const { busy, add, refreshOne, remove, setIsin, error: actionsError } = useInstrumentActions()
const { status: healthStatus, version: healthVersion, start: startHealth, stop: stopHealth } =
  useHealth()

const { tab: activeTab, settingsTab } = useHashTab()
const selectedItem = ref<InstrumentSummary | null>(null)
const selectedRange = ref<RangeKey>('intraday')
const refreshingSymbol = ref<string | null>(null)
const jsonItem = ref<InstrumentSummary | null>(null)
const pendingRemoval = ref<InstrumentSummary | null>(null)

const selectedSymbol = computed(() => selectedItem.value?.symbol ?? null)
const selectedCurrency = computed(() => selectedItem.value?.latest_currency ?? null)
const chartLoading = computed(() => historyLoading.value || dailyLoading.value)

// Fehler aller Composables als dismissible Banner-Einträge.
const errorSources = {
  instruments: instrumentsError,
  actions: actionsError,
  history: historyError,
  daily: dailyError,
  refresh: refreshError,
}

const errors = computed<ErrorEntry[]>(() =>
  Object.entries(errorSources)
    .filter(([, source]) => source.value !== null)
    .map(([key, source]) => ({ key, message: source.value ?? '' })),
)

/** Blendet einen Banner-Fehler aus, indem die zugehörige error-Ref geleert wird. */
function dismissError(key: string): void {
  const source = errorSources[key as keyof typeof errorSources]
  if (source) source.value = null
}

// Einheitliche Chart-Serie {x = Zeit (ms), y = Kurs} aus Intraday-Ticks oder EOD.
const chartSeries = computed<{ x: number; y: number }[]>(() => {
  if (selectedRange.value === 'intraday') {
    return [...points.value]
      .reverse()
      .map((point) => ({ x: Date.parse(point.quote_time), y: point.price }))
  }
  return daily.value.map((point) => ({ x: Date.parse(point.date), y: point.close }))
})

onMounted(async () => {
  startHealth()
  await Promise.all([loadEnv(), loadInstruments(), loadExchanges()])
})

onUnmounted(() => stopHealth())

async function loadChart(): Promise<void> {
  const item = selectedItem.value
  if (!item) return
  const range = selectedRange.value
  if (range === 'intraday') {
    await loadHistory(item)
  } else {
    await loadDaily(item, range)
  }
}

async function select(item: InstrumentSummary): Promise<void> {
  selectedItem.value = item
  await loadChart()
}

async function onRangeChange(range: RangeKey): Promise<void> {
  selectedRange.value = range
  await loadChart()
}

async function onRefreshAll(): Promise<void> {
  await trigger()
  await loadInstruments()
}

async function onAdd(identifier: string): Promise<void> {
  await add(identifier)
  await loadInstruments()
}

async function onSetIsin(payload: { symbol: string; isin: string }): Promise<void> {
  await setIsin(payload.symbol, payload.isin)
  await loadInstruments()
}

async function onRefreshOne(item: InstrumentSummary): Promise<void> {
  refreshingSymbol.value = item.symbol
  try {
    await refreshOne(item)
    await loadInstruments()
    if (selectedItem.value?.symbol === item.symbol) await loadChart()
  } finally {
    refreshingSymbol.value = null
  }
}

// Löschen ist unwiderruflich (Kurshistorie geht mit verloren) — daher erst Rückfrage
// im ConfirmDeleteDialog, bevor tatsächlich gelöscht wird (T-11i).
function onRemove(item: InstrumentSummary): void {
  pendingRemoval.value = item
}

async function confirmRemoval(): Promise<void> {
  const item = pendingRemoval.value
  if (!item) return
  pendingRemoval.value = null
  await remove(item)
  if (selectedItem.value?.symbol === item.symbol) closeChart()
  await loadInstruments()
}

/** Schließt das Chart-Dock und verwirft die geladene Historie. */
function closeChart(): void {
  selectedItem.value = null
  clearHistory()
  clearDaily()
}
</script>

<template>
  <!--
    Ein Rahmen um alles: `inline-theme-disabled`, weil Naive seine Variablen
    sonst an jedes Element schreibt und der Theme-Wechsel sichtbar langsam wird.
    Die Provider stehen hier, damit Toasts und Rückfragen überall erreichbar
    sind.
  -->
  <NConfigProvider
    :locale="naiveLocale"
    :date-locale="naiveDateLocale"
    :theme="isDark ? darkTheme : null"
    :theme-overrides="naiveOverrides"
    inline-theme-disabled
  >
  <NMessageProvider>
  <NDialogProvider>
  <NNotificationProvider :max="3">
  <!--
    Der Rahmen kommt aus dem Fundament. `position: sticky` allein hält die
    Statuszeile **nicht** unten: Sticky greift nur, solange der umschließende
    Block sichtbar ist — auf einer kurzen Seite (etwa den Einstellungen) endet
    die Leiste dort, wo der Inhalt endet, mitten im Bild. Die Shell macht die
    Spalte mindestens fensterhoch und lässt den Inhalt wachsen.
  -->
  <UxAppShell>
    <template #topbar>
      <AppHeader :active="activeTab" @navigate="activeTab = $event" />
    </template>

  <TopProgress :active="refreshing || busy" />

  <main class="content" :class="{ 'with-dock': selectedItem && activeTab === 'assets' }">
    <ErrorBanner :errors="errors" @dismiss="dismissError" />
    <template v-if="activeTab === 'assets'">
      <Toolbar :refreshing="refreshing" :busy="busy" @refresh="onRefreshAll" @add="onAdd" />
      <InstrumentsTable
        :instruments="instruments"
        :selected-symbol="selectedSymbol"
        :refreshing-symbol="refreshingSymbol"
        :extraetf-etf-url="env?.extraetf_etf_url ?? ''"
        :extraetf-stock-url="env?.extraetf_stock_url ?? ''"
        :yahoo-url="env?.yahoo_url ?? ''"
        @select="select"
        @refresh="onRefreshOne"
        @remove="onRemove"
        @set-isin="onSetIsin"
        @json="jsonItem = $event"
      />
    </template>

    <ExchangesPanel v-else-if="activeTab === 'exchanges'" :data="exchanges" />
    <AnalysisPanel v-else-if="activeTab === 'analysis'" :instruments="instruments" />
    <FxPanel v-else-if="activeTab === 'fx'" :currencies="fxCurrencies" />
    <SettingsPanel v-else-if="activeTab === 'settings'" v-model:tab="settingsTab" :env="env" />
  </main>

    <template #statusbar>
      <StatusBar
        :status="healthStatus"
        :version="healthVersion"
        :instrument-count="instruments.length"
        @open-status="activeTab = 'settings'"
      />
    </template>

  <!-- Chart-Dock: erscheint bei Zeilen-Auswahl am unteren Rand, über der StatusBar -->
  <div v-if="selectedItem && activeTab === 'assets'" class="chart-dock">
    <HistoryChart
      :series="chartSeries"
      :currency="selectedCurrency"
      :symbol="selectedSymbol"
      :range="selectedRange"
      :loading="chartLoading"
      @range-change="onRangeChange"
      @close="closeChart"
    />
  </div>

  <JsonModal :item="jsonItem" @close="jsonItem = null" />
  <ConfirmDeleteDialog
    :item="pendingRemoval"
    @confirm="confirmRemoval"
    @cancel="pendingRemoval = null"
  />
  </UxAppShell>
  </NNotificationProvider>
  </NDialogProvider>
  </NMessageProvider>
  </NConfigProvider>
</template>

<style scoped lang="scss">
@use './styles/variables' as *;

.content {
  max-width: 1200px;
  margin: 0 auto;
  /*
   * Kein Ausgleich mehr für die Leisten: Sie standen früher per `position:
   * fixed` über dem Inhalt, jetzt hält die Shell sie als Spalte — der Inhalt
   * beginnt und endet von selbst an der richtigen Stelle.
   */
  padding: 1.25rem;

  // Bei offenem Chart-Dock: Platz lassen, damit das Tabellenende erreichbar bleibt
  &.with-dock { padding-bottom: calc(30vh + 7rem); }
}

.chart-dock {
  position: fixed;
  left: 0;
  right: 0;
  bottom: $status-h;
  z-index: 15;
  background: token(--surface-page, 0.94);
  backdrop-filter: blur(8px);
  border-top: 1px solid $color-border;
  padding: 0.6rem 1.25rem 0.75rem;

  // Card-Chrome des Charts im Dock neutralisieren — das Dock ist der Rahmen
  :deep(.chart) {
    border: none;
    background: transparent;
    padding: 0;
    margin: 0;
    max-width: 1200px;
    margin-inline: auto;
  }
}
</style>
