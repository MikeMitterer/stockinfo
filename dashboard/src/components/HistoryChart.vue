<script setup lang="ts">
import {
  CategoryScale,
  Chart as ChartJS,
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
  CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend,
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
        borderColor: '#38bdf8',
        tension: 0.2,
      },
    ],
  }
})

const chartOptions = { responsive: true, maintainAspectRatio: false }
</script>

<template>
  <section class="chart">
    <h2>Kurshistorie</h2>
    <p v-if="points.length === 0" class="empty">Kein Instrument gewählt oder keine Historie.</p>
    <div v-else class="canvas">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </section>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.chart {
  background: $color-surface;
  border-radius: $radius;
  padding: 1rem;

  .canvas { height: 320px; }
  .empty { color: $color-muted; }
}
</style>
