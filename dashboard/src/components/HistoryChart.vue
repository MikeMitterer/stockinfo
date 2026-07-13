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

import type { QuotePoint } from '../types'

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler,
)

const props = defineProps<{ points: QuotePoint[]; currency: string | null }>()

const chartData = computed(() => {
  const ordered = [...props.points].reverse() // älteste zuerst
  return {
    labels: ordered.map((point) => point.quote_time),
    datasets: [
      {
        label: `Kurs${props.currency ? ` (${props.currency})` : ''}`,
        data: ordered.map((point) => point.price),
        borderColor: '#df5430',
        backgroundColor: 'rgba(223, 84, 48, 0.12)',
        pointBackgroundColor: '#df5430',
        pointRadius: 2,
        borderWidth: 2,
        tension: 0.25,
        fill: true,
      },
    ],
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { labels: { color: '#9a8fb0' } } },
  scales: {
    x: { ticks: { color: '#9a8fb0', maxTicksLimit: 8 }, grid: { color: 'rgba(56,44,70,0.5)' } },
    y: { ticks: { color: '#9a8fb0' }, grid: { color: 'rgba(56,44,70,0.5)' } },
  },
}
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
