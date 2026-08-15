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
import { accentColors } from '../utils/chartColors'
import { pctAxisBounds, periodChangePct, relChangePct } from '../utils/changePct'
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

// Prozentuale Veränderung erster → letzter Kurs im gewählten Zeitraum.
const changePct = computed(() => periodChangePct(props.series))

/** Formatiert einen Prozentwert lokalisiert mit Vorzeichen (z.B. „+2,34 %"). */
function fmtPct(value: number): string {
  return (
    value.toLocaleString(locale.value, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
      signDisplay: 'exceptZero',
    }) + ' %'
  )
}

// Pfeil zusätzlich zur Farbe — Farbe ist nie alleiniger Info-Träger.
const changeArrow = computed(() =>
  changePct.value === null || changePct.value === 0 ? '→' : changePct.value > 0 ? '▲' : '▼',
)
const changeClass = computed(() =>
  changePct.value === null || changePct.value === 0 ? 'flat' : changePct.value > 0 ? 'up' : 'down',
)
const changeText = computed(() => {
  const value = changePct.value
  return value === null ? '' : fmtPct(value)
})

const chartData = computed<ChartData<'line'>>(() => {
  void current.value
  const accentTriplet = cssVar('--accent', '242 103 63')
  // Tokens sind seit T-11b RGB-Tripel, kein Hex mehr — daher keine
  // Hex-Alpha-Verkettung (`${accent}22`) mehr, die war seit T-11b kaputt.
  const { solid: accent, fill } = accentColors(accentTriplet)
  return {
    datasets: [
      {
        label: `${t('chart.priceLabel')}${props.currency ? ` (${props.currency})` : ''}`,
        data: props.series,
        borderColor: accent,
        backgroundColor: fill,
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
  const muted = `rgb(${cssVar('--text-muted', '176 163 198')})`
  const border = `rgb(${cssVar('--border-default', '73 58 92')})`
  const bounds = pctAxisBounds(props.series)
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: muted } },
      tooltip: {
        callbacks: {
          // Zweite Tooltip-Zeile: Veränderung des Punkts gegenüber dem Startwert.
          afterLabel: (ctx) => {
            const first = props.series[0]?.y
            if (first === undefined) return ''
            const pct = relChangePct(first, ctx.parsed.y ?? Number.NaN)
            return pct === null ? '' : `${t('chart.vsStart')}: ${fmtPct(pct)}`
          },
        },
      },
    },
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
      y: {
        ticks: { color: muted },
        grid: { color: border },
        ...(bounds ? { min: bounds.yMin, max: bounds.yMax } : {}),
      },
      // Rechte Achse: dieselbe physische Spanne wie die Kursachse, aber in %
      // relativ zum ersten Punkt beschriftet.
      yPct: {
        position: 'right',
        ...(bounds ? { min: bounds.pctMin, max: bounds.pctMax } : {}),
        ticks: {
          color: muted,
          callback: (value) =>
            Number(value).toLocaleString(locale.value, {
              maximumFractionDigits: 1,
              signDisplay: 'exceptZero',
            }) + ' %',
        },
        grid: { drawOnChartArea: false }, // keine doppelten Gitterlinien
      },
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
        <span
          v-if="changePct !== null"
          class="change"
          :class="changeClass"
          :title="t('chart.periodChange')"
        >
          {{ changeArrow }} {{ changeText }}
        </span>
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

  // %-Veränderung über den Zeitraum — Vorzeichen + Pfeil, Farbe fix/semantisch
  .change {
    font-family: $font-mono;
    font-variant-numeric: tabular-nums;
    font-weight: 700;
    font-size: 0.9rem;
    padding: 0.1rem 0.5rem;
    border-radius: $radius;
    white-space: nowrap;
    &.up { color: $health-ok; background: token(--status-ok, 0.15); }
    &.down { color: $health-down; background: token(--status-out, 0.15); }
    &.flat { color: $color-muted; background: $color-surface-2; }
  }
}

// Dock-tauglich: skaliert mit der Viewport-Höhe statt fixer 320px
.canvas { height: clamp(180px, 28vh, 300px); }
.empty { color: $color-muted; margin: 0.25rem 0 0; }
</style>
