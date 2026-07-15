<script setup lang="ts">
import { consola } from 'consola'
import { onMounted, onUnmounted, ref, watch } from 'vue'

import { useRawQuote } from '../composables/useRawQuote'
import type { InstrumentSummary } from '../types'

const props = defineProps<{ item: InstrumentSummary | null }>()
const emit = defineEmits<{ (event: 'close'): void }>()

const { url, json, loading, error, load } = useRawQuote()
const copied = ref<string | null>(null)

watch(
  () => props.item,
  (item) => {
    if (item) void load(item)
  },
  { immediate: true },
)

/** Kopiert Text in die Zwischenablage und zeigt kurz eine Bestätigung. */
async function copy(text: string, what: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(text)
    copied.value = what
    setTimeout(() => {
      if (copied.value === what) copied.value = null
    }, 1500)
  } catch (err) {
    consola.error('JsonModal.copy', err)
  }
}

function onKey(event: KeyboardEvent): void {
  if (event.key === 'Escape' && props.item) emit('close')
}

onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <div v-if="item" class="overlay" @click.self="emit('close')">
    <div class="modal" role="dialog" aria-modal="true">
      <header class="head">
        <h3>JSON — {{ item.symbol }}</h3>
        <button class="x" title="Schließen" @click="emit('close')">✕</button>
      </header>

      <div class="url-row">
        <code class="url">{{ url }}</code>
        <button class="copy" @click="copy(url, 'url')">
          {{ copied === 'url' ? 'kopiert ✓' : 'URL kopieren' }}
        </button>
      </div>

      <div class="body">
        <p v-if="loading" class="muted">Lade…</p>
        <p v-else-if="error" class="err">{{ error }}</p>
        <pre v-else>{{ json }}</pre>
      </div>

      <footer class="foot">
        <button class="copy primary" :disabled="!json" @click="copy(json, 'json')">
          {{ copied === 'json' ? 'kopiert ✓' : 'JSON kopieren' }}
        </button>
      </footer>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(3px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
}

.modal {
  width: min(720px, 100%);
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  background: $color-surface;
  border: 1px solid $color-border;
  border-radius: $radius;
  overflow: hidden;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.8rem 1rem;
  border-bottom: 1px solid $color-border;
  h3 { margin: 0; font-size: 0.95rem; }
  .x { background: $color-surface-2; padding: 0.2rem 0.55rem; }
}

.url-row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid $color-border;
  .url {
    flex: 1;
    font-family: $font-mono;
    font-size: 0.8rem;
    color: $color-accent;
    overflow-x: auto;
    white-space: nowrap;
  }
}

.body {
  padding: 0 1rem;
  overflow: auto;
  pre {
    font-family: $font-mono;
    font-size: 0.8rem;
    line-height: 1.5;
    color: $color-text;
    margin: 0.9rem 0;
    white-space: pre;
  }
  .muted { color: $color-muted; }
  .err { color: $color-danger; }
}

.foot {
  padding: 0.75rem 1rem;
  border-top: 1px solid $color-border;
  display: flex;
  justify-content: flex-end;
}

.copy { white-space: nowrap; }
</style>
