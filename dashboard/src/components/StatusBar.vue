<script setup lang="ts">
import type { HealthStatus } from '../composables/useHealth'

defineProps<{ status: HealthStatus; version: string | null }>()

const labels: Record<HealthStatus, string> = {
  ok: 'Online',
  degraded: 'Prüfe…',
  down: 'Offline',
}
</script>

<template>
  <footer class="statusbar">
    <span class="left">
      StockInfo powered by
      <a href="https://www.mangolila.at/" target="_blank" rel="noopener">MangoLila</a>
    </span>
    <span class="right">
      <span v-if="version" class="version mono">v{{ version }}</span>
      <span class="health" :class="status">
        <span class="dot" />
        {{ labels[status] }}
      </span>
    </span>
  </footer>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.statusbar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: $status-h;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.25rem;
  background: rgba(20, 16, 25, 0.9);
  backdrop-filter: blur(8px);
  border-top: 1px solid $color-border;
  font-size: 0.78rem;

  .left {
    color: $color-muted;
    a { color: $color-accent; text-decoration: none; &:hover { text-decoration: underline; } }
  }
  .right { display: flex; align-items: center; gap: 1rem; }
  .version { color: $color-muted; }

  .health {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-weight: 600;

    .dot { width: 8px; height: 8px; border-radius: 50%; }
    &.ok { color: $health-ok; .dot { background: $health-ok; box-shadow: 0 0 6px $health-ok; } }
    &.degraded { color: $health-warn; .dot { background: $health-warn; box-shadow: 0 0 6px $health-warn; } }
    &.down { color: $health-down; .dot { background: $health-down; box-shadow: 0 0 6px $health-down; } }
  }
}
</style>
