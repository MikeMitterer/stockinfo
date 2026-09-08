<script setup lang="ts">
import { computed, h, nextTick, ref, watch } from 'vue'
import { I18nT, useI18n } from 'vue-i18n'
import { useIsCompact } from '@mmit/ux-foundation'
import { NAlert, NButton, NDataTable, NEmpty, NInput, NList, NListItem, NSwitch, NTag, NText } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import ExchangeSupport from './ExchangeSupport.vue'
import { availableQuoteSources } from '../utils/exchangeCoverage'
import { quoteSourceFromHash } from '../composables/useHashTab'
import InfoHint from './InfoHint.vue'
import type { ExchangeEntry, ExchangesResponse } from '../types'

const props = defineProps<{ data: ExchangesResponse | null; loading?: boolean; error?: string | null }>()
defineEmits<{ reload: [] }>()
const { t } = useI18n()
const compact = useIsCompact()
const query = ref('')
const showUnavailable = ref(false)
const catalog = computed(() => props.data?.catalog ?? [])
const coveredMics = computed(() => new Set(catalog.value.filter((entry): entry is ExchangeEntry => entry.kind === 'exchange' && availableQuoteSources(entry.support).length > 0).map(entry => entry.mic)))
const hasUncovered = computed(() => catalog.value.some(entry => entry.kind === 'exchange' && !coveredMics.value.has(entry.mic)))
const exchanges = computed(() => catalog.value.filter((entry): entry is ExchangeEntry => entry.kind === 'exchange').filter(entry => showUnavailable.value || coveredMics.value.has(entry.mic)).filter(matches))
const unspecified = computed(() => (props.data?.unspecified_support ?? []).filter(entry => entry.role === 'quotes'))

const sourceInfo = computed(() => {
  const sources = new Map<string, { name: string; market: boolean; inventory: boolean }>()
  for (const exchange of catalog.value) {
    if (exchange.kind !== 'exchange') continue
    for (const entry of availableQuoteSources(exchange.support)) {
      const source = sources.get(entry.source) ?? { name: entry.source, market: false, inventory: false }
      source.market ||= entry.scope === 'market'
      source.inventory ||= entry.scope === 'inventory'
      sources.set(source.name, source)
    }
  }
  return [...sources.values()]
})
function showSource(source: string) {
  const target = document.getElementById(`exchange-source-${source}`)
  target?.scrollIntoView({ block: 'start' })
  target?.focus({ preventScroll: true })
}
// Vor der Routennormalisierung lesen; die Daten können erst später eintreffen.
let linkedSource = quoteSourceFromHash()
watch(sourceInfo, async sources => {
  if (!linkedSource || !sources.some(source => source.name === linkedSource)) return
  const source = linkedSource
  linkedSource = null
  await nextTick()
  showSource(source)
}, { immediate: true })

function matches(entry: ExchangeEntry): boolean {
  const values = [entry.name, entry.region, t(`exchanges.regions.${entry.region}`), entry.currency]
  values.push(entry.mic, entry.alias ?? '', ...(entry.declared_by ?? []), ...(entry.support ?? []).map(item => item.source))
  return values.join(' ').toLocaleLowerCase().includes(query.value.trim().toLocaleLowerCase())
}

function rowProps(entry: ExchangeEntry) {
  return { class: availableQuoteSources(entry.support).length ? '' : 'exchanges__uncovered' }
}

function venue(entry: ExchangeEntry) {
  return h('div', [
    h('strong', entry.name),
    entry.mic === props.data?.default_exchange ? h(NTag, { size: 'small', type: availableQuoteSources(entry.support).length ? 'info' : 'default', class: 'exchanges__default' }, () => t('exchanges.default')) : null,
    h('div', entry.currency),
    entry.currency === 'GBp' ? h('div', t('exchanges.penceNote')) : null,
  ])
}

const columns = computed<DataTableColumns<ExchangeEntry>>(() => [
  { title: t('exchanges.mic'), key: 'mic', render: entry => h('strong', { class: 'exchanges__code' }, entry.mic) },
  { title: t('exchanges.colSuffix'), key: 'alias', render: entry => h('strong', { class: 'exchanges__code' }, `.${entry.alias ?? entry.mic}`) },
  { title: t('exchanges.colExchange'), key: 'name', render: venue },
  { title: t('exchanges.support'), key: 'support', render: entry => h(ExchangeSupport, { entries: entry.support ?? [], onShowSource: showSource }) },
])
</script>

