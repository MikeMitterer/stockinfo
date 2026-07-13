<script setup lang="ts">
import { onMounted, ref } from 'vue'

import EnvironmentPanel from './components/EnvironmentPanel.vue'
import HistoryChart from './components/HistoryChart.vue'
import InstrumentsTable from './components/InstrumentsTable.vue'
import LinksPanel from './components/LinksPanel.vue'
import Toolbar from './components/Toolbar.vue'
import { useEnvironment } from './composables/useEnvironment'
import { useHistory } from './composables/useHistory'
import { useInstrumentActions } from './composables/useInstrumentActions'
import { useInstruments } from './composables/useInstruments'
import { useRefresh } from './composables/useRefresh'

const { env, load: loadEnv } = useEnvironment()
const { instruments, load: loadInstruments } = useInstruments()
const { points, load: loadHistory } = useHistory()
const { refreshing, trigger } = useRefresh()
const { busy, add, refreshOne, remove } = useInstrumentActions()

const selectedIsin = ref<string | null>(null)
const selectedCurrency = ref<string | null>(null)

onMounted(async () => {
  await Promise.all([loadEnv(), loadInstruments()])
})

async function select(isin: string): Promise<void> {
  selectedIsin.value = isin
  selectedCurrency.value =
    instruments.value.find((item) => item.isin === isin)?.latest_currency ?? null
  await loadHistory(isin)
}

async function onRefreshAll(): Promise<void> {
  await trigger()
  await loadInstruments()
}

async function onAdd(identifier: string): Promise<void> {
  await add(identifier)
  await loadInstruments()
}

async function onRefreshOne(isin: string): Promise<void> {
  await refreshOne(isin)
  await loadInstruments()
  if (selectedIsin.value === isin) await loadHistory(isin)
}

async function onRemove(isin: string): Promise<void> {
  await remove(isin)
  if (selectedIsin.value === isin) {
    selectedIsin.value = null
    points.value = []
  }
  await loadInstruments()
}
</script>

<template>
  <main class="app">
    <h1>StockInfo Dashboard</h1>
    <Toolbar :refreshing="refreshing" :busy="busy" @refresh="onRefreshAll" @add="onAdd" />
    <EnvironmentPanel :env="env" />
    <LinksPanel />
    <InstrumentsTable
      :instruments="instruments"
      :selected-isin="selectedIsin"
      @select="select"
      @refresh="onRefreshOne"
      @remove="onRemove"
    />
    <HistoryChart :points="points" :currency="selectedCurrency" />
  </main>
</template>

<style scoped lang="scss">
@use './styles/variables' as *;

.app {
  max-width: 1100px;
  margin: 0 auto;
  padding: 1.5rem;

  h1 { color: $color-accent; }
}
</style>
