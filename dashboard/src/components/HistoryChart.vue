<script setup lang="ts">
import {
  Chart as ChartJS,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  TimeScale,
  Title,
  Tooltip,
  type ChartData,
  type ChartOptions,
} from 'chart.js'
import 'chartjs-adapter-date-fns'
import { de as dateFnsDe, enUS as dateFnsEn } from 'date-fns/locale'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Line } from 'vue-chartjs'

import { useTheme } from '../composables/useTheme'
import type { RangeKey } from '../types'
import RangeSelector from './RangeSelector.vue'

ChartJS.register(
  TimeScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler,
)

const props = defineProps<{
  series: { x: number; y: number }[]
  currency: string | null
  symbol: string | null
  range: RangeKey
  loading: boolean
}>()

const emit = defineEmits<{
  (event: 'range-change', range: RangeKey): void
  (event: 'close'): void
}>()

const { current } = useTheme()
const { t, locale } = useI18n()

// Sprachabhängige Datumsformate für Achse und Tooltip.
const dateFormats = computed(() =>
  locale.value === 'de'
    ? {
        fnsLocale: dateFnsDe,
        tooltipIntraday: 'dd.MM. HH:mm',
        tooltipDay: 'dd.MM.yyyy',
        display: { hour: 'HH:mm', day: 'dd.MM', month: 'MM.yy' },
      }
    : {
        fnsLocale: dateFnsEn,
        tooltipIntraday: 'MMM d, HH:mm',
        tooltipDay: 'MM/dd/yyyy',
        display: { hour: 'HH:mm', day: 'MM/dd', month: 'MM/yy' },
      },
)

/** Liest eine CSS-Custom-Property vom <html> (mit Fallback). */
function cssVar(name: string, fallback: string): string {
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return value || fallback
}

const isIntraday = computed(() => props.range === 'intraday')

const chartData = computed<ChartData<'line'>>(() => {
  void current.value
  const accent = cssVar('--c-accent', '#df5430')
  return {
    datasets: [
      {
        label: `${t('chart.priceLabel')}${props.currency ? ` (${props.currency})` : ''}`,
        data: props.series,
        borderColor: accent,
        backgroundColor: `${accent}22`,
        pointBackgroundColor: accent,
        pointRadius: isIntraday.value ? 2 : 1.5,
        borderWidth: 2,
        tension: 0.2,
        fill: true,
      },
    ],
  }
})

const chartOptions = computed<ChartOptions<'line'>>(() => {
  void current.value
  const muted = cssVar('--c-muted', '#9a8fb0')
  const border = cssVar('--c-border', '#382c46')
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { labels: { color: muted } } },
    scales: {
      x: {
        type: 'time',
        adapters: { date: { locale: dateFormats.value.fnsLocale } },
        time: {
          unit: isIntraday.value ? 'hour' : 'day',
          tooltipFormat: isIntraday.value
            ? dateFormats.value.tooltipIntraday
            : dateFormats.value.tooltipDay,
          displayFormats: dateFormats.value.display,
        },
        ticks: { color: muted, maxTicksLimit: 8, autoSkip: true, maxRotation: 0 },
        grid: { color: border },
      },
      y: { ticks: { color: muted }, grid: { color: border } },
    },
  }
})
</script>

<template>
  <section class="chart card">
    <header class="head">
      <h2>
        {{ t('chart.title') }}<span v-if="symbol" class="sym"> — {{ symbol }}</span>
      </h2>
      <div class="tools">
        <RangeSelector :active="range" @change="emit('range-change', $event)" />
        <button class="x" :title="t('chart.close')" @click="emit('close')">✕</button>
      </div>
    </header>
    <p v-if="series.length === 0" class="empty">
      {{ loading ? t('chart.loading') : t('chart.empty') }}
    </p>
    <div v-else class="canvas">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </section>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.chart {
  // globale .card-Basis — kompakteres Padding wie die Assets-Tabelle
  padding: 1rem 1.1rem;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.75rem;
  h2 { margin: 0; }
  .sym { color: $color-muted; font-weight: 400; font-family: $font-mono; }
  .tools { display: flex; align-items: center; gap: 0.6rem; }
  .x { background: $color-surface-2; padding: 0.2rem 0.55rem; }
}

// Dock-tauglich: skaliert mit der Viewport-Höhe statt fixer 320px
.canvas { height: clamp(180px, 28vh, 300px); }
.empty { color: $color-muted; margin: 0.25rem 0 0; }
</style>
