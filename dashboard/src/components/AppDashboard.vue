<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { UxAppShell, useNotifier } from '@mikemitterer/ux-foundation'

import AnalysisPanel from './AnalysisPanel.vue'
import AppHeader from './AppHeader.vue'
import ConfirmDeleteDialog from './ConfirmDeleteDialog.vue'
import ExchangesPanel from './ExchangesPanel.vue'
import FxPanel from './FxPanel.vue'
import HistoryChart from './HistoryChart.vue'
import InstrumentsTable from './InstrumentsTable.vue'
import JsonModal from './JsonModal.vue'
import SettingsPanel from './SettingsPanel.vue'
import StatusBar from './StatusBar.vue'
import Toolbar from './Toolbar.vue'
import TopProgress from './TopProgress.vue'
import { useDaily } from '../composables/useDaily'
import { useEnvironment } from '../composables/useEnvironment'
import { useExchanges } from '../composables/useExchanges'
import { useHashTab } from '../composables/useHashTab'
import { useHealth } from '../composables/useHealth'
import { useHistory } from '../composables/useHistory'
import { useInstrumentActions } from '../composables/useInstrumentActions'
import { useInstruments } from '../composables/useInstruments'
import { useOverrides } from '../composables/useOverrides'
import { useRefresh } from '../composables/useRefresh'
import type { InstrumentOverrides, InstrumentSummary, RangeKey } from '../types'
import { currenciesFromExchanges } from '../utils/currencies'

/**
 * Der eigentliche Inhalt des Dashboards.
 *
 * Getrennt von `App.vue`, weil `useNotifier()` einen `NNotificationProvider`
 * **über** sich braucht — in derselben Komponente, die den Provider erst im
 * Template aufspannt, findet `useNotification()` ihn nicht. `App.vue` ist
 * damit der Rahmen (Theme-Brücke, Provider), diese Komponente der Inhalt.
 */

const { t } = useI18n()

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
const { saving: savingSymbol, save: saveOverrides, error: overridesError } = useOverrides()
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

/*
 * Fehler aller Composables als Toast — nicht als Banner im Textfluss: Eine
 * Meldung zwischen Kopf und Tabelle schiebt beim Erscheinen alles nach unten,
 * und man klickt daneben.
 *
 * Die Anzeigedauer ist fest `0` — Fehler bleiben stehen, bis sie weggeklickt
 * werden. Ein Zähler wäre erst dann sinnvoll, wenn es hier eine Einstellung
 * dafür gäbe; bis dahin wäre eine Zahl im Code eine geratene.
 *
 * Die Beschriftung des Zählers wird trotzdem mitgegeben: Das Fundament hat
 * keinen Katalog und verlangt sie deshalb, statt ein deutsches Wort fest zu
 * verdrahten. Sichtbar wird sie erst, wenn die Anzeigedauer über 0 geht.
 */
const { notify } = useNotifier(ref(0), (n) => t('errors.closesIn', { n }))

const errorSources: Record<string, typeof instrumentsError> = {
  instruments: instrumentsError,
  actions: actionsError,
  history: historyError,
  daily: dailyError,
  refresh: refreshError,
  overrides: overridesError,
}

for (const source of Object.values(errorSources)) {
  notify(
    computed(() => source.value !== null),
    {
      title: t('errors.title'),
      type: 'error',
      // Die Meldung selbst steht schon übersetzt in der Ref — die Composables
      // legen sie beim Fehlschlag ab.
      content: () => source.value ?? '',
    },
  )
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

/**
 * Trägt eine von Hand gepflegte Kennzahl ein und lädt die Liste neu.
 *
 * Das Neuladen ist nicht optional: Ob der eingetragene Wert tatsächlich
 * angezeigt wird, entscheidet die Vorrang-Regel im Backend — und die Antwort
 * darauf steht in der Liste, nicht in der Eingabe.
 */
async function onOverride(payload: {
  item: InstrumentSummary
  patch: Partial<InstrumentOverrides>
}): Promise<void> {
  await saveOverrides(payload.item, payload.patch)
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
    Der Rahmen kommt aus dem Fundament. `position: sticky` allein hält die
    Statuszeile **nicht** unten: Sticky greift nur, solange der umschließende
    Block sichtbar ist — auf einer kurzen Seite (etwa den Einstellungen) endet
    die Leiste dort, wo der Inhalt endet, mitten im Bild. Die Shell macht die
    Spalte mindestens fensterhoch und lässt den Inhalt wachsen.
  -->
  <UxAppShell>
    <template #topbar>
      <AppHeader
        :active="activeTab"
        :refreshing="refreshing"
        @navigate="activeTab = $event"
        @refresh="onRefreshAll"
      />
    </template>

    <TopProgress :active="refreshing || busy" />

    <main class="content" :class="{ 'with-dock': selectedItem && activeTab === 'assets' }">
      <template v-if="activeTab === 'assets'">
        <Toolbar :busy="busy" @add="onAdd" />
        <InstrumentsTable
          :instruments="instruments"
          :selected-symbol="selectedSymbol"
          :refreshing-symbol="refreshingSymbol"
          :saving-symbol="savingSymbol"
          :extraetf-etf-url="env?.extraetf_etf_url ?? ''"
          :extraetf-stock-url="env?.extraetf_stock_url ?? ''"
          :yahoo-url="env?.yahoo_url ?? ''"
          @select="select"
          @refresh="onRefreshOne"
          @remove="onRemove"
          @set-isin="onSetIsin"
          @override="onOverride"
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
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

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
