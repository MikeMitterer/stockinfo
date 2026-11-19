<script setup lang="ts">
import { ref } from 'vue'
import { I18nT, useI18n } from 'vue-i18n'
import { NButton, NModal } from 'naive-ui'

import { focusComponent, useLastShown } from '../composables/useDialog'
import type { IntakeConfirmation } from '../types'

const props = defineProps<{ decision: IntakeConfirmation | null; identifier: string; busy: boolean }>()
const emit = defineEmits<{ (event: 'confirm'): void; (event: 'cancel'): void }>()
const { t } = useI18n()
const cancelButton = ref<InstanceType<typeof NButton> | null>(null)

// Inhalt bis zum Ende der Ausblendung behalten, samt der Eingabe, zu der er gehört.
const shownIdentifier = ref('')
const shown = useLastShown(() => props.decision, () => {
  shownIdentifier.value = props.identifier
})

/** Ein versehentliches Enter soll keine Aufnahme bestätigen. */
function focusCancel(): void {
  focusComponent(cancelButton)
}

/** Escape und Klick außerhalb entsprechen Abbrechen, außer beim Speichern. */
function updateShow(show: boolean): void {
  if (!show && !props.busy) emit('cancel')
}
</script>

<template>
  <NModal
    :show="decision !== null" preset="card" role="dialog" aria-modal="true"
    :title="t('confirmExchange.title')" :auto-focus="false"
    :style="{ width: 'min(480px, calc(100vw - 2rem))' }"
    :closable="!busy" :mask-closable="!busy" :close-on-esc="!busy"
    @update:show="updateShow" @after-enter="focusCancel" @after-leave="shown = null"
  >
    <template v-if="shown">
      <I18nT keypath="confirmExchange.found" tag="p" class="confirm-exchange__input">
        <template #identifier><strong>{{ shownIdentifier }}</strong></template>
        <template #exchange><strong>{{ shown.preferred.name }}</strong></template>
      </I18nT>
      <I18nT keypath="confirmExchange.alternative" tag="p">
        <template #exchange><strong>{{ shown.exchange }}</strong></template>
        <template #currency><strong>{{ shown.currency }}</strong></template>
      </I18nT>
    </template>
    <template #footer>
      <div class="confirm-exchange__actions">
        <NButton ref="cancelButton" :disabled="busy" @click="emit('cancel')">{{ t('table.cancel') }}</NButton>
        <NButton type="primary" :loading="busy" :disabled="busy" @click="emit('confirm')">{{ t('confirmExchange.confirm') }}</NButton>
      </div>
    </template>
  </NModal>
</template>

<style scoped lang="scss">
.confirm-exchange__input { margin-bottom: 1lh; overflow-wrap: anywhere; }
.confirm-exchange__actions { display: flex; justify-content: flex-end; flex-wrap: wrap; gap: 0.6rem; }
</style>
