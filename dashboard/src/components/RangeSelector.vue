<script setup lang="ts">
import type { RangeKey } from '../types'

defineProps<{ active: RangeKey }>()

const emit = defineEmits<{
  (event: 'change', range: RangeKey): void
}>()

const ranges: { key: RangeKey; label: string }[] = [
  { key: 'intraday', label: '1T' },
  { key: '1w', label: '1W' },
  { key: '1m', label: '1M' },
  { key: '3m', label: '3M' },
  { key: '1y', label: '1J' },
  { key: 'max', label: 'Max' },
]
</script>

<template>
  <div class="range">
    <button
      v-for="range in ranges"
      :key="range.key"
      :class="{ active: range.key === active }"
      @click="emit('change', range.key)"
    >
      {{ range.label }}
    </button>
  </div>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.range {
  display: inline-flex;
  gap: 2px;
  padding: 3px;
  border-radius: $radius;
  background: $color-bg;
  border: 1px solid $color-border;

  button {
    background: transparent;
    border: none;
    color: $color-muted;
    padding: 0.25rem 0.7rem;
    border-radius: 7px;
    font-size: 0.8rem;

    &:hover { color: $color-text; }
    &.active {
      color: #fff;
      background: $brand-gradient;
    }
  }
}
</style>
