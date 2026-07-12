<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  (event: 'refresh'): void
  (event: 'add', identifier: string): void
}>()

defineProps<{ refreshing: boolean; busy: boolean }>()

const identifier = ref<string>('')

function submit(): void {
  const value = identifier.value.trim()
  if (value) {
    emit('add', value)
    identifier.value = ''
  }
}
</script>

<template>
  <header class="toolbar">
    <button :disabled="refreshing" @click="emit('refresh')">
      {{ refreshing ? 'Aktualisiere…' : 'Alle aktualisieren' }}
    </button>
    <form class="add" @submit.prevent="submit">
      <input v-model="identifier" placeholder="ISIN oder Symbol (z.B. VGWL.DE)" />
      <button type="submit" :disabled="busy">Hinzufügen</button>
    </form>
  </header>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.toolbar {
  display: flex;
  gap: 1rem;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 1rem;

  .add { display: flex; gap: 0.5rem; }
  input {
    padding: 0.4rem 0.6rem;
    border-radius: $radius;
    border: 1px solid $color-muted;
    background: $color-surface;
    color: $color-text;
    min-width: 260px;
  }
}
</style>
