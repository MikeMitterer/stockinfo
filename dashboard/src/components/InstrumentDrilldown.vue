<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import InfoHint from './InfoHint.vue'
import MetricEditor from './MetricEditor.vue'
import { sourceProvides } from '../composables/useOverrides'
import { OVERRIDE_FIELDS } from '../types'
import type { InstrumentOverrides, InstrumentSummary, OverrideField } from '../types'
import { formatDateTime } from '../utils/datetime'
import { FIELD_LABEL_KEY } from '../utils/fieldLabels'
import { isEuropeanIsin } from '../utils/isin'

/**
 * Die aufklappbare Zeile (Task 8) — Pflege aller acht ETF-Kennzahlen an einer
 * Stelle, egal ob aus der Tabelle oder der Kartenliste geöffnet.
 *
 * Die acht Felder stehen oben, mehrspaltig auf breitem Schirm; die Herkunft
 * (Zeitpunkt der letzten Metadaten-Abfrage, Erklärung) folgt darunter als
 * schmale Fußzeile, durch eine feine Linie abgesetzt (Nacharbeit Sichtprüfung,
 * Befund 3 — vorher zweispaltig, mit einer rechten Spalte, die meist fast leer
 * blieb).
 *
 * Die allgemeine Erklärung — woher die Daten kommen, dass sich nur ergänzen
 * lässt, was die Quelle nicht liefert — bleibt immer erreichbar, steht aber
 * nicht mehr dauerhaft im Text: Sie beantwortet eine Frage, die man einmal hat
 * und danach nicht mehr, und nahm als Dauertext mehr Raum ein als die
 * Kennzahlen darüber. Sie sitzt im Fragezeichen hinter dem Zeitstempel.
 *
 * Die Sonderfälle dagegen **stehen** da, denn sie sind keine Erklärung, sondern
 * ein Befund über genau dieses Papier — sie kommen dazu, wenn sie zutreffen:
 * für nicht-europäische ISINs überspringt das Backend die Quelle bewusst
 * (`is_european_isin` in `app/providers/justetf_provider.py`), und wenn die
 * Quelle abgefragt wurde, aber nichts geliefert hat.
 */
const props = defineProps<{
  item: InstrumentSummary
  /** Solange gespeichert wird, nichts anfassen. */
  busy?: boolean
  /**
   * Vorschläge je Textfeld — einmal weiter oben (in `AppDashboard.vue`)
   * gebildet, hier nur an den passenden `MetricEditor` gereicht.
   */
  fieldOptions?: Partial<Record<OverrideField, string[]>>
}>()

const emit = defineEmits<{
  (event: 'commit', patch: Partial<InstrumentOverrides>): void
}>()

const { t, locale } = useI18n()

/** Vorschläge des jeweiligen Felds — `undefined` für die vier Nicht-Textfelder. */
function optionsFor(field: OverrideField): string[] | undefined {
  return props.fieldOptions?.[field]
}

function onCommit(patch: Partial<InstrumentOverrides>): void {
  emit('commit', patch)
}

/**
 * Hat die Quelle für irgendeines der acht Felder etwas beigesteuert?
 *
 * Geprüft wird der **Quellenwert**, nicht der wirksame: Ein von Hand
 * eingetragener Wert (`overrideState === 'manual'`) füllt eine Lücke, die die
 * Quelle gelassen hat — er zählt hier nicht als ihr Beitrag.
 */
const sourceEmpty = computed(() => OVERRIDE_FIELDS.every((field) => !sourceProvides(props.item, field)))

/**
 * Warum justETF nichts beigesteuert hat — vier sich gegenseitig ausschließende
 * Gründe (Nacharbeit Sichtprüfung, I2).
 *
 * Die Reihenfolge ist **kein** Stilmittel, sondern gehört dorthin: Sie spiegelt
 * die Prüfung des Backends (`app/services/quote_service.py:137`,
 * `if instrument_type == "etf" and isin:`, dahinter `is_european_isin()` in
 * `justetf_provider.py`). Vertauscht man sie, behauptet die Erklärung einen
 * Grund, der nicht der tatsächliche ist — genau der Fehler, den diese
 * Nacharbeit behebt: Eine Aktie mit europäischer ISIN bekam „Quelle wurde
 * abgefragt, hat nichts geliefert" (sie wurde nie abgefragt), ein Papier ohne
 * ISIN bekam „Diese ISIN liegt außerhalb" (es gibt keine).
 */
const skipReason = computed<'notEtf' | 'noIsin' | 'notEuropean' | 'empty' | null>(() => {
  if (props.item.type !== 'etf') return 'notEtf'
  if (!props.item.isin) return 'noIsin'
  if (!isEuropeanIsin(props.item.isin)) return 'notEuropean'
  return sourceEmpty.value ? 'empty' : null
})

