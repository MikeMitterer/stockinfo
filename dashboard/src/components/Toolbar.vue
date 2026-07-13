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
  <div class="toolbar">
    <form class="add" @submit.prevent="submit">
      <input v-model="identifier" placeholder="ISIN oder Symbol (z.B. VGWL.DE)" />
      <button type="submit" class="primary" :disabled="busy">Hinzufügen</button>
    </form>
    <button :disabled="refreshing" @click="emit('refresh')">
      {{ refreshing ? 'Aktualisiere…' : '↻ Alle aktualisieren' }}
    </button>
  </div>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.toolbar {
  display: flex;
  gap: 1rem;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  margin-bottom: 1.1rem;

  .add { display: flex; gap: 0.5rem; flex: 1; min-width: 280px; }
  input {
    flex: 1;
    padding: 0.5rem 0.75rem;
    border-radius: $radius;
    border: 1px solid $color-border;
    background: $color-surface;
    color: $color-text;
    font-size: 0.9rem;

    &::placeholder { color: $color-muted; }
    &:focus { outline: none; border-color: $color-accent; }
  }
}
</style>
