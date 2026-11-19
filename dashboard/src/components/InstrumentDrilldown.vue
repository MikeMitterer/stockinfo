<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import InfoHint from './InfoHint.vue'
import OpenDetails from './OpenDetails.vue'
import type { OverridePatch, InstrumentSummary } from '../types'
import { formatDateTime } from '../utils/datetime'

/**
 * Die aufklappbare Zeile (Task 8) — Pflege der Kennzahlen an einer Stelle,
 * egal ob aus der Tabelle oder der Kartenliste geöffnet.
 *
 * Die Felder kommen aus `details` und dem Feldkatalog (`OpenDetails`). Bis
 * T-141 gab es daneben einen zweiten, älteren Weg über `MetricEditor` für ein
 * Backend ohne `details`; Dashboard und Backend kommen im selben Image, und das
 * Backend schickt `details` immer (Entscheidung q-9).
 *
 * Die Herkunft (Quelle, Zeitpunkt, Erklärung) folgt darunter als schmale
 * Fußzeile, durch eine feine Linie abgesetzt. Die allgemeine Erklärung — woher
 * die Daten kommen, dass sich nur ergänzen lässt, was die Quelle nicht liefert
 * — sitzt im Hinweis hinter dem Zeitstempel statt als Dauertext.
 */
const props = defineProps<{
  item: InstrumentSummary
  /** Solange gespeichert wird, nichts anfassen. */
  busy?: boolean
  /** Vorschläge je Textfeld — einmal weiter oben (in `AppDashboard.vue`) gebildet. */
  fieldOptions?: Partial<Record<string, string[]>>
}>()

const emit = defineEmits<{
  (event: 'commit', patch: OverridePatch): void
}>()

const { t, locale } = useI18n()

function onCommit(patch: OverridePatch): void {
  emit('commit', patch)
}

/** StockInfos eigene Berechnung (`app/calculated_metrics.py`), kein Plugin aus `sources.yaml`. */
const calculatedSource = 'calculated'

/** Die sichtbaren Quellenwerte, aus denen die Fußzeile Herkunft und Stand bildet. */
const providerValues = computed(() => Object.values(props.item.details)
  .filter((value) => value.origin === 'provider' && value.source))

/**
 * Stand: der letzte Metadatenabruf, sonst der jüngste Stand der angezeigten
 * Quellenwerte. Bei einer Aktie gibt es keinen Metadatenabruf; ihre berechnete
 * Volatilität trägt das Datum des letzten Schlusskurses.
 */
const fetchedAt = computed(() => {
  const latest = props.item.meta_fetched_at ?? providerValues.value
    .map((value) => value.as_of)
    .filter((asOf): asOf is string => Boolean(asOf))
    .sort()
    .at(-1)
  return latest ? formatDateTime(latest, locale.value) : null
})

/** Die Fußzeile fasst die Herkunft der sichtbaren Quellenwerte zusammen. */
const detailSources = computed(() => [...new Set(providerValues.value.map((value) =>
  value.source === calculatedSource ? t('drilldown.sourceCalculated') : value.source,
))].sort().join(' + '))
</script>

<template>
  <div class="drilldown">
    <OpenDetails :item="item" :busy="busy" :field-options="fieldOptions" @commit="onCommit" />

    <div class="drilldown__source">
      <!--
        Zuerst wer, dann wann: Ohne Absender ist der Zeitstempel eine Zahl ohne
        Aussage. Der Name kommt aus der Antwort und nennt die Quelle, die
        tatsächlich geliefert hat — im Online-Profil etwa `justetf`, im
        CSV-Profil `metadata-file`. Er wird hier **nicht** gedeutet: Welche
        Namen es gibt, entscheidet `sources.yaml`. Einzige Ausnahme ist
        StockInfos eigene Berechnung `calculated`; sie ist kein Plugin und
        erscheint deshalb übersetzt.
      -->
      <p v-if="detailSources" class="drilldown__fetched">
        {{ t('drilldown.source') }}: <span class="mono">{{ detailSources }}</span>
      </p>
      <!--
        Der Absatz steht immer, auch ohne Zeitstempel: Er trägt das
        Fragezeichen, und gerade wer einen leeren Detailbereich vor sich hat, will
        wissen, woher hier etwas herkommen soll. Ohne Zeitstempel bleibt nur
        der Hinweis übrig.
      -->
      <p class="drilldown__fetched">
        <template v-if="fetchedAt"
          >{{ t('drilldown.fetchedAt') }}: <span class="mono">{{ fetchedAt }}</span>
        </template>
        <InfoHint :text="t('drilldown.explain')" icon="info" />
      </p>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

