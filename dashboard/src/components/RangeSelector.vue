<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { RangeKey } from '../types'

defineProps<{ active: RangeKey }>()

const emit = defineEmits<{
  (event: 'change', range: RangeKey): void
}>()

const { t } = useI18n()

const ranges = computed<{ key: RangeKey; label: string }[]>(() => [
  { key: 'intraday', label: t('chart.ranges.intraday') },
  { key: '1w', label: t('chart.ranges.oneWeek') },
  { key: '1m', label: t('chart.ranges.oneMonth') },
  { key: '3m', label: t('chart.ranges.threeMonths') },
  { key: '1y', label: t('chart.ranges.oneYear') },
  { key: 'max', label: t('chart.ranges.max') },
])
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
  // Sicherheitsnetz für sehr schmale Viewports (< 261px nutzbare Breite):
  // ohne Umbruch würden einzelne Range-Buttons abgeschnitten statt umzubrechen.
  flex-wrap: wrap;
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

    // Trefferfläche ≥44×44px (ux-standards), aber nur unterhalb md (768px):
    // gemessen bei 371px war jeder Range-Knopf nur 23px hoch und 37-47px breit.
    // Die Größe kommt aus Padding + Mindestmaßen, nicht aus der Schrift — der
    // Text bleibt 0.8rem, das Dock soll ein kompaktes Segmented-Control bleiben.
    @media (max-width: 767px) {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 44px;
      min-height: 44px;
      padding: 0.4rem 0.7rem;
    }
  }
}
</style>
