<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { NButton } from 'naive-ui'

/**
 * Die Aktionen zu einem Papier: JSON, Profil bei extraETF und Yahoo,
 * Aktualisieren, Löschen. Tabelle und Karte zeigen dieselben fünf Knöpfe.
 *
 * **Ohne eigenen Rahmen** (mehrere Wurzelelemente): Abstand und Umbruch legt
 * der Elternteil fest — in der Tabelle `.actions`, in der Karte
 * `.icard__actions`. Ein Rahmen hier hätte deren Regeln für direkte Kinder
 * ausgehebelt.
 */
defineProps<{
  /** Profil bei extraETF; leer, wenn es keins gibt. */
  extraetfUrl: string
  /** Seite bei Yahoo Finance; leer, wenn es keine gibt. */
  yahooUrl: string
  /** Läuft gerade ein Refresh dieses Papiers? */
  refreshing: boolean
}>()
const emit = defineEmits<{
  (event: 'json'): void
  (event: 'refresh'): void
  (event: 'remove'): void
}>()
const { t } = useI18n()
</script>

<template>
  <NButton
    class="instrument-action instrument-action--json"
    size="tiny"
    quaternary
    :title="t('table.showJson')"
    @click="emit('json')"
  >
    {{ t('table.jsonShort') }}
  </NButton>
  <NButton
    v-if="extraetfUrl"
    class="instrument-action instrument-action--extraetf"
    tag="a"
    size="tiny"
    quaternary
    :href="extraetfUrl"
    target="_blank"
    rel="noopener"
    :title="t('table.extraetfProfile')"
  >
    {{ t('table.extraetfShort') }}
  </NButton>
  <NButton
    v-if="yahooUrl"
    class="instrument-action instrument-action--yahoo"
    tag="a"
    size="tiny"
    quaternary
    :href="yahooUrl"
    target="_blank"
    rel="noopener"
    :title="t('table.yahooFinance')"
  >
    {{ t('table.yahooShort') }}
  </NButton>
  <NButton
    class="instrument-action instrument-action--refresh"
    size="tiny"
    quaternary
    :loading="refreshing"
    :disabled="refreshing"
    :title="t('table.refresh')"
    @click="emit('refresh')"
  >
    ↻
  </NButton>
  <NButton
    class="instrument-action instrument-action--remove"
    size="tiny"
    quaternary
    type="error"
    :title="t('table.remove')"
    @click="emit('remove')"
  >
    ✕
  </NButton>
</template>
