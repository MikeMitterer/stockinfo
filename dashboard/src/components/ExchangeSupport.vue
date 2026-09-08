<script setup lang="ts">
import { computed } from 'vue'
import { NText } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { availableQuoteSources } from '../utils/exchangeCoverage'
import { quoteSourceHref } from '../composables/useHashTab'
import type { ExchangeSupport } from '../types'

const props = defineProps<{ entries: ExchangeSupport[] }>()
const { t } = useI18n()
const emit = defineEmits<{ showSource: [source: string] }>()
const sources = computed(() => [...new Set(availableQuoteSources(props.entries).map(entry => entry.source))])

function openSource(event: MouseEvent, source: string) {
  if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return
  event.preventDefault()
  emit('showSource', source)
}
</script>

<template>
  <span v-if="sources.length">
    <template v-for="(source, index) in sources" :key="source">
      <span v-if="index"> · </span>
      <a :href="quoteSourceHref(source)" @click="openSource($event, source)">{{ source === 'yaml-file' ? t('exchanges.yamlFile') : source }}</a>
    </template>
  </span>
  <NText v-else depth="3">{{ t('exchanges.noSupport') }}</NText>
</template>