<template>
  <section class="exchanges card">
    <div class="exchanges__heading">
      <h2>{{ t('exchanges.title') }}</h2>
      <NButton :loading="loading" :disabled="loading" @click="$emit('reload')">{{ t('exchanges.reload') }}</NButton>
    </div>
    <p class="exchanges__hint">
      <I18nT keypath="exchanges.hint" tag="span">
        <template #alias><strong>SAP.DE</strong></template>
        <template #mic><strong>SAP.XETR</strong></template>
      </I18nT>
      <InfoHint :text="t('env.strictExchangeHint')" settings-tab="environment" />
    </p>
    <NAlert v-if="error" type="error">{{ error }}</NAlert>
    <NInput v-model:value="query" clearable :placeholder="t('exchanges.search')" :aria-label="t('exchanges.search')" />
    <div v-if="hasUncovered" class="exchanges__coverage-toggle">
      <NSwitch v-model:value="showUnavailable" :aria-label="t('exchanges.showUnavailable')" />
      <span>{{ t('exchanges.showUnavailable') }}</span>
    </div>
    <template v-if="data">
      <NList v-if="compact" class="exchanges__venues">
        <NListItem v-for="entry in exchanges" :key="entry.mic" v-bind="rowProps(entry)">
          <strong><span class="exchanges__code">{{ entry.mic }}</span> · {{ entry.name }}</strong>
          <NTag v-if="entry.mic === data.default_exchange" size="small" :type="availableQuoteSources(entry.support).length ? 'info' : 'default'" class="exchanges__default">{{ t('exchanges.default') }}</NTag>
          <p>{{ t(`exchanges.regions.${entry.region}`) }} · {{ entry.currency }}</p>
          <p class="exchanges__suffix">
            {{ t('exchanges.colSuffix') }}:
            <strong class="exchanges__code">.{{ entry.alias ?? entry.mic }}</strong>
          </p>
          <p v-if="entry.currency === 'GBp'">{{ t('exchanges.penceNote') }}</p>
          <p>{{ t('exchanges.support') }}: <ExchangeSupport :entries="entry.support ?? []" @show-source="showSource" /></p>
        </NListItem>
      </NList>
      <NDataTable v-else :columns="columns" :data="exchanges" :row-props="rowProps" :row-key="entry => entry.mic">
        <template #empty><NEmpty :description="t('exchanges.empty')" /></template>
      </NDataTable>
      <NEmpty v-if="compact && !exchanges.length" :description="t('exchanges.empty')" />
      <section v-if="unspecified.length">
        <h3>{{ t('exchanges.unspecified') }}</h3>
        <p class="exchanges__hint">{{ t('exchanges.unspecifiedHint') }}</p>
        <NText>{{ [...new Set(unspecified.map(entry => entry.source))].join(', ') }}</NText>
      </section>
      <section v-if="sourceInfo.length" class="exchanges__source-info">
        <h3>{{ t('exchanges.sourceInfo') }}</h3>
        <section v-for="source in sourceInfo" :key="source.name">
          <h4 :id="`exchange-source-${source.name}`" tabindex="-1">{{ source.name }}</h4>
          <p v-if="source.market">{{ t('exchanges.marketInfo') }}</p>
          <p v-if="source.inventory">{{ t('exchanges.inventoryInfo') }}</p>
          <p v-if="source.name === 'yaml-file'">{{ t('exchanges.yamlRefreshInfo') }}</p>
        </section>
      </section>
    </template>
  </section>
</template>

<style scoped lang="scss">
.exchanges {
  @include stack(var(--space-4));
  min-width: 0;
  overflow-wrap: anywhere;
  &__coverage-toggle { @include row; }
  &__heading { @include row; justify-content: space-between; flex-wrap: wrap; }
  :deep(.exchanges__default) { margin-inline-start: var(--space-2); }
  :deep(.exchanges__code) { color: token(--accent); }
  :deep(.exchanges__uncovered),
  :deep(.exchanges__uncovered td),
  :deep(.exchanges__uncovered .exchanges__code) { color: token(--text-muted); }
  &__hint { color: token(--text-muted); }
  h2, h3, h4, p { margin: 0; }
  &__source-info { @include stack(var(--space-4)); }
  &__source-info section { @include stack(var(--space-2)); }
  &__source-info h4 { scroll-margin-top: calc(var(--topbar-height) + var(--space-4)); }
  &__venues p { margin-block: var(--space-2); }
  &__suffix strong { font-size: var(--font-lg); }
}
</style>
