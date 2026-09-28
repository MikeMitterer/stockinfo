<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { THEMES } from '@mmit/ux-foundation'

import { FINANCIAL_CONTENT_URL, LICENSE_URLS, LICENSING_URL, MANGOLILA_URL } from '../config'
import { useTheme } from '../composables/useTheme'

const { t, locale } = useI18n()
const { current: currentTheme } = useTheme()
const licenseUrl = computed(() => locale.value === 'de' ? LICENSE_URLS.de : LICENSE_URLS.en)
const logoUrl = computed(() => `${import.meta.env.BASE_URL}mangolila-logo-${THEMES[currentTheme.value].isDark ? 'dark' : 'light'}.png`)
</script>

<template>
  <section class="about card" aria-labelledby="about-title">
    <div class="about__layout">
      <div class="about__content">
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
      </div>
      <div class="about__provider">
        <div class="about__brand">
          <img :src="logoUrl" alt="" width="200" height="57">
        </div>
        <address class="about__address">
          <strong>{{ t('about.providerName') }}</strong><br>
          {{ t('about.providerStreet') }}<br>
          {{ t('about.providerCity') }}<br>
          {{ t('about.providerCountry') }}
        </address>
        <a :href="MANGOLILA_URL" target="_blank" rel="noopener noreferrer">
          {{ t('about.websiteLink') }}
        </a>
      </div>
    </div>
  </section>
</template>

<style scoped lang="scss">
.about {
  max-width: 70rem;

  h3 { margin: 0 0 var(--space-3); }
  p { margin: 0 0 var(--space-3); }
  ul { margin: 0; padding-inline-start: var(--space-6); }
  li + li { margin-top: var(--space-2); }

  &__layout {
    display: grid;
    gap: var(--space-6);

    @include up(md) { grid-template-columns: minmax(0, 1fr) 17rem; }
  }

  &__provider {
    display: grid;
    grid-template-columns: 8rem minmax(0, 1fr);
    align-content: start;
    column-gap: var(--space-4);
    row-gap: var(--space-2);

    .about__brand { grid-row: 1 / span 2; }

    @include up(md) {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: var(--space-3);
      border-inline-start: 1px solid token(--border-default);
      padding-inline-start: var(--space-6);
    }
  }

  &__brand {
    width: 100%;
    max-width: 12rem;

    img { display: block; width: 100%; height: auto; }
  }

  &__address {
    font-style: normal;
    line-height: 1.6;
    font-size: var(--font-sm);
  }
}
</style>
