<script setup lang="ts">
import { useI18n } from 'vue-i18n'

type RegionKey = 'germany' | 'usa' | 'europe' | 'global'

interface Exchange {
  suffix: string // leer = kein Suffix (NYSE/NASDAQ)
  name: string
  region: RegionKey
  currency: string
  note?: 'standard' | 'pence'
}

const { t } = useI18n()

// Gängige Yahoo-Finance-Börsensuffixe. Die Währung stammt immer aus dem
// Live-Kurs — die Angabe hier ist die übliche Notierungswährung.
const exchanges: Exchange[] = [
  { suffix: '.DE', name: 'Xetra', region: 'germany', currency: 'EUR', note: 'standard' },
  { suffix: '.SG', name: 'Stuttgart', region: 'germany', currency: 'EUR' },
  { suffix: '.F', name: 'Frankfurt', region: 'germany', currency: 'EUR' },
  { suffix: '.MU', name: 'München', region: 'germany', currency: 'EUR' },
  { suffix: '.BE', name: 'Berlin', region: 'germany', currency: 'EUR' },
  { suffix: '.DU', name: 'Düsseldorf', region: 'germany', currency: 'EUR' },
  { suffix: '.HM', name: 'Hamburg', region: 'germany', currency: 'EUR' },
  { suffix: '.HA', name: 'Hannover', region: 'germany', currency: 'EUR' },
  { suffix: '', name: 'NYSE / NASDAQ', region: 'usa', currency: 'USD' },
  { suffix: '.L', name: 'London LSE', region: 'europe', currency: 'GBp', note: 'pence' },
  { suffix: '.MI', name: 'Mailand', region: 'europe', currency: 'EUR' },
  { suffix: '.PA', name: 'Paris (Euronext)', region: 'europe', currency: 'EUR' },
  { suffix: '.AS', name: 'Amsterdam', region: 'europe', currency: 'EUR' },
  { suffix: '.BR', name: 'Brüssel', region: 'europe', currency: 'EUR' },
  { suffix: '.LS', name: 'Lissabon', region: 'europe', currency: 'EUR' },
  { suffix: '.MC', name: 'Madrid', region: 'europe', currency: 'EUR' },
  { suffix: '.VI', name: 'Wien', region: 'europe', currency: 'EUR' },
  { suffix: '.SW', name: 'SIX Swiss', region: 'europe', currency: 'CHF' },
  { suffix: '.ST', name: 'Stockholm', region: 'europe', currency: 'SEK' },
  { suffix: '.CO', name: 'Kopenhagen', region: 'europe', currency: 'DKK' },
  { suffix: '.OL', name: 'Oslo', region: 'europe', currency: 'NOK' },
  { suffix: '.HE', name: 'Helsinki', region: 'europe', currency: 'EUR' },
  { suffix: '.WA', name: 'Warschau', region: 'europe', currency: 'PLN' },
  { suffix: '.TO', name: 'Toronto', region: 'global', currency: 'CAD' },
  { suffix: '.HK', name: 'Hongkong', region: 'global', currency: 'HKD' },
  { suffix: '.T', name: 'Tokio', region: 'global', currency: 'JPY' },
  { suffix: '.AX', name: 'Sydney (ASX)', region: 'global', currency: 'AUD' },
]
</script>

<template>
  <section class="exchanges card">
    <h2>{{ t('exchanges.title') }}</h2>
    <p class="hint">{{ t('exchanges.hint', { example: 'GOLD.SG' }) }}</p>
    <div class="scroll">
      <table class="data-table">
        <thead>
          <tr>
            <th>{{ t('exchanges.colSuffix') }}</th><th>{{ t('exchanges.colExchange') }}</th>
            <th>{{ t('exchanges.colRegion') }}</th><th>{{ t('exchanges.colCurrency') }}</th><th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="exchange in exchanges" :key="exchange.suffix + exchange.name">
            <td class="mono suffix">{{ exchange.suffix || t('exchanges.noSuffix') }}</td>
            <td>{{ exchange.name }}</td>
            <td class="dim">{{ t(`exchanges.regions.${exchange.region}`) }}</td>
            <td class="mono">{{ exchange.currency }}</td>
            <td>
              <span v-if="exchange.note === 'standard'" class="badge std">{{ t('exchanges.standard') }}</span>
              <span v-else-if="exchange.note === 'pence'" class="badge warn">{{ t('exchanges.penceNote') }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.hint { color: $color-muted; margin: 0 0 1rem; font-size: 0.85rem; }
.hint code { font-family: $font-mono; color: $color-text; }
.scroll { overflow-x: auto; }

td { padding: 0.45rem 0.7rem; border-bottom: 1px solid color-mix(in srgb, $color-border 55%, transparent); }
.suffix { font-weight: 600; color: $color-accent; }
.dim { color: $color-muted; }

// Varianten der globalen .badge-Pill
.badge {
  &.std { color: $color-accent; background: color-mix(in srgb, $color-accent 15%, transparent); }
  &.warn { color: $health-warn; background: color-mix(in srgb, $health-warn 18%, transparent); }
}
</style>
