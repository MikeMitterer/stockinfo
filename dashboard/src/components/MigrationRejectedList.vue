<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { RejectedInstrument } from '../types'

/**
 * Die Papiere, die den gültigen Bestand verlassen — mit Grund und Preis.
 *
 * Eine eigene Komponente, weil sie **dreimal** erscheint: in der Vorschau, im
 * Bericht danach und im Fehlerzustand nach einem gescheiterten Betriebsstart.
 * Dreimal ins Template geschrieben wäre sie beim ersten zusätzlichen Feld an
 * zwei Stellen gepflegt und an einer vergessen — genau dieser Fehler ist im
 * Backend passiert, wo zwei Feldlisten dieselbe Serialisierung bauten
 * (Codex-Runde 31).
 *
 * **Kartenliste statt Tabelle, ohne Umschaltpunkt.** Eine Zeile trägt Symbol,
 * Name, Grund und Verlust; als vierspaltige Tabelle bräuchte sie unterhalb
 * `md` eine zweite Darstellung. Diese Form trägt auf jeder Breite, also gibt
 * es nur eine.
 *
 * Sie bleibt in dieser App und zieht nicht ins Fundament: Der Identitäts-Umzug
 * ist ein Fachthema von StockInfo, kein hausweites Muster.
 */
defineProps<{ items: RejectedInstrument[] }>()

const { t, te } = useI18n()

/**
 * Der Satz zu einer Ablehnungskennung.
 *
 * Die Kennung kommt stabil vom Server, der Text steht im Katalog. Eine
 * **unbekannte** Kennung fällt nicht stumm heraus, sondern wird angezeigt, wie
 * sie ist: Sonst stünde für ein entferntes Papier gar kein Grund da — und der
 * ist der eigentliche Zweck dieser Liste.
 */
function reasonText(reason: string): string {
  const key = `migration.reason.${reason}`
  return te(key) ? t(key) : reason
}
</script>

<template>
  <ul class="rejected">
    <li v-for="item in items" :key="item.symbol" class="rejected__row">
      <div class="rejected__head">
        <span class="rejected__symbol">{{ item.symbol }}</span>
        <span v-if="item.name" class="rejected__name">{{ item.name }}</span>
        <span v-if="item.isin" class="rejected__isin">{{ item.isin }}</span>
      </div>
      <p class="rejected__reason">{{ reasonText(item.reason) }}</p>
      <p class="rejected__loss">
        {{ t('migration.rowLoss', { quotes: item.quotes, daily: item.daily_closes }) }}
      </p>
    </li>
  </ul>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.rejected {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;

  &__row {
    padding: 0.75rem 1rem;
    border-radius: $radius;
    background: $color-surface;
    border-left: 3px solid $color-danger;
  }

  &__head {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 0.5rem;
  }

  &__symbol {
    font-family: $font-mono;
    font-weight: 600;
    color: $color-text;
  }

  &__name,
  &__isin {
    // `min-width: 0` an jedem Flex-Kind mit Text: Ohne es ist die
    // Mindestbreite der längste unteilbare Inhalt und sprengt die Zeile.
    min-width: 0;
    color: $color-muted;
    font-size: 0.85rem;
  }

  &__isin {
    font-family: $font-mono;
  }

  &__reason,
  &__loss {
    margin: 0.3rem 0 0;
    font-size: 0.85rem;
    color: $color-muted;
  }
}
</style>
