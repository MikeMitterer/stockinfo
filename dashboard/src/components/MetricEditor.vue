<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { NButton, NSelect } from 'naive-ui'
import { UxInlineNumber } from '@mmit/ux-foundation'

import MetricValue from './MetricValue.vue'
import { manualValue, overrideState } from '../composables/useOverrides'
import type { InstrumentOverrides, InstrumentSummary, OverrideField } from '../types'

/**
 * Die Bearbeitungs-Hälfte einer Kennzahl (T-15) — für die Schublade (Task 8).
 *
 * Hervorgegangen aus `ManualMetric.vue`, aber auf eine Hälfte verkleinert:
 * Den wirksamen Wert **anzuzeigen** ist seit Task 6 Sache von
 * `MetricValue.vue`; hier geht es ums Ändern. Dieselbe Vorrang-Regel
 * entscheidet, ob überhaupt etwas zu ändern ist — was die Quelle liefert,
 * gewinnt, ein eigener Wert füllt nur Lücken.
 *
 * Ist ein Feld gesperrt, verschwindet nur die **Bedienung** — der wirksame
 * Wert bleibt stehen, gerendert über `MetricValue` (Nacharbeit Sichtprüfung,
 * Befund 1). Ohne das zeigte ein gesperrtes Feld ohne eigenen Wert acht
 * Beschriftungen und daneben nichts: kein Wert, keine Erklärung. Eine dritte
 * Anzeige-Komponente dafür zu bauen wäre dieselbe Aussage ein zweites Mal —
 * `MetricValue` kann das bereits.
 *
 * Acht Felder, drei Bedienarten: Zahl (`UxInlineNumber`), der Dreier-
 * Umschalter für die Thesaurierung, und Text als Auswahl mit freier Eingabe
 * (`NSelect` mit `filterable` + `tag`). Reine Auswahl wäre für die Textfelder
 * falsch: Ein Fonds mit unbekanntem Anbieter oder Domizil wäre sonst gar
 * nicht pflegbar — genau für solche Fälle ist das Feature gedacht. Welche
 * Bedienart zu welchem Feld gehört, steht als Tabelle da — eine Verzweigung
 * mit acht gleichförmigen Zweigen wäre dieselbe Aussage, nur ausführlicher.
 *
 * Neu gegenüber `ManualMetric.vue`: der Entfernen-Knopf. Er erscheint immer,
 * wenn ein eigener Wert existiert — **auch im gesperrten Zustand**. Ohne ihn
 * wäre das Feature eine Falle: Wer während eines Quellen-Ausfalls acht Felder
 * nachträgt, käme nach dessen Ende an keines davon mehr heran, außer per
 * direktem API-Aufruf.
 */
const props = defineProps<{
  item: InstrumentSummary
  field: OverrideField
  /** Solange gespeichert wird, nichts anfassen. */
  busy?: boolean
  /**
   * Vorschlagswerte für die vier Textfelder — hier nur durchgereicht, nicht
   * ermittelt.
   *
   * Diese Komponente kennt weder die Instrumentenliste noch die
   * Börsentabelle, aus denen sich die Vorschläge ableiten (Anbieter,
   * Replikationsart und Fondsdomizil aus den geladenen Instrumenten;
   * Fondswährung aus `currenciesFromExchanges()`). Das bleibt bewusst eine
   * Ebene höher: Acht `MetricEditor` je Zeile dürften diese Ableitung nicht
   * acht Mal wiederholen, und ein Prop-Drilling von Instrumentenliste oder
   * Börsentabelle bis in dieses Blatt hätte diese Komponente unnötig an
   * Datenquellen gekoppelt, die mit ihrer eigentlichen Aufgabe nichts zu tun
   * haben.
   */
  options?: string[]
}>()

const emit = defineEmits<{
  (event: 'commit', patch: Partial<InstrumentOverrides>): void
}>()

const { t, n } = useI18n()

