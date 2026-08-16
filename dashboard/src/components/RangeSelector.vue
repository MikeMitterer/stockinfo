<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { NButton, NButtonGroup } from 'naive-ui'

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
  <!--
    Eine Gruppe, kein loser Haufen: Die Zeiträume schließen einander aus, und
    genau das zeigt die zusammenhängende Form.
  -->
  <NButtonGroup class="range" size="small">
    <NButton
      v-for="range in ranges"
      :key="range.key"
      :type="range.key === active ? 'primary' : 'default'"
      @click="emit('change', range.key)"
    >
      {{ range.label }}
    </NButton>
  </NButtonGroup>
</template>

<style scoped lang="scss">
/*
 * Rahmen, Flächen und die Knöpfe selbst bringt `NButtonGroup` mit. Hier stand
 * vorher ein nachgebautes Segmented-Control samt eigener Trefferflächen —
 * eine zweite Sorte Knopf neben der des Hauses.
 */

.range {
  // Sicherheitsnetz für sehr schmale Schirme: ohne Umbruch würden einzelne
  // Knöpfe abgeschnitten statt umzubrechen.
  flex-wrap: wrap;
}
</style>
