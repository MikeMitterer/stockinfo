<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'

import AppHeader from './components/AppHeader.vue'
import EnvironmentPanel from './components/EnvironmentPanel.vue'
import HistoryChart from './components/HistoryChart.vue'
import InstrumentsTable from './components/InstrumentsTable.vue'
import LinksPanel from './components/LinksPanel.vue'
import StatusBar from './components/StatusBar.vue'
import ThemesPanel from './components/ThemesPanel.vue'
import Toolbar from './components/Toolbar.vue'
import TopProgress from './components/TopProgress.vue'
import { useEnvironment } from './composables/useEnvironment'
import { useHealth } from './composables/useHealth'
import { useHistory } from './composables/useHistory'
import { useInstrumentActions } from './composables/useInstrumentActions'
import { useInstruments } from './composables/useInstruments'
import { useRefresh } from './composables/useRefresh'
import type { InstrumentSummary, TabKey } from './types'

const { env, load: loadEnv } = useEnvironment()
const { instruments, load: loadInstruments } = useInstruments()
const { points, load: loadHistory } = useHistory()
const { refreshing, trigger } = useRefresh()
const { busy, add, refreshOne, remove } = useInstrumentActions()
const { status: healthStatus, version: healthVersion, start: startHealth, stop: stopHealth } =
  useHealth()

const activeTab = ref<TabKey>('instruments')
const selectedSymbol = ref<string | null>(null)
const selectedCurrency = ref<string | null>(null)
const refreshingSymbol = ref<string | null>(null)

onMounted(async () => {
  startHealth()
  await Promise.all([loadEnv(), loadInstruments()])
})

onUnmounted(() => stopHealth())

async function select(item: InstrumentSummary): Promise<void> {
  selectedSymbol.value = item.symbol
  selectedCurrency.value = item.latest_currency
  await loadHistory(item)
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
    if (selectedSymbol.value === item.symbol) {
      const updated = instruments.value.find((entry) => entry.symbol === item.symbol)
      if (updated) await loadHistory(updated)
    }
  } finally {
    refreshingSymbol.value = null
  }
}

async function onRemove(item: InstrumentSummary): Promise<void> {
  await remove(item)
  if (selectedSymbol.value === item.symbol) {
    selectedSymbol.value = null
    points.value = []
  }
  await loadInstruments()
}
</script>

<template>
  <AppHeader :active="activeTab" @navigate="activeTab = $event" />
  <TopProgress :active="refreshing || busy" />

  <main class="content">
    <template v-if="activeTab === 'instruments'">
      <Toolbar :refreshing="refreshing" :busy="busy" @refresh="onRefreshAll" @add="onAdd" />
      <InstrumentsTable
        :instruments="instruments"
        :selected-symbol="selectedSymbol"
        :refreshing-symbol="refreshingSymbol"
        @select="select"
        @refresh="onRefreshOne"
        @remove="onRemove"
      />
      <HistoryChart :points="points" :currency="selectedCurrency" />
    </template>

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
