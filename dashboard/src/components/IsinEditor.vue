<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { NButton, NInput } from 'naive-ui'

import { isIsin } from '../api/paths'

/**
 * Nachträgliches Erfassen einer ISIN, direkt in der Zeile.
 *
 * Bedienelemente von Naive UI. Der Fokus wird über die Instanz gesetzt statt
 * über eine Direktive auf dem DOM-Knoten: Bei einer Komponente zeigt das
 * `ref` auf die Komponente, nicht auf das Feld darin.
 */
const props = defineProps<{
  symbol: string
}>()

const emit = defineEmits<{
  (event: 'save', payload: { symbol: string; isin: string }): void
}>()

const { t } = useI18n()

const editing = ref<boolean>(false)
const isinDraft = ref<string>('')
const isinInvalid = ref<boolean>(false)
const feld = ref<InstanceType<typeof NInput> | null>(null)

// Fehlerhinweis zurücksetzen, sobald der Entwurf geändert wird.
watch(isinDraft, () => {
  isinInvalid.value = false
})

async function startIsin(): Promise<void> {
  editing.value = true
  isinDraft.value = ''
  isinInvalid.value = false
  // Erst nach dem Einblenden fokussieren — vorher gibt es das Feld nicht.
  await nextTick()
  feld.value?.focus()
}

function cancelIsin(): void {
  editing.value = false
  isinDraft.value = ''
  isinInvalid.value = false
}

function confirmIsin(): void {
  const value = isinDraft.value.trim().toUpperCase()
  if (!value) {
    cancelIsin()
    return
  }
  if (!isIsin(value)) {
    isinInvalid.value = true // Hinweis zeigen, Eingabe offen lassen
    return
  }
  emit('save', { symbol: props.symbol, isin: value })
  cancelIsin()
}
</script>

<template>
  <span
    v-if="editing"
    class="isin__edit"
    @click.stop
  >
    <NInput
      ref="feld"
      v-model:value="isinDraft"
      class="isin__input"
      size="tiny"
      :status="isinInvalid ? 'error' : undefined"
      :placeholder="t('table.isinPlaceholder')"
      @keyup.enter="confirmIsin"
      @keyup.esc="cancelIsin"
    />
    <NButton
      class="isin__ok"
      size="tiny"
      :title="t('table.save')"
      @click="confirmIsin"
    >
      ✓
    </NButton>
    <NButton
      class="isin__cancel"
      size="tiny"
      quaternary
      :title="t('table.cancel')"
      @click="cancelIsin"
    >
      ✕
    </NButton>
    <span
      v-if="isinInvalid"
      class="isin__err"
    >{{ t('table.isinInvalid') }}</span>
  </span>

  <NButton
    v-else
    class="isin__add"
    size="tiny"
    quaternary
    :title="t('table.addIsin')"
    @click.stop="startIsin"
  >
    + ISIN
  </NButton>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.isin__edit {
  @include row(0.25rem);
  display: inline-flex;
}

.isin__input {
  width: 140px;
  font-family: $font-mono;
}

.isin__err {
  color: $color-danger;
  font-size: 0.72rem;
  white-space: nowrap;
}
</style>
