<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import type { InstrumentSummary } from '../types'

const props = defineProps<{ item: InstrumentSummary | null }>()
const emit = defineEmits<{ (event: 'confirm'): void; (event: 'cancel'): void }>()

const { t } = useI18n()

const modalRef = ref<HTMLElement | null>(null)
const cancelBtnRef = ref<HTMLButtonElement | null>(null)
let lastFocused: HTMLElement | null = null

/** Alle innerhalb des Dialogs fokussierbaren Elemente, in DOM-Reihenfolge. */
function focusableElements(): HTMLElement[] {
  if (!modalRef.value) return []
  return Array.from(
    modalRef.value.querySelectorAll<HTMLElement>(
      'button:not(:disabled), [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
    ),
  )
}

/** Hält Tab/Shift+Tab innerhalb des Dialogs gefangen, solange er offen ist. */
function trapTab(event: KeyboardEvent): void {
  const elements = focusableElements()
  if (elements.length === 0) return
  const first = elements[0]
  const last = elements[elements.length - 1]
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

function onKey(event: KeyboardEvent): void {
  if (!props.item) return
  if (event.key === 'Escape') {
    emit('cancel')
  } else if (event.key === 'Tab') {
    trapTab(event)
  }
}

// Öffnen: Fokus merken und in den Dialog verschieben (auf Abbrechen, nicht Löschen —
// ein versehentliches Enter soll abbrechen statt löschen). Schließen: Fokus zurückgeben.
watch(
  () => props.item,
  async (item, previous) => {
    if (item && !previous) {
      lastFocused = document.activeElement as HTMLElement | null
      await nextTick()
      cancelBtnRef.value?.focus()
    } else if (!item && previous) {
      lastFocused?.focus()
      lastFocused = null
    }
  },
)

onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <div v-if="item" class="overlay" @click.self="emit('cancel')">
    <div
      ref="modalRef"
      class="modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-delete-title"
      aria-describedby="confirm-delete-body"
    >
      <header class="head">
        <h3 id="confirm-delete-title">{{ t('confirmDelete.title') }}</h3>
      </header>

      <div id="confirm-delete-body" class="body">
        <p class="confirm-delete__item">
          <span class="confirm-delete__name">{{ item.name ?? item.symbol }}</span>
          <span class="confirm-delete__symbol mono">{{ item.symbol }}</span>
        </p>
        <p class="confirm-delete__history">{{ t('confirmDelete.history', item.history_count) }}</p>
        <p class="confirm-delete__irreversible">{{ t('confirmDelete.irreversible') }}</p>
      </div>

      <footer class="foot">
        <button ref="cancelBtnRef" class="confirm-delete__cancel" @click="emit('cancel')">
          {{ t('table.cancel') }}
        </button>
        <button class="confirm-delete__confirm" @click="emit('confirm')">
          {{ t('table.remove') }}
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
  // Bewusst neutrales Schwarz, kein Theme-Ton — der Schleier soll in jedem Theme
  // gleich abdunkeln (siehe JsonModal.vue).
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(3px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
}

.modal {
  width: min(420px, 100%);
  display: flex;
  flex-direction: column;
  background: $color-surface;
  border: 1px solid $color-border;
  border-radius: $radius;
  overflow: hidden;
}

.head {
  padding: 0.9rem 1rem 0.6rem;
  h3 { margin: 0; font-size: 1rem; }
}

.body {
  padding: 0 1rem 0.9rem;

  p { margin: 0 0 0.5rem; }
  p:last-child { margin-bottom: 0; }
}

.confirm-delete__item {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.confirm-delete__name { font-weight: 600; }
.confirm-delete__symbol { color: $color-muted; font-size: 0.85rem; }
.confirm-delete__history,
.confirm-delete__irreversible { color: $color-muted; font-size: 0.85rem; }

.foot {
  padding: 0.75rem 1rem;
  border-top: 1px solid $color-border;
  display: flex;
  justify-content: flex-end;
  gap: 0.6rem;
}

.confirm-delete__cancel,
.confirm-delete__confirm {
  min-width: 44px;
  min-height: 44px;
  padding: 0.5rem 1rem;
}

.confirm-delete__confirm {
  background: $color-danger;
  color: #fff;
  &:hover:not(:disabled) { filter: brightness(1.1); }
}
</style>
