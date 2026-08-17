<script setup lang="ts">
import { consola } from 'consola'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { NButton, NModal } from 'naive-ui'

import { useRawQuote } from '../composables/useRawQuote'
import type { InstrumentSummary } from '../types'
import { copyText } from '../utils/clipboard'

/**
 * Zeigt die rohe Abfrage samt Antwort — Adresse oben, JSON darunter.
 *
 * Rahmen, Schleier, Escape und der Klick daneben kommen von `NModal`; der
 * Inhalt scrollt in seinem eigenen Bereich, damit Kopf und Fuß stehen bleiben.
 */
const props = defineProps<{ item: InstrumentSummary | null }>()
const emit = defineEmits<{ (event: 'close'): void }>()

const { url, json, loading, error, load } = useRawQuote()
const copied = ref<string | null>(null)
const { t } = useI18n()

/*
 * Eigene Kopie des Papiers, damit der Kasten sich beim Ausblenden nicht leert:
 * Der Aufrufer setzt seine Auswahl sofort zurück, die Animation läuft aber noch.
 */
const shown = ref<InstrumentSummary | null>(null)

watch(
  () => props.item,
  (item) => {
    if (!item) return
    shown.value = item
    void load(item)
  },
  { immediate: true },
)

/** Kopiert Text in die Zwischenablage und zeigt kurz eine Bestätigung. */
async function copy(text: string, what: string): Promise<void> {
  if (!(await copyText(text))) {
    consola.error('JsonModal.copy: Kopieren fehlgeschlagen')
    return
  }
  copied.value = what
  setTimeout(() => {
    if (copied.value === what) copied.value = null
  }, 1500)
}

/** Escape, Klick auf die Fläche und das ✕ laufen alle hier zusammen. */
function onUpdateShow(show: boolean): void {
  if (!show && props.item) emit('close')
}
</script>

<template>
  <NModal
    :show="item !== null"
    preset="card"
    :title="`JSON — ${shown?.symbol ?? ''}`"
    :style="{ width: 'min(720px, calc(100vw - 3rem))' }"
    :content-style="{ padding: 0 }"
    @update:show="onUpdateShow"
    @after-leave="shown = null"
  >
    <div v-if="shown" class="json">
      <div class="json__url-row">
        <code class="json__url">{{ url }}</code>
        <NButton class="json__copy" size="small" @click="copy(url, 'url')">
          {{ copied === 'url' ? t('json.copied') : t('json.copyUrl') }}
        </NButton>
      </div>

      <!-- Nur dieser Bereich rollt: Adresse und Fuß bleiben stehen. -->
      <div class="json__body">
        <p v-if="loading" class="json__note">{{ t('json.loading') }}</p>
        <p v-else-if="error" class="json__error">{{ error }}</p>
        <pre v-else class="json__code">{{ json }}</pre>
      </div>
    </div>

    <template #footer>
      <div class="json__actions">
        <NButton
          class="json__copy"
          type="primary"
          size="small"
          :disabled="!json"
          @click="copy(json, 'json')"
        >
          {{ copied === 'json' ? t('json.copied') : t('json.copyJson') }}
        </NButton>
      </div>
    </template>
  </NModal>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.json {
  display: flex;
  flex-direction: column;
  max-height: 60vh;

  &__url-row {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid $color-border;
  }

  &__url {
    flex: 1;
    font-family: $font-mono;
    font-size: 0.8rem;
    color: $color-accent;
    overflow-x: auto;
    white-space: nowrap;
  }

  &__body {
    padding: 0 1rem;
    overflow: auto;
  }

  &__code {
    font-family: $font-mono;
    font-size: 0.8rem;
    line-height: 1.5;
    color: $color-text;
    margin: 0.9rem 0;
    white-space: pre;
  }

  &__note { @include muted(null); }
  &__error { color: $color-danger; }

  // Der Kopieren-Knopf darf nicht umbrechen — Layout, nicht Gestaltung.
  &__copy { white-space: nowrap; }

  &__actions {
    display: flex;
    justify-content: flex-end;
  }
}
</style>
