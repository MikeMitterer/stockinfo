<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { NButton, NInput, NSelect } from 'naive-ui'
import { UxInlineNumber } from '@mmit/ux-foundation'
import { useI18n } from 'vue-i18n'
import type { DetailDefinition, DetailInput, DetailValue } from '../types'

const props = defineProps<{ definition: DetailDefinition; value: DetailValue; busy?: boolean; options?: string[] }>()
const emit = defineEmits<{ (event: 'commit', value: DetailInput): void }>()
const { t, locale, n } = useI18n()
const label = computed(() => locale.value === 'de' ? props.definition.label_de || props.definition.label_en : props.definition.label_en)
const editable = computed(() => props.definition.overridable && props.value.origin !== 'provider')
const numeric = computed(() => typeof props.value.manual_value === 'number' ? props.value.manual_value : null)
const display = computed(() => {
  const value = props.value.value
  if (value === null) return t('common.noValue')
  if (typeof value === 'boolean') return t(value ? 'table.yes' : 'table.no')
  const text = typeof value === 'number' ? n(value) : value
  const unit = props.definition.unit === 'percent' ? '%' : props.value.currency || props.definition.unit || ''
  return `${text}${unit ? ` ${unit}` : ''}`
})
const draftCurrency = ref(props.value.manual_currency || props.value.currency || '')
watch(() => props.value.manual_currency, (value) => { draftCurrency.value = value || '' })
function changeCurrency(value: string): void {
  draftCurrency.value = value.trim().toUpperCase()
  if (props.value.manual_value !== null) commit(props.value.manual_value)
}
function commit(value: DetailInput['value'], currency = draftCurrency.value || null): void {
  emit('commit', { value, currency: props.definition.currency_required ? currency : null })
}
function toggle(): void {
  commit(props.value.manual_value === true ? false : props.value.manual_value === false ? null : true)
}
</script>

<template>
  <div class="detail-editor">
    <template v-if="editable">
      <UxInlineNumber v-if="definition.kind === 'number'" :value="numeric" :display="display"
        :min="definition.minimum ?? undefined" :max="definition.maximum ?? undefined"
        :precision="4" :empty-value="null" :disabled="busy"
        :edit-label="t('details.editField', { field: label })" :clear-label="t('overrides.clear')" @commit="commit($event)" />
      <NButton v-else-if="definition.kind === 'boolean'" size="small" :disabled="busy" :aria-label="t('details.editField', { field: label })" @click="toggle">{{ display }}</NButton>
      <NSelect v-else class="detail-editor__text" :value="typeof value.manual_value === 'string' ? value.manual_value : null"
        :options="(options ?? []).map((value) => ({ label: value, value }))" filterable tag size="small" :placeholder="label" :disabled="busy"
        @update:value="commit($event)" />
      <NInput v-if="definition.currency_required" :value="draftCurrency" size="small"
        :placeholder="t('details.currency')" :disabled="busy" :maxlength="3"
        @change="changeCurrency" />
    </template>
    <span v-else>{{ display }}</span>
    <NButton v-if="definition.overridable && value.manual_value !== null && (definition.kind !== 'number' || !editable)" size="tiny" quaternary type="error"
      :disabled="busy" :title="t('overrides.removeOwn')" @click="commit(null)">✕</NButton>
    <small v-if="value.shadowed">{{ t('details.shadowed', { value: value.manual_value }) }}</small>
  </div>
</template>

<style scoped lang="scss">
.detail-editor { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-1); }
.detail-editor__text { flex: 1 1 0; min-width: 0; }
small { color: var(--color-text-muted); }
</style>
