<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import DetailEditor from './DetailEditor.vue'
import { useFieldCatalog } from '../composables/useFieldCatalog'
import { localizedLabel } from '../i18n/locales'
import type { InstrumentSummary, OverridePatch } from '../types'

const props = defineProps<{ item: InstrumentSummary; busy?: boolean; fieldOptions?: Partial<Record<string, string[]>> }>()
const emit = defineEmits<{ (event: 'commit', patch: OverridePatch): void }>()
const { t, locale } = useI18n()
const { definitions, loading, error, load } = useFieldCatalog()
const fields = computed(() => definitions.value.filter((definition) =>
  Object.hasOwn(props.item.details ?? {}, definition.name),
))
// Schon beim Aufbau, nicht erst nach dem Einhängen: `loading` steht dann beim
// ersten Rendern, und „keine Felder" blitzt nicht kurz auf.
void load()
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
