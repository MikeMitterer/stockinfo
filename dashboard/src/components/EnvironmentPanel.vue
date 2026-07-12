<script setup lang="ts">
import type { EnvInfo } from '../types'

defineProps<{ env: EnvInfo | null }>()
</script>

<template>
  <section v-if="env" class="env">
    <h2>Environment</h2>
    <dl>
      <div><dt>Version</dt><dd>{{ env.version }}</dd></div>
      <div><dt>DB-Pfad</dt><dd>{{ env.database_path }}</dd></div>
      <div><dt>Cache-TTL (h)</dt><dd>{{ env.cache_ttl_hours }}</dd></div>
      <div><dt>Refresh-Intervall (h)</dt><dd>{{ env.refresh_interval_hours }}</dd></div>
      <div><dt>Metadaten-TTL (d)</dt><dd>{{ env.metadata_ttl_days }}</dd></div>
      <div><dt>Default-Börse</dt><dd>{{ env.default_exchange }}</dd></div>
      <div><dt>Host:Port</dt><dd>{{ env.host }}:{{ env.port }}</dd></div>
      <div><dt>API-Key gesetzt</dt><dd>{{ env.api_key_set ? 'ja' : 'nein' }}</dd></div>
      <div><dt>OpenFIGI-Key gesetzt</dt><dd>{{ env.openfigi_key_set ? 'ja' : 'nein' }}</dd></div>
    </dl>
  </section>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.env {
  background: $color-surface;
  border-radius: $radius;
  padding: 1rem;

  dl { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 0.5rem; }
  dt { color: $color-muted; font-size: 0.8rem; }
  dd { margin: 0; font-weight: 600; }
}
</style>
