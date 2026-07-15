<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'

import AppHeader from './components/AppHeader.vue'
import EnvironmentPanel from './components/EnvironmentPanel.vue'
import ErrorBanner from './components/ErrorBanner.vue'
import ExchangesPanel from './components/ExchangesPanel.vue'
import HistoryChart from './components/HistoryChart.vue'
import InstrumentsTable from './components/InstrumentsTable.vue'
import JsonModal from './components/JsonModal.vue'
import LinksPanel from './components/LinksPanel.vue'
import StatusBar from './components/StatusBar.vue'
import ThemesPanel from './components/ThemesPanel.vue'
import Toolbar from './components/Toolbar.vue'
import TopProgress from './components/TopProgress.vue'
import { useDaily } from './composables/useDaily'
import { useEnvironment } from './composables/useEnvironment'
import { useHashTab } from './composables/useHashTab'
import { useHealth } from './composables/useHealth'
import { useHistory } from './composables/useHistory'
import { useInstrumentActions } from './composables/useInstrumentActions'
import { useInstruments } from './composables/useInstruments'
import { useRefresh } from './composables/useRefresh'
import type { ErrorEntry, InstrumentSummary, RangeKey } from './types'

const { env, load: loadEnv } = useEnvironment()
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

const activeTab = useHashTab()
const selectedItem = ref<InstrumentSummary | null>(null)
const selectedRange = ref<RangeKey>('intraday')
const refreshingSymbol = ref<string | null>(null)
const jsonItem = ref<InstrumentSummary | null>(null)

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
  await Promise.all([loadEnv(), loadInstruments()])
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

async function onRemove(item: InstrumentSummary): Promise<void> {
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
  <AppHeader :active="activeTab" @navigate="activeTab = $event" />
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

    <ExchangesPanel v-else-if="activeTab === 'exchanges'" />
    <EnvironmentPanel v-else-if="activeTab === 'environment'" :env="env" />
    <LinksPanel v-else-if="activeTab === 'links'" />
    <ThemesPanel v-else />
  </main>

  <StatusBar :status="healthStatus" :version="healthVersion" />

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
</template>

<style scoped lang="scss">
@use './styles/variables' as *;

.content {
  max-width: 1200px;
  margin: 0 auto;
  padding: calc(#{$header-h} + 1.25rem) 1.25rem calc(#{$status-h} + 1.25rem);

  // Bei offenem Chart-Dock: Platz lassen, damit das Tabellenende erreichbar bleibt
  &.with-dock { padding-bottom: calc(#{$status-h} + 30vh + 7rem); }
}

.chart-dock {
  position: fixed;
  left: 0;
  right: 0;
  bottom: $status-h;
  z-index: 15;
  background: color-mix(in srgb, $color-bg 94%, transparent);
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
