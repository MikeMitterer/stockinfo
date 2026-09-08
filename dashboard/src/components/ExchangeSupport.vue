<script setup lang="ts">
import { NTag, NText } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import type { ExchangeSupport } from '../types'

defineProps<{ entries: ExchangeSupport[] }>()
const { t } = useI18n()
</script>

<template>
  <div class="exchange-support">
    <NText v-if="!entries.length" depth="3">{{ t('exchanges.noSupport') }}</NText>
    <div v-for="entry in entries" :key="`${entry.source}:${entry.role}`" class="exchange-support__item">
      <span>{{ entry.source }} · {{ t(`roles.${entry.role}`) }}</span>
      <NTag v-if="!entry.usable" size="small">{{ t('exchanges.inactive') }}</NTag>
      <NTag v-if="!entry.scope" size="small">{{ t('exchanges.unspecified') }}</NTag>
      <NTag v-else-if="entry.scope === 'inventory'" size="small">{{ t('exchanges.inventory') }}</NTag>
      <NTag v-else-if="entry.usable" size="small" type="info">{{ t('exchanges.declared') }}</NTag>
    </div>
  </div>
</template>

<style scoped lang="scss">
.exchange-support {
  @include stack(var(--space-2));
  &__item { @include row; flex-wrap: wrap; overflow-wrap: anywhere; }
}
</style>
