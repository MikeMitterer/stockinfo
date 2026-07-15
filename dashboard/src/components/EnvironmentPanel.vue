<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { EnvInfo } from '../types'

defineProps<{ env: EnvInfo | null }>()

const { t } = useI18n()
</script>

<template>
  <section v-if="env" class="env card">
    <h2>{{ t('env.title') }}</h2>
    <p class="hint">{{ t('env.refreshNote', { hours: env.refresh_interval_hours }) }}</p>
    <dl>
      <div><dt>{{ t('env.version') }}</dt><dd>{{ env.version }}</dd></div>
      <div><dt>{{ t('env.dbPath') }}</dt><dd>{{ env.database_path }}</dd></div>
      <div><dt>{{ t('env.cacheTtl') }}</dt><dd>{{ env.cache_ttl_hours }}</dd></div>
      <div><dt>{{ t('env.refreshInterval') }}</dt><dd>{{ env.refresh_interval_hours }}</dd></div>
      <div><dt>{{ t('env.metadataTtl') }}</dt><dd>{{ env.metadata_ttl_days }}</dd></div>
      <div><dt>{{ t('env.defaultExchange') }}</dt><dd>{{ env.default_exchange }}</dd></div>
      <div><dt>{{ t('env.hostPort') }}</dt><dd>{{ env.host }}:{{ env.port }}</dd></div>
      <div><dt>{{ t('env.openfigiKeySet') }}</dt><dd>{{ env.openfigi_key_set ? t('env.yes') : t('env.no') }}</dd></div>
    </dl>
  </section>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.env {
  .hint { color: $color-muted; margin: 0 0 1rem; font-size: 0.85rem; max-width: 72ch; }
  dl { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 0.9rem 1.5rem; }
  div { display: flex; flex-direction: column; gap: 0.15rem; }
  dt { color: $color-muted; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.04em; }
  dd { margin: 0; font-weight: 600; font-family: $font-mono; font-variant-numeric: tabular-nums; }
}
</style>