type FieldKind = 'number' | 'boolean' | 'text'

/** Bedienart je Feld — steuert, welcher Zweig im Template greift. */
const FIELD_KIND: Record<OverrideField, FieldKind> = {
  ter: 'number',
  volatility: 'number',
  fund_size: 'number',
  accumulating: 'boolean',
  provider: 'text',
  replication: 'text',
  fund_domicile: 'text',
  fund_currency: 'text',
}

const kind = computed(() => FIELD_KIND[props.field])

const state = computed(() => overrideState(props.item, props.field))

/** Der wirksame Wert — er entscheidet, ob die Quelle etwas beisteuert. */
const effectiveValue = computed(() => props.item[props.field])

/**
 * Liefert die Quelle etwas? Dann wird hier nichts gepflegt.
 *
 * Erkannt am Zustand, nicht an einem zweiten Feld: Steht der wirksame Wert
 * auf `manual`, kommt er aus der Eingabe und die Quelle hat nichts. Sonst ist
 * der wirksame Wert der der Quelle — und ist er gesetzt, ist hier zu.
 */
const editable = computed(() => !(state.value !== 'manual' && effectiveValue.value !== null))

/** Der von Hand eingetragene Rohwert — das, was bearbeitet und entfernt wird. */
const manual = computed(() => manualValue(props.item, props.field))

/**
 * Der Entfernen-Knopf steht unabhängig vom Sperr-Zustand zur Verfügung.
 *
 * Bewusste Ausnahme von der Vorrang-Regel — siehe Kommentar am Komponenten-
 * kopf. Ohne sie käme man an einen verdeckten Wert nur noch per API-Aufruf
 * heran, sobald die Quelle doch etwas liefert.
 */
const removable = computed(() => manual.value !== null)

function commit(patch: Partial<InstrumentOverrides>): void {
  emit('commit', patch)
}

function onRemove(): void {
  commit({ [props.field]: null } as Partial<InstrumentOverrides>)
}

// ─── Zahlenfelder (ter, volatility, fund_size) ─────────────────────────────

const DIGITS = { minimumFractionDigits: 2, maximumFractionDigits: 2 }

/** Obergrenze je Zahlenfeld — dieselben Werte prüft das Backend noch einmal. */
const NUMBER_MAX: Partial<Record<OverrideField, number>> = {
  ter: 5,
  volatility: 500,
  fund_size: 2_000_000,
}

const numericValue = computed(() => (typeof manual.value === 'number' ? manual.value : null))

const numberMax = computed(() => NUMBER_MAX[props.field] ?? Number.MAX_SAFE_INTEGER)

/** Fondsvolumen ist keine Prozentzahl — TER und Volatilität schon. */
const numberDisplay = computed(() => {
  if (numericValue.value === null) return '—'
  const formatted = n(numericValue.value, DIGITS)
  return props.field === 'fund_size' ? formatted : `${formatted} %`
})

function onNumber(value: number | null): void {
  commit({ [props.field]: value } as Partial<InstrumentOverrides>)
}

// ─── Thesaurierung ──────────────────────────────────────────────────────────

/**
 * Der nächste Zustand: ja → nein → nicht gesetzt → ja.
 *
 * Ausgeschrieben statt als Nachschlagetabelle — wie in `ManualMetric.vue`:
 * Ein `?? true` würde das gültige Ergebnis `null` verschlucken.
 */
function nextAccumulating(value: boolean | null): boolean | null {
  if (value === true) return false
  if (value === false) return null
  return true
}

/*
 * Gezykelt wird der **eingetragene** Wert, nicht der wirksame. Der Umschalter
 * ist ohnehin nur sichtbar, solange die Quelle nichts liefert — dort sind
 * beide Werte identisch, aber der eingetragene ist der, den wir ändern.
 */
const nextAccumulatingValue = computed(() => nextAccumulating(props.item.manual_accumulating))

