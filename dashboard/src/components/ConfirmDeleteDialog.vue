<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { NButton, NModal } from 'naive-ui'

import { focusComponent, useLastShown } from '../composables/useDialog'
import type { InstrumentSummary } from '../types'

/**
 * Rückfrage vor dem Löschen — das ist unwiderruflich, die Kurshistorie geht mit.
 *
 * Der Rahmen kommt von `NModal`: abdunkelnde Fläche, Escape, Klick daneben,
 * Fokus-Falle und Fokus-Rückgabe bringt es mit. Vorher stand das alles hier als
 * eigener Nachbau — rund achtzig Zeilen, die dasselbe schlechter konnten.
 *
 * Was hier bleibt, ist die eine Entscheidung, die Naive nicht treffen kann:
 * Der Fokus landet auf **Abbrechen**, nicht auf Löschen. Ein versehentliches
 * Enter soll abbrechen.
 */
const props = defineProps<{ item: InstrumentSummary | null }>()
const emit = defineEmits<{ (event: 'confirm'): void; (event: 'cancel'): void }>()

const { t } = useI18n()

const cancelBtn = ref<InstanceType<typeof NButton> | null>(null)

// Inhalt bis zum Ende der Ausblendung behalten; danach wird die Kopie verworfen.
const shown = useLastShown(() => props.item)

/** Escape, Klick auf die Fläche und das ✕ laufen alle hier zusammen. */
function onUpdateShow(show: boolean): void {
  if (!show && props.item) emit('cancel')
}

/** Fokus auf „Abbrechen" — erst nach der Einblendung. */
function focusCancel(): void {
  focusComponent(cancelBtn)
}
</script>

<template>
  <NModal
    :show="item !== null"
    preset="card"
    :title="t('confirmDelete.title')"
    :style="{ width: 'min(420px, calc(100vw - 3rem))' }"
    :auto-focus="false"
    role="dialog"
    aria-modal="true"
    @update:show="onUpdateShow"
    @after-enter="focusCancel"
    @after-leave="shown = null"
  >
    <div v-if="shown" class="confirm-delete">
      <p class="confirm-delete__item">
        <span class="confirm-delete__name">{{ shown.name }}</span>
        <span class="confirm-delete__symbol mono">{{ shown.symbol }}</span>
      </p>
      <p class="confirm-delete__history">{{ t('confirmDelete.history', shown.history_count) }}</p>
      <p class="confirm-delete__irreversible">{{ t('confirmDelete.irreversible') }}</p>
    </div>

    <template #footer>
      <div class="confirm-delete__actions">
        <NButton ref="cancelBtn" class="confirm-delete__cancel" @click="emit('cancel')">
          {{ t('table.cancel') }}
        </NButton>
        <NButton class="confirm-delete__confirm" type="error" @click="emit('confirm')">
          {{ t('table.remove') }}
        </NButton>
      </div>
    </template>
  </NModal>
</template>

<style scoped lang="scss">
/*
 * Fläche, Rahmen und Innenabstände bringt `NModal` mit — hier steht nur, was
 * diesen Inhalt ausmacht.
 */
.confirm-delete {
  p { margin: 0 0 0.5rem; }
  p:last-child { margin-bottom: 0; }

  &__item {
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  &__name { font-weight: 600; }

  &__symbol,
  &__history,
  &__irreversible { @include muted(0.85rem); }

  &__actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.6rem;
  }
}
</style>
