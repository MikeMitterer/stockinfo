<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { FINANCIAL_CONTENT_URL, LICENSE_URLS, LICENSING_URL } from '../config'

const { t, locale } = useI18n()
const licenseUrl = computed(() => locale.value === 'de' ? LICENSE_URLS.de : LICENSE_URLS.en)
</script>

<template>
  <section class="about card" aria-labelledby="about-title">
    <h3 id="about-title">{{ t('about.title') }}</h3>
    <p>{{ t('about.intro') }}</p>
    <p>{{ t('about.data') }}</p>
    <p>{{ t('about.use') }}</p>
    <p>{{ t('about.legal') }}</p>
    <ul>
      <li><a :href="licenseUrl" target="_blank" rel="noopener noreferrer">{{ t('about.licenseLink') }}</a></li>
      <li><a :href="LICENSING_URL" target="_blank" rel="noopener noreferrer">{{ t('about.licensingLink') }}</a></li>
      <li><a :href="FINANCIAL_CONTENT_URL" target="_blank" rel="noopener noreferrer">{{ t('about.financialContentLink') }}</a></li>
    </ul>
  </section>
</template>

<style scoped lang="scss">
.about {
  max-width: 72ch;

  h3 { margin: 0 0 var(--space-3); }
  p { margin: 0 0 var(--space-3); }
  ul { margin: 0; padding-inline-start: var(--space-5); }
  li + li { margin-top: var(--space-2); }
}
</style>
