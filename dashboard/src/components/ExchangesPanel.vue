<script setup lang="ts">
interface Exchange {
  suffix: string
  name: string
  region: string
  currency: string
  note?: string
}

// Gängige Yahoo-Finance-Börsensuffixe. Die Währung stammt immer aus dem
// Live-Kurs — die Angabe hier ist die übliche Notierungswährung.
const exchanges: Exchange[] = [
  { suffix: '.DE', name: 'Xetra', region: 'Deutschland', currency: 'EUR', note: 'Standard' },
  { suffix: '.SG', name: 'Stuttgart', region: 'Deutschland', currency: 'EUR' },
  { suffix: '.F', name: 'Frankfurt', region: 'Deutschland', currency: 'EUR' },
  { suffix: '.MU', name: 'München', region: 'Deutschland', currency: 'EUR' },
  { suffix: '.BE', name: 'Berlin', region: 'Deutschland', currency: 'EUR' },
  { suffix: '.DU', name: 'Düsseldorf', region: 'Deutschland', currency: 'EUR' },
  { suffix: '.HM', name: 'Hamburg', region: 'Deutschland', currency: 'EUR' },
  { suffix: '.HA', name: 'Hannover', region: 'Deutschland', currency: 'EUR' },
  { suffix: '(ohne)', name: 'NYSE / NASDAQ', region: 'USA', currency: 'USD' },
  { suffix: '.L', name: 'London LSE', region: 'Europa', currency: 'GBp', note: 'oft Pence (1/100 GBP)!' },
  { suffix: '.MI', name: 'Mailand', region: 'Europa', currency: 'EUR' },
  { suffix: '.PA', name: 'Paris (Euronext)', region: 'Europa', currency: 'EUR' },
  { suffix: '.AS', name: 'Amsterdam', region: 'Europa', currency: 'EUR' },
  { suffix: '.BR', name: 'Brüssel', region: 'Europa', currency: 'EUR' },
  { suffix: '.LS', name: 'Lissabon', region: 'Europa', currency: 'EUR' },
  { suffix: '.MC', name: 'Madrid', region: 'Europa', currency: 'EUR' },
  { suffix: '.VI', name: 'Wien', region: 'Europa', currency: 'EUR' },
  { suffix: '.SW', name: 'SIX Swiss', region: 'Europa', currency: 'CHF' },
  { suffix: '.ST', name: 'Stockholm', region: 'Europa', currency: 'SEK' },
  { suffix: '.CO', name: 'Kopenhagen', region: 'Europa', currency: 'DKK' },
  { suffix: '.OL', name: 'Oslo', region: 'Europa', currency: 'NOK' },
  { suffix: '.HE', name: 'Helsinki', region: 'Europa', currency: 'EUR' },
  { suffix: '.WA', name: 'Warschau', region: 'Europa', currency: 'PLN' },
  { suffix: '.TO', name: 'Toronto', region: 'Global', currency: 'CAD' },
  { suffix: '.HK', name: 'Hongkong', region: 'Global', currency: 'HKD' },
  { suffix: '.T', name: 'Tokio', region: 'Global', currency: 'JPY' },
  { suffix: '.AX', name: 'Sydney (ASX)', region: 'Global', currency: 'AUD' },
]
</script>

<template>
  <section class="exchanges card">
    <h2>Börsen-Suffixe</h2>
    <p class="hint">
      Bei der Abfrage per Symbol bestimmt das Suffix die Börse (z.B. <code>GOLD.SG</code> =
      Stuttgart). Die Währung kommt immer aus dem Live-Kurs — London notiert häufig in
      <strong>Pence</strong>.
    </p>
    <div class="scroll">
      <table class="data-table">
        <thead>
          <tr><th>Suffix</th><th>Börse</th><th>Region</th><th>Währung</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="exchange in exchanges" :key="exchange.suffix + exchange.name">
            <td class="mono suffix">{{ exchange.suffix }}</td>
            <td>{{ exchange.name }}</td>
            <td class="dim">{{ exchange.region }}</td>
            <td class="mono">{{ exchange.currency }}</td>
            <td>
              <span v-if="exchange.note === 'Standard'" class="badge std">{{ exchange.note }}</span>
              <span v-else-if="exchange.note" class="badge warn">{{ exchange.note }}</span>
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
