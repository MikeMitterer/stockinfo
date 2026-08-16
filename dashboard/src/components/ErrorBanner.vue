<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { NButton } from 'naive-ui'

import type { ErrorEntry } from '../types'

defineProps<{ errors: ErrorEntry[] }>()

const { t } = useI18n()

const emit = defineEmits<{
  (event: 'dismiss', key: string): void
}>()
</script>

<template>
  <div v-if="errors.length" class="error-banner" role="alert">
    <div v-for="entry in errors" :key="entry.key" class="row">
      <span class="msg">⚠ {{ entry.message }}</span>
      <NButton class="x" quaternary circle size="tiny" :title="t('errors.dismiss')" @click="emit('dismiss', entry.key)">✕</NButton>
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
  border: 1px solid token(--status-out, 0.55);
  border-radius: $radius;
  background: token(--status-out, 0.12);
  color: $color-text;
  font-size: 0.85rem;
}

.msg { min-width: 0; }

// Der Schließen-Knopf ist ein NButton — Fläche, Farbe und Innenabstand bringt
// er mit. Eigene Werte darauf ergäben eine zweite Sorte Knopf.
</style>
