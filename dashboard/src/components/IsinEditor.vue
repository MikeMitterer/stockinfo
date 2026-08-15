<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { isIsin } from '../api/paths'

const props = defineProps<{
  symbol: string
}>()

const emit = defineEmits<{
  (event: 'save', payload: { symbol: string; isin: string }): void
}>()

const { t } = useI18n()

// Inline-Eingabe zum nachträglichen Erfassen einer ISIN
const editing = ref<boolean>(false)
const isinDraft = ref<string>('')
const isinInvalid = ref<boolean>(false)

// Fokussiert das Eingabefeld direkt beim Einblenden.
const vFocus = { mounted: (el: HTMLInputElement) => el.focus() }

// Fehlerhinweis zurücksetzen, sobald der Entwurf geändert wird.
watch(isinDraft, () => {
  isinInvalid.value = false
})

function startIsin(): void {
  editing.value = true
  isinDraft.value = ''
  isinInvalid.value = false
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
  <span v-if="editing" class="isin__edit" @click.stop>
    <input
      v-model="isinDraft"
      v-focus
      class="isin__input"
      :class="{ invalid: isinInvalid }"
      :placeholder="t('table.isinPlaceholder')"
      @keyup.enter="confirmIsin"
      @keyup.esc="cancelIsin"
    />
    <button class="isin__ok" :title="t('table.save')" @click="confirmIsin">✓</button>
    <button class="isin__cancel" :title="t('table.cancel')" @click="cancelIsin">✕</button>
    <span v-if="isinInvalid" class="isin__err">{{ t('table.isinInvalid') }}</span>
  </span>
  <button v-else class="isin__add" :title="t('table.addIsin')" @click.stop="startIsin">
    + ISIN
  </button>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.isin__edit { display: inline-flex; align-items: center; gap: 0.25rem; }
.isin__input {
  width: 140px;
  padding: 0.15rem 0.4rem;
  border-radius: 6px;
  border: 1px solid $color-accent;
  background: $color-bg;
  color: $color-text;
  font-family: $font-mono;
  font-size: 0.8rem;
  &:focus { outline: none; }
  &.invalid { border-color: $color-danger; }
}
.isin__add,
.isin__ok,
.isin__cancel {
  padding: 0.12rem 0.45rem;
  font-size: 0.72rem;
  background: $color-surface-2;
}
.isin__add { color: $color-muted; }
.isin__add:hover { color: $color-accent; }
.isin__ok { color: $health-ok; }
.isin__err { color: $color-danger; font-size: 0.72rem; white-space: nowrap; }
</style>
