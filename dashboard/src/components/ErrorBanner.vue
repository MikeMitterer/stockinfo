<script setup lang="ts">
import type { ErrorEntry } from '../types'

defineProps<{ errors: ErrorEntry[] }>()

const emit = defineEmits<{
  (event: 'dismiss', key: string): void
}>()
</script>

<template>
  <div v-if="errors.length" class="error-banner" role="alert">
    <div v-for="entry in errors" :key="entry.key" class="row">
      <span class="msg">⚠ {{ entry.message }}</span>
      <button class="x" title="Ausblenden" @click="emit('dismiss', entry.key)">✕</button>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.error-banner {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin: 0 0 1.1rem;
}

.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.55rem 0.9rem;
  border: 1px solid color-mix(in srgb, $color-danger 55%, transparent);
  border-radius: $radius;
  background: color-mix(in srgb, $color-danger 12%, transparent);
  color: $color-text;
  font-size: 0.85rem;
}

.msg { min-width: 0; }

.x {
  padding: 0.1rem 0.45rem;
  font-size: 0.75rem;
  background: transparent;
  color: $color-muted;
  &:hover { color: $color-text; }
}
</style>
