<script setup lang="ts">
import {
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Title,
  Tooltip,
} from 'chart.js'
import { computed } from 'vue'
import { Line } from 'vue-chartjs'

import { useTheme } from '../composables/useTheme'
import type { QuotePoint } from '../types'

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler,
)

const props = defineProps<{ points: QuotePoint[]; currency: string | null }>()
const { current } = useTheme()

/** Liest eine CSS-Custom-Property vom <html> (mit Fallback). */
function cssVar(name: string, fallback: string): string {
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return value || fallback
}

const chartData = computed(() => {
  void current.value // neu berechnen bei Theme-Wechsel
  const accent = cssVar('--c-accent', '#df5430')
  const ordered = [...props.points].reverse() // älteste zuerst
  return {
    labels: ordered.map((point) => point.quote_time),
    datasets: [
      {
        label: `Kurs${props.currency ? ` (${props.currency})` : ''}`,
        data: ordered.map((point) => point.price),
        borderColor: accent,
        backgroundColor: `${accent}22`,
        pointBackgroundColor: accent,
        pointRadius: 2,
        borderWidth: 2,
        tension: 0.25,
        fill: true,
      },
    ],
  }
})

const chartOptions = computed(() => {
  void current.value
  const muted = cssVar('--c-muted', '#9a8fb0')
  const border = cssVar('--c-border', '#382c46')
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { labels: { color: muted } } },
    scales: {
      x: { ticks: { color: muted, maxTicksLimit: 8 }, grid: { color: border } },
      y: { ticks: { color: muted }, grid: { color: border } },
    },
  }
})
</script>

<template>
  <section class="chart card">
    <h2>Kurshistorie</h2>
    <p v-if="points.length === 0" class="empty">Kein Instrument gewählt oder keine Historie.</p>
    <div v-else class="canvas">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </section>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.card {
  background: $color-surface;
  border: 1px solid $color-border;
  border-radius: $radius;
  padding: 1rem 1.1rem;
}

.canvas { height: 320px; }
.empty { color: $color-muted; margin: 0.25rem 0 0; }
</style>
