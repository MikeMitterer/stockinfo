<script setup lang="ts">
import type { InstrumentSummary } from '../types'

defineProps<{ instruments: InstrumentSummary[]; selectedIsin: string | null }>()

const emit = defineEmits<{
  (event: 'select', isin: string): void
  (event: 'refresh', isin: string): void
  (event: 'remove', isin: string): void
}>()
</script>

<template>
  <section class="table">
    <h2>Instrumente</h2>
    <table>
      <thead>
        <tr>
          <th>Symbol</th><th>ISIN</th><th>Name</th><th>Typ</th>
          <th>Kurs</th><th>TER</th><th>Punkte</th><th></th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="item in instruments"
          :key="item.symbol"
          :class="{ selected: item.isin === selectedIsin }"
          @click="item.isin && emit('select', item.isin)"
        >
          <td>{{ item.symbol }}</td>
          <td>{{ item.isin ?? '—' }}</td>
          <td>{{ item.name ?? '—' }}</td>
          <td>{{ item.type ?? '—' }}</td>
          <td>{{ item.latest_price ?? '—' }} {{ item.latest_currency ?? '' }}</td>
          <td>{{ item.ter ?? '—' }}</td>
          <td>{{ item.history_count }}</td>
          <td class="actions" @click.stop>
            <button v-if="item.isin" @click="emit('refresh', item.isin)">↻</button>
            <button v-if="item.isin" class="danger" @click="emit('remove', item.isin)">✕</button>
          </td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.table {
  background: $color-surface;
  border-radius: $radius;
  padding: 1rem;
  margin: 1rem 0;
  overflow-x: auto;

  table { width: 100%; border-collapse: collapse; }
  th, td { text-align: left; padding: 0.4rem 0.6rem; border-bottom: 1px solid $color-bg; }
  tbody tr { cursor: pointer; &:hover { background: rgba(255, 255, 255, 0.04); } }
  tr.selected { background: rgba(56, 189, 248, 0.15); }
  .actions { display: flex; gap: 0.3rem; }
  .danger { background: $color-danger; }
}
</style>