const toggleTitle = computed(() =>
  t('overrides.cycleTo', {
    value:
      nextAccumulatingValue.value === null
        ? t('overrides.notSet')
        : nextAccumulatingValue.value
          ? t('table.yes')
          : t('table.no'),
  }),
)

function onToggle(): void {
  commit({ accumulating: nextAccumulatingValue.value })
}

// ─── Textfelder (provider, replication, fund_domicile, fund_currency) ──────

/** Der eingetragene Wert, `null` statt `''` — `NSelect` erwartet das für „nichts gewählt". */
const selectValue = computed(() => (typeof manual.value === 'string' ? manual.value : null))

/** `NSelect` will Label/Value-Paare; hier sind beide gleich, das Label ist der Wert selbst. */
const selectOptions = computed(() =>
  (props.options ?? []).map((value) => ({ label: value, value })),
)

/** Katalog-Schlüssel der Feldbeschriftung — als Platzhalter im leeren Auswahlfeld. */
const TEXT_FIELD_LABEL_KEY: Partial<Record<OverrideField, string>> = {
  provider: 'overrides.fields.provider',
  replication: 'overrides.fields.replication',
  fund_domicile: 'overrides.fields.fundDomicile',
  fund_currency: 'overrides.fields.fundCurrency',
}

const selectPlaceholder = computed(() => {
  const key = TEXT_FIELD_LABEL_KEY[props.field]
  return key ? t(key) : undefined
})

/**
 * `NSelect` mit `tag` feuert dieses Event erst, wenn eine Auswahl (bestehend
 * oder neu getippt und bestätigt) feststeht — anders als beim reinen Textfeld
 * gibt es hier keinen offenen Entwurf, der noch zwischengespeichert werden
 * müsste.
 */
function onSelect(value: string | null): void {
  commit({ [props.field]: value } as Partial<InstrumentOverrides>)
}
</script>

<template>
  <span class="metric-editor">
    <template v-if="editable">
      <button
        v-if="kind === 'boolean'"
        type="button"
        class="metric-editor__toggle"
        :disabled="busy"
        :title="toggleTitle"
        @click="onToggle"
      >
        <span
          v-if="item.manual_accumulating !== null"
          class="badge thes"
          :class="{ acc: item.manual_accumulating }"
        >{{ item.manual_accumulating ? t('table.yes') : t('table.no') }}</span>
        <span
          v-else
          class="metric-editor__empty"
        >—</span>
      </button>

      <UxInlineNumber
        v-else-if="kind === 'number'"
        :value="numericValue"
        :display="numberDisplay"
        :precision="2"
        :min="0"
        :max="numberMax"
        :empty-value="null"
        :disabled="busy"
        :edit-label="t('overrides.edit')"
        :clear-label="t('overrides.clear')"
        @commit="onNumber"
      />

      <NSelect
        v-else
        :value="selectValue"
        :options="selectOptions"
        filterable
        tag
        size="small"
        :disabled="busy"
        :placeholder="selectPlaceholder"
        @update:value="onSelect"
      />
    </template>

    <MetricValue v-else :item="item" :field="field" />

    <NButton
      v-if="removable"
      class="metric-editor__remove"
      size="tiny"
      quaternary
      :disabled="busy"
      :title="t('overrides.removeOwn')"
      @click="onRemove"
    >
      ✕
    </NButton>
  </span>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.metric-editor {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;

  &__toggle {
    display: inline-flex;
    border: none;
    background: none;
    padding: 0;
    cursor: pointer;
    font: inherit;
    color: inherit;
  }

  &__empty { color: $color-muted; }
}

// Lokale Variante der globalen .badge-Pill — dieselben Farben wie die
// Anzeige-Hälfte (`MetricValue.vue`), hier aber im eigenen Scope nötig, weil
// die Badge innerhalb dieser Komponente gerendert wird.
.badge.thes {
  color: $color-muted;
  background: $color-surface-2;
  &.acc { color: $color-accent; background: token(--accent, 0.15); }
}
</style>
