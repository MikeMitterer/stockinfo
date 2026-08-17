<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

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
 * Die Erklärung selbst trägt immer, nicht nur in Ausnahmefällen (Befund 2):
 * woher die Daten kommen und dass sich nur ergänzen lässt, was die Quelle
 * nicht liefert. Zwei Sonderfälle kommen zusätzlich dazu, wenn sie zutreffen —
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
      <div v-for="field in OVERRIDE_FIELDS" :key="field" class="drilldown__field">
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
      <p v-if="fetchedAt" class="drilldown__fetched">
        {{ t('drilldown.fetchedAt') }}: <span class="mono">{{ fetchedAt }}</span>
      </p>
      <!--
        Trägt immer, unabhängig vom Zustand der Quelle — anders als die beiden
        Sonderfälle darunter, die nur in ihrem jeweiligen Ausnahmefall dazukommen
        (Nacharbeit Sichtprüfung, Befund 2).
      -->
      <p class="drilldown__explain">{{ t('drilldown.explain') }}</p>
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
 * Schublade der aufgeklappte Teil einer Karte, mit entsprechend wenig Breite.
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
}

.drilldown__label { color: $color-muted; font-size: 0.85rem; }
.drilldown__value { display: flex; justify-content: flex-start; }

// Schmale Fußzeile, per feiner Linie von den Feldern abgesetzt.
.drilldown__source {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  max-width: 72ch;
  padding-top: var(--space-3);
  border-top: 1px solid token(--border-default, 0.55);
  font-size: 0.85rem;
  color: $color-muted;
}

.drilldown__fetched { margin: 0; }
.drilldown__explain { margin: 0; }
</style>