const fetchedAt = computed(() =>
  props.item.meta_fetched_at ? formatDateTime(props.item.meta_fetched_at, locale.value) : null,
)
</script>

<template>
  <div class="drilldown">
    <dl class="drilldown__fields">
      <!--
        Die Fläche markiert, wo etwas zu tun ist — nicht jedes Feld. Wo die
        Quelle liefert, ist das Feld gesperrt (Vorrang-Regel), und eine
        Hervorhebung behauptete dort eine Möglichkeit, die es nicht gibt.
      -->
      <div
        v-for="field in OVERRIDE_FIELDS"
        :key="field"
        class="drilldown__field"
        :class="{ 'drilldown__field--editable': !sourceProvides(item, field) }"
      >
        <dt class="drilldown__label">{{ t(FIELD_LABEL_KEY[field]) }}</dt>
        <dd class="drilldown__value">
          <MetricEditor
            :item="item"
            :field="field"
            :busy="busy"
            :options="optionsFor(field)"
            @commit="onCommit"
          />
        </dd>
      </div>
    </dl>

    <div class="drilldown__source">
      <!--
        Zuerst wer, dann wann: Ohne Absender ist der Zeitstempel eine Zahl ohne
        Aussage. `yfinance` allein heißt „justETF war nicht dabei",
        `yfinance+justetf` heißt „die ETF-Extras kommen von dort".
      -->
      <p v-if="item.source" class="drilldown__fetched">
        {{ t('drilldown.source') }}: <span class="mono">{{ item.source }}</span>
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
      <p v-if="skipReason === 'notEtf'" class="drilldown__explain">{{ t('drilldown.notEtf') }}</p>
      <p v-else-if="skipReason === 'noIsin'" class="drilldown__explain">{{ t('drilldown.noIsin') }}</p>
      <p v-else-if="skipReason === 'notEuropean'" class="drilldown__explain">{{ t('drilldown.noEuropeanSource') }}</p>
      <p v-else-if="skipReason === 'empty'" class="drilldown__explain">{{ t('drilldown.sourceEmpty') }}</p>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

/*
 * Nacharbeit Sichtprüfung, Befund 3: vorher zweispaltig — links bearbeiten,
 * rechts nachlesen. Bei acht Feldern links und kaum mehr als einem Zeitstempel
 * rechts blieb die rechte Spalte fast leer, der Schnitt wirkte kaputt.
 *
 * Jetzt einspaltig gestapelt: Die acht Felder oben bekommen die ganze Breite
 * (mehrspaltig ab `md`, siehe `.drilldown__fields`), die Herkunft folgt darunter
 * als schmale Fußzeile, durch `.drilldown__source` von den Feldern abgesetzt.
 * Unter `md` ist das ohnehin die einzig sinnvolle Aufteilung — dort ist die
 * Detailbereich der aufgeklappte Teil einer Karte, mit entsprechend wenig Breite.
 */
.drilldown {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-3) var(--space-1);
}

// Einspaltig unter `md` — mehrspaltig erst, wo tatsächlich Breite dafür da
// ist. Zwei Spalten ab `md`, drei ab `lg`: Die Breite gehört dem, wovon es
// viel gibt (acht Felder), nicht einer fast leeren zweiten Spalte.
.drilldown__fields {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-2) var(--space-6);
  margin: 0;

  @include up(md) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  @include up(lg) {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

.drilldown__field {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2);
  border-radius: var(--radius-sm);
}

/*
 * Nur die pflegbaren Felder bekommen eine Fläche — sie sagt „hier lässt sich
 * etwas eintragen". Läge sie unter jedem Feld, sagte sie nichts: Wo die Quelle
 * liefert, hat sie Vorrang und das Feld ist gesperrt.
 *
 * Bewusst schwach: eine getönte Fläche ohne Rand und ohne abgesetzten Schatten.
 * Ein Kasten mit Kante zog die Aufmerksamkeit auf den Rahmen statt auf den
 * Inhalt. Der Ton kommt vom Akzent und nicht aus Grau — auf den dunklen Themes
 * verschwindet eine graue Aufhellung, eine getönte trägt in beide Richtungen.
 * Deckkraft über `token()`, weil die Farben im Fundament als RGB-Tripel liegen;
 * mit Hex-Werten bliebe die Fläche unsichtbar.
 */
.drilldown__field--editable {
  background: token(--accent, 0.06);
}

.drilldown__label { color: $color-muted; font-size: var(--font-sm); }
.drilldown__value { display: flex; justify-content: flex-start; }

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

.drilldown__explain { margin: 0; }
</style>
