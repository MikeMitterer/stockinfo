<script setup lang="ts">
import { computed, h, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useIsCompact } from '@mmit/ux-foundation'
import { NAlert, NButton, NDataTable, NEmpty, NInput, NList, NListItem, NTag, NText } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import ExchangeSupport from './ExchangeSupport.vue'
import InfoHint from './InfoHint.vue'
import type { CatalogEntry, CollectorEntry, ExchangeEntry, ExchangesResponse } from '../types'

const props = defineProps<{ data: ExchangesResponse | null; loading?: boolean; error?: string | null }>()
defineEmits<{ reload: [] }>()
const { t } = useI18n()
const compact = useIsCompact()
const query = ref('')
const catalog = computed(() => props.data?.catalog ?? [])
const exchanges = computed(() => catalog.value.filter((entry): entry is ExchangeEntry => entry.kind === 'exchange').filter(matches))
const collectors = computed(() => catalog.value.filter((entry): entry is CollectorEntry => entry.kind === 'collector').filter(matches))
const unspecified = computed(() => props.data?.unspecified_support ?? [])

function matches(entry: CatalogEntry): boolean {
  const values = [entry.name, entry.region, t(`exchanges.regions.${entry.region}`), entry.currency]
  if (entry.kind === 'exchange') values.push(entry.mic, entry.alias ?? '', ...(entry.declared_by ?? []), ...(entry.support ?? []).map(item => item.source))
  else values.push(entry.code, ...entry.members)
  return values.join(' ').toLocaleLowerCase().includes(query.value.trim().toLocaleLowerCase())
}

function origin(entry: ExchangeEntry): string {
  if (entry.provenance.kind === 'core') return t('exchanges.core')
  const sources = entry.declared_by?.length ? entry.declared_by : [entry.provenance.id].filter(Boolean)
  return t('exchanges.plugin', { sources: sources.join(', ') })
}

function venue(entry: ExchangeEntry) {
  return h('div', [
    h('strong', entry.name),
    entry.mic === props.data?.default_exchange ? h(NTag, { size: 'small', type: 'info', class: 'exchanges__default' }, () => t('exchanges.default')) : null,
    h('div', entry.currency),
    h(NText, { depth: 3 }, () => origin(entry)),
    entry.currency === 'GBp' ? h('div', t('exchanges.penceNote')) : null,
  ])
}

const columns = computed<DataTableColumns<ExchangeEntry>>(() => [
  { title: t('exchanges.mic'), key: 'mic' },
  { title: t('exchanges.colExchange'), key: 'name', render: venue },
  { title: t('exchanges.colSuffix'), key: 'alias', render: entry => entry.alias ? `.${entry.alias}` : t('exchanges.noSuffix') },
  { title: t('exchanges.colRegion'), key: 'region', render: entry => t(`exchanges.regions.${entry.region}`) },
  { title: t('exchanges.support'), key: 'support', render: entry => h(ExchangeSupport, { entries: entry.support ?? [] }) },
])
</script>

<template>
  <section class="exchanges card">
    <div class="exchanges__heading">
      <h2>{{ t('exchanges.title') }}</h2>
      <NButton :loading="loading" :disabled="loading" @click="$emit('reload')">{{ t('exchanges.reload') }}</NButton>
    </div>
    <p class="exchanges__hint">
      {{ t('exchanges.hint') }}
      <InfoHint :text="t('env.strictExchangeHint')" settings-tab="environment" />
    </p>
    <NAlert v-if="error" type="error">{{ error }}</NAlert>
    <NInput v-model:value="query" clearable :placeholder="t('exchanges.search')" :aria-label="t('exchanges.search')" />
    <template v-if="data">
      <NList v-if="compact" class="exchanges__venues">
        <NListItem v-for="entry in exchanges" :key="entry.mic">
          <strong>{{ entry.mic }} · {{ entry.name }}</strong>
          <NTag v-if="entry.mic === data.default_exchange" size="small" type="info" class="exchanges__default">{{ t('exchanges.default') }}</NTag>
          <p>{{ t(`exchanges.regions.${entry.region}`) }} · {{ entry.currency }}</p>
          <p class="exchanges__suffix">
            {{ t('exchanges.colSuffix') }}:
            <strong v-if="entry.alias">.{{ entry.alias }}</strong>
            <span v-else>{{ t('exchanges.noSuffix') }}</span>
          </p>
          <NText depth="3">{{ origin(entry) }}</NText>
          <p v-if="entry.currency === 'GBp'">{{ t('exchanges.penceNote') }}</p>
          <ExchangeSupport :entries="entry.support ?? []" />
        </NListItem>
      </NList>
      <NDataTable v-else :columns="columns" :data="exchanges" :row-key="entry => entry.mic">
        <template #empty><NEmpty :description="t('exchanges.empty')" /></template>
      </NDataTable>
      <NEmpty v-if="compact && !exchanges.length" :description="t('exchanges.empty')" />
      <section v-if="collectors.length" class="exchanges__collectors">
        <h3>{{ t('exchanges.collector') }}</h3>
        <p class="exchanges__hint">{{ t('exchanges.collectorHint') }}</p>
        <NList>
          <NListItem v-for="entry in collectors" :key="entry.code">
            <strong>{{ entry.code }} · {{ entry.name }}</strong>
            <NTag v-if="entry.code === data.default_exchange" size="small" type="info" class="exchanges__default">{{ t('exchanges.default') }}</NTag>
            <p>{{ t('exchanges.members') }}: {{ entry.members.join(', ') }}</p>
          </NListItem>
        </NList>
      </section>
      <section v-if="unspecified.length">
        <h3>{{ t('exchanges.unspecified') }}</h3>
        <p class="exchanges__hint">{{ t('exchanges.unspecifiedHint') }}</p>
        <ExchangeSupport :entries="unspecified" />
      </section>
    </template>
  </section>
</template>

<style scoped lang="scss">
.exchanges {
  @include stack(var(--space-4));
  min-width: 0;
  overflow-wrap: anywhere;
  &__heading { @include row; justify-content: space-between; flex-wrap: wrap; }
  :deep(.exchanges__default) { margin-inline-start: var(--space-2); }
  &__hint { color: token(--text-muted); }
  h2, h3, p { margin: 0; }
  &__venues p { margin-block: var(--space-2); }
  &__suffix strong { color: token(--accent); font-size: var(--font-lg); }
}
</style>
