<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { NButton, NInput } from 'naive-ui'
import { UxInlineNumber } from '@mmit/ux-foundation'

import { manualValue, overrideState } from '../composables/useOverrides'
import type { InstrumentOverrides, InstrumentSummary, OverrideField } from '../types'

/**
 * Die Bearbeitungs-Hälfte einer Kennzahl (T-15) — für die Schublade (Task 8).
 *
 * Hervorgegangen aus `ManualMetric.vue`, aber auf eine Hälfte verkleinert:
 * Den wirksamen Wert **anzuzeigen** ist seit Task 6 Sache von
 * `MetricValue.vue`; hier geht es nur ums Ändern. Dieselbe Vorrang-Regel
 * entscheidet, ob überhaupt etwas zu ändern ist — was die Quelle liefert,
 * gewinnt, ein eigener Wert füllt nur Lücken.
 *
 * Acht Felder, drei Bedienarten: Zahl (`UxInlineNumber`), Text (`NInput`,
 * Commit beim Verlassen) und der Dreier-Umschalter für die Thesaurierung.
 * Welche Art zu welchem Feld gehört, steht als Tabelle da — eine Verzweigung
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

const textValue = computed(() => (typeof manual.value === 'string' ? manual.value : ''))

/** Entwurf des Textfelds — committet wird erst beim Verlassen, nicht je Tastendruck. */
const textDraft = ref<string>(textValue.value)
watch(textValue, (value) => {
  textDraft.value = value
})

function onTextBlur(): void {
  const trimmed = textDraft.value.trim()
  const next = trimmed === '' ? null : trimmed
  if (next === (textValue.value || null)) return
  commit({ [props.field]: next } as Partial<InstrumentOverrides>)
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

      <NInput
        v-else
        v-model:value="textDraft"
        size="small"
        :disabled="busy"
        @blur="onTextBlur"
      />
    </template>

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
