<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { apiClient } from '../api/client'
import { describeFailure } from '../api/reason'
import DetailEditor from './DetailEditor.vue'
import { localizedLabel } from '../i18n/locales'
import type { DetailDefinition, InstrumentSummary, OverridePatch } from '../types'

const props = defineProps<{ item: InstrumentSummary; busy?: boolean; fieldOptions?: Partial<Record<string, string[]>> }>()
const emit = defineEmits<{ (event: 'commit', patch: OverridePatch): void }>()
const { t, locale } = useI18n()
const definitions = ref<DetailDefinition[]>([])
const error = ref<string | null>(null)
const loading = ref(true)
const fields = computed(() => definitions.value.filter((definition) =>
  Object.hasOwn(props.item.details ?? {}, definition.name),
))
onMounted(async () => {
  try {
    const catalog = await apiClient.get<{ details: DetailDefinition[] }>('/fields')
    definitions.value = catalog.details
  } catch (failure) {
    error.value = describeFailure(t('details.loadFailed'), failure)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="open-details">
    <p v-if="error" role="alert">{{ error }}</p>
    <p v-else-if="loading">{{ t('details.loading') }}</p>
    <p v-else-if="fields.length === 0">{{ t('details.empty') }}</p>
    <dl v-else class="open-details__fields">
      <div v-for="definition in fields" :key="definition.name">
        <dt>{{ localizedLabel(definition, locale) }}</dt>
        <dd><DetailEditor :definition="definition" :value="item.details![definition.name]!" :busy="busy" :options="fieldOptions?.[definition.name]"
          :currency-options="fieldOptions?.fund_currency"
          @commit="emit('commit', { details: { [definition.name]: $event } })" /></dd>
      </div>
    </dl>
  </div>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.open-details__fields {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
  gap: var(--space-4); margin: 0;
}
dt {
  margin-bottom: var(--space-2);
  color: $color-muted;
  font-size: var(--font-xs);
  font-weight: 500;
}
dd { margin: 0; }
</style>
