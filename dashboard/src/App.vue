<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'

import AppHeader from './components/AppHeader.vue'
import EnvironmentPanel from './components/EnvironmentPanel.vue'
import ExchangesPanel from './components/ExchangesPanel.vue'
import HistoryChart from './components/HistoryChart.vue'
import InstrumentsTable from './components/InstrumentsTable.vue'
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
import type { InstrumentSummary, RangeKey } from './types'

const { env, load: loadEnv } = useEnvironment()
const { instruments, load: loadInstruments } = useInstruments()
const { points, load: loadHistory, loading: historyLoading } = useHistory()
const { daily, load: loadDaily, loading: dailyLoading } = useDaily()
const { refreshing, trigger } = useRefresh()
const { busy, add, refreshOne, remove } = useInstrumentActions()
const { status: healthStatus, version: healthVersion, start: startHealth, stop: stopHealth } =
  useHealth()

const activeTab = useHashTab()
const selectedItem = ref<InstrumentSummary | null>(null)
const selectedRange = ref<RangeKey>('intraday')
const refreshingSymbol = ref<string | null>(null)

const selectedSymbol = computed(() => selectedItem.value?.symbol ?? null)
const selectedCurrency = computed(() => selectedItem.value?.latest_currency ?? null)
const chartLoading = computed(() => historyLoading.value || dailyLoading.value)

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
  if (selectedItem.value?.symbol === item.symbol) {
    selectedItem.value = null
    points.value = []
    daily.value = []
  }
  await loadInstruments()
}
</script>

<template>
  <AppHeader :active="activeTab" @navigate="activeTab = $event" />
  <TopProgress :active="refreshing || busy" />

  <main class="content">
    <template v-if="activeTab === 'assets'">
      <Toolbar :refreshing="refreshing" :busy="busy" @refresh="onRefreshAll" @add="onAdd" />
      <InstrumentsTable
        :instruments="instruments"
        :selected-symbol="selectedSymbol"
        :refreshing-symbol="refreshingSymbol"
        @select="select"
        @refresh="onRefreshOne"
        @remove="onRemove"
      />
      <HistoryChart
        :series="chartSeries"
        :currency="selectedCurrency"
        :range="selectedRange"
        :loading="chartLoading"
        @range-change="onRangeChange"
      />
    </template>

    <ExchangesPanel v-else-if="activeTab === 'exchanges'" />
    <EnvironmentPanel v-else-if="activeTab === 'environment'" :env="env" />
    <LinksPanel v-else-if="activeTab === 'links'" />
    <ThemesPanel v-else />
  </main>

  <StatusBar :status="healthStatus" :version="healthVersion" />
</template>

<style scoped lang="scss">
@use './styles/variables' as *;

.content {
  max-width: 1200px;
  margin: 0 auto;
  padding: calc(#{$header-h} + 1.25rem) 1.25rem calc(#{$status-h} + 1.25rem);
}
</style>
