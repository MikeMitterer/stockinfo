<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { NButton, NModal } from 'naive-ui'

import type { IntakeConfirmation } from '../types'

const props = defineProps<{ decision: IntakeConfirmation | null; busy: boolean }>()
const emit = defineEmits<{ (event: 'confirm'): void; (event: 'cancel'): void }>()
const { t } = useI18n()
const cancelButton = ref<InstanceType<typeof NButton> | null>(null)

// Inhalt bis zum Ende der Ausblendung behalten.
const shown = ref<IntakeConfirmation | null>(null)
watch(() => props.decision, (decision) => {
  if (decision) shown.value = decision
}, { immediate: true })

/** Ein versehentliches Enter soll keine Aufnahme bestätigen. */
function focusCancel(): void {
  const element = cancelButton.value?.$el as HTMLElement | undefined
  element?.focus()
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
      <p>{{ shown.name }}</p>
      <p>{{ t('confirmExchange.text') }}</p>
      <dl>
        <dt>{{ t('confirmExchange.actual') }}</dt>
        <dd>{{ shown.identity.ticker }} · {{ shown.exchange }} ({{ shown.identity.mic }}) · {{ shown.currency }}</dd>
        <dt>{{ t('confirmExchange.preferred') }}</dt>
        <dd>{{ shown.preferred.name }} ({{ shown.preferred.mic }}) · {{ shown.preferred.currency }}</dd>
      </dl>
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
dt { font-weight: 600; }
dd { margin: 0 0 1rem; overflow-wrap: anywhere; }
.confirm-exchange__actions { display: flex; justify-content: flex-end; flex-wrap: wrap; gap: 0.6rem; }
</style>