/*
 * Einspaltig gestapelt: Die Felder oben bekommen die ganze Breite, die
 * Herkunft folgt darunter als schmale Fußzeile, durch `.drilldown__source`
 * abgesetzt (Nacharbeit Sichtprüfung, Befund 3 — vorher zweispaltig, mit einer
 * fast leeren rechten Spalte).
 */
.drilldown {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-3) var(--space-1);
}

// Schmale Fußzeile, per feiner Linie von den Feldern abgesetzt.
.drilldown__source {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  max-width: 72ch;
  padding-top: var(--space-3);
  border-top: 1px solid token(--border-default, 0.55);
  font-size: var(--font-sm);
  color: $color-muted;
}

/*
 * Kleiner und leiser als der Rest der Fußzeile: Herkunft und Zeitstempel sind
 * Beleg, nicht Inhalt — man sucht sie, wenn eine Zahl fragwürdig aussieht, und
 * überliest sie sonst. Der Befund darunter (`__explain`) behält die volle
 * Größe: Er sagt, warum ein Feld leer ist, und das ist keine Fußnote.
 */
.drilldown__fetched {
  margin: 0;
  font-size: var(--font-xs);
  opacity: 0.8;
}

/*
 * Abstand zum Zeitstempel davor. Ohne ihn klebt der Auslöser an der Zahl: Er
 * ist ein runder Kasten von 16 px neben Text von 12 px und braucht mehr Luft
 * als ein Buchstabe. Gemessen war die Lücke vorher 0 px — das Leerzeichen aus
 * dem Markup fällt beim Übersetzen weg.
 *
 * `:deep()` ist hier **nötig**, nicht bequem: Das Scope-Merkmal einer
 * Komponente landet nur am **Wurzelknoten** ihrer direkten Kinder. Der Auslöser
 * steckt zwei Ebenen tiefer (`InfoHint` → `UxInfoHint` → `NTooltip`-Slot) und
 * trägt es deshalb nicht — eine gewöhnliche Regel greift dort nie. Beim Pfeil
 * daneben geht es ohne, weil dessen Wurzel selbst das `svg` ist.
 *
 * Der Abstand gehört hierher und nicht ins Fundament: Wie eng es zugeht, weiß
 * nur die Umgebung.
 */
.drilldown__fetched :deep(.ux-hint__trigger) {
  margin-left: 0.4rem;

  /*
   * Optische Korrektur nach oben. Rechnerisch sitzt der Auslöser mittig — der
   * Kasten war 0,7 px von der Textmitte entfernt —, er **wirkt** aber zu tief.
   * Der Grund ist `vertical-align: middle`: Es richtet an der Grundlinie plus
   * halber x-Höhe aus, und diese Zeile besteht aus **Ziffern**. Die stehen auf
   * Versalhöhe, also deutlich über der x-Höhe; ihre optische Mitte liegt damit
   * höher als die Bezugslinie.
   *
   * Zwei Pixel, mit Augen bestimmt und nicht gerechnet: Bei einem Pixel blieb
   * der Rest sichtbar. Eine feste Verschiebung ist hier gefahrlos, anders als
   * beim Pfeil — der Kreis dreht sich nicht.
   */
  position: relative;
  top: -2px;
}
</style>
