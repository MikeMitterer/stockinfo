<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import MetricEditor from './MetricEditor.vue'
import { overrideState } from '../composables/useOverrides'
import { OVERRIDE_FIELDS } from '../types'
import type { InstrumentOverrides, InstrumentSummary, OverrideField } from '../types'
import { formatDateTime } from '../utils/datetime'
import { isEuropeanIsin } from '../utils/isin'

/**
 * Die aufklappbare Zeile (Task 8) — Pflege aller acht ETF-Kennzahlen an einer
 * Stelle, egal ob aus der Tabelle oder der Kartenliste geöffnet.
 *
 * Zweispaltig, wie für aufgeklappte Zeilen festgelegt: links bearbeiten (acht
 * `MetricEditor`), rechts nachlesen — Zeitpunkt der letzten Metadaten-Abfrage
 * und, falls justETF nichts beigesteuert hat, **warum**. Genau diese Erklärung
 * fehlte bisher: Für nicht-europäische ISINs überspringt das Backend die
 * Quelle bewusst (`is_european_isin` in `app/providers/justetf_provider.py`),
 * ohne dass die Oberfläche das je gesagt hätte.
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

/** Beschriftung je Feld — dieselben Katalog-Einträge wie Tabellenkopf und Editor. */
const FIELD_LABEL_KEY: Record<OverrideField, string> = {
  ter: 'table.colTer',
  volatility: 'table.colVola',
  accumulating: 'table.colAccumulating',
  provider: 'overrides.fields.provider',
  replication: 'overrides.fields.replication',
  fund_size: 'overrides.fields.fundSize',
  fund_domicile: 'overrides.fields.fundDomicile',
  fund_currency: 'overrides.fields.fundCurrency',
}

/** Vorschläge des jeweiligen Felds — `undefined` für die vier Nicht-Textfelder. */
function optionsFor(field: OverrideField): string[] | undefined {
  return props.fieldOptions?.[field]
}

function onCommit(patch: Partial<InstrumentOverrides>): void {
  emit('commit', patch)
}

const european = computed(() => isEuropeanIsin(props.item.isin))

/**
 * Hat die Quelle für irgendeines der acht Felder etwas beigesteuert?
 *
 * Geprüft wird der **Quellenwert**, nicht der wirksame: Ein von Hand
 * eingetragener Wert (`overrideState === 'manual'`) füllt eine Lücke, die die
 * Quelle gelassen hat — er zählt hier nicht als ihr Beitrag.
 */
const sourceEmpty = computed(() =>
  OVERRIDE_FIELDS.every((field) => {
    const state = overrideState(props.item, field)
    const sourceValue = state === 'manual' ? null : props.item[field]
    return sourceValue === null
  }),
)

const fetchedAt = computed(() =>
  props.item.meta_fetched_at ? formatDateTime(props.item.meta_fetched_at, locale.value) : null,
)
</script>

<template>
  <div class="drilldown">
    <dl class="drilldown__fields">
      <template v-for="field in OVERRIDE_FIELDS" :key="field">
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
      </template>
    </dl>

    <div class="drilldown__source">
      <p v-if="fetchedAt" class="drilldown__fetched">
        {{ t('drilldown.fetchedAt') }}: <span class="mono">{{ fetchedAt }}</span>
      </p>
      <p v-if="!european" class="drilldown__explain">{{ t('drilldown.noEuropeanSource') }}</p>
      <p v-else-if="sourceEmpty" class="drilldown__explain">{{ t('drilldown.sourceEmpty') }}</p>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

// Zweispaltig — links bearbeiten, rechts nachlesen (ux-standards: „aufgeklappter
// Bereich ist zweispaltig"). Unter der Kartenliste bleibt kaum mehr Breite als
// die einer Spalte übrig, dort fällt die Aufteilung von selbst auf eine Spalte.
.drilldown {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(0, 1fr);
  gap: 1rem 1.5rem;
  padding: 0.75rem 0.25rem;

  @media (max-width: 30rem) {
    grid-template-columns: 1fr;
  }
}

.drilldown__fields {
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: center;
  gap: 0.5rem 0.75rem;
  margin: 0;
}

.drilldown__label { color: $color-muted; font-size: 0.85rem; }
.drilldown__value { display: flex; justify-content: flex-start; }

.drilldown__source {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  font-size: 0.85rem;
  color: $color-muted;
}

.drilldown__fetched { margin: 0; }
.drilldown__explain { margin: 0; }
</style>
