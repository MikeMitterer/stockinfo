<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'

import AppHeader from './components/AppHeader.vue'
import EnvironmentPanel from './components/EnvironmentPanel.vue'
import HistoryChart from './components/HistoryChart.vue'
import InstrumentsTable from './components/InstrumentsTable.vue'
import LinksPanel from './components/LinksPanel.vue'
import StatusBar from './components/StatusBar.vue'
import Toolbar from './components/Toolbar.vue'
import { useEnvironment } from './composables/useEnvironment'
import { useHealth } from './composables/useHealth'
import { useHistory } from './composables/useHistory'
import { useInstrumentActions } from './composables/useInstrumentActions'
import { useInstruments } from './composables/useInstruments'
import { useRefresh } from './composables/useRefresh'
import type { TabKey } from './types'

const { env, load: loadEnv } = useEnvironment()
const { instruments, load: loadInstruments } = useInstruments()
const { points, load: loadHistory } = useHistory()
const { refreshing, trigger } = useRefresh()
const { busy, add, refreshOne, remove } = useInstrumentActions()
const { status: healthStatus, version: healthVersion, start: startHealth, stop: stopHealth } =
  useHealth()

const activeTab = ref<TabKey>('instruments')
const selectedIsin = ref<string | null>(null)
const selectedCurrency = ref<string | null>(null)

onMounted(async () => {
  startHealth()
  await Promise.all([loadEnv(), loadInstruments()])
})

onUnmounted(() => stopHealth())

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
  <AppHeader :active="activeTab" @navigate="activeTab = $event" />

  <main class="content">
    <template v-if="activeTab === 'instruments'">
      <Toolbar :refreshing="refreshing" :busy="busy" @refresh="onRefreshAll" @add="onAdd" />
      <InstrumentsTable
        :instruments="instruments"
        :selected-isin="selectedIsin"
        @select="select"
        @refresh="onRefreshOne"
        @remove="onRemove"
      />
      <HistoryChart :points="points" :currency="selectedCurrency" />
    </template>

    <EnvironmentPanel v-else-if="activeTab === 'environment'" :env="env" />

    <LinksPanel v-else />
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
