<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { UxInlineNumber } from '@mikemitterer/ux-foundation'

import { manualValue, overrideState } from '../composables/useOverrides'
import type { InstrumentOverrides, InstrumentSummary, OverrideField } from '../types'

/**
 * Eine Kennzahl, die sich von Hand nachtragen lässt (T-09).
 *
 * Zeigt den **wirksamen** Wert und macht ihn an Ort und Stelle bearbeitbar —
 * kein Dialog für eine Zahl. Die Vorrang-Regel wendet das Backend an: Was die
 * Quelle liefert, gewinnt; eine Eingabe füllt nur Lücken.
 *
 * Genau deshalb braucht es die Kennzeichnung daneben. Ohne sie wäre nicht zu
 * erklären, warum ein eingetragener Wert nicht dasteht — und beim nächsten
 * Kurs-Update sähe es aus, als sei er verloren.
 *
 * **Bleibt in dieser App**, obwohl sie aussieht wie ein Baustein: Sie kennt
 * `InstrumentSummary` und die Namen der drei Kennzahlen, also ein Datenmodell,
 * das nur StockInfo hat. Was allgemein war — die Zahl in der Zeile samt dem
 * Zustand „nicht gesetzt" — liegt als `UxInlineNumber` im Fundament.
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

const zustand = computed(() => overrideState(props.item, props.field))

/** Der wirksame Wert — das, was die Zelle zeigt. */
const wert = computed<number | boolean | null>(() => {
  if (props.field === 'ter') return props.item.ter
  if (props.field === 'volatility') return props.item.volatility
  return props.item.accumulating
})

const zahl = computed(() => (typeof wert.value === 'number' ? wert.value : null))

/**
 * Obergrenze je Kennzahl — dieselben Werte prüft das Backend noch einmal.
 *
 * Zwei Stellen sind hier unvermeidbar: Das Feld soll beim Tippen begrenzen,
 * und der Endpoint darf sich nicht auf die Oberfläche verlassen. Die Zahlen
 * sind bewusst großzügig — sie fangen Tippfehler ab, nicht Meinungen.
 */
const maximum = computed(() => (props.field === 'ter' ? 100 : 500))

/*
 * Immer zwei Nachkommastellen, und über `n()` statt `toFixed`.
 *
 * Zwei Gründe: Die Spalte trägt `tabular-nums` und richtet sich nur aus, wenn
 * jede Zahl gleich viele Stellen hat. Und `toFixed` schreibt einen Punkt, auch
 * wenn die Oberfläche deutsch ist — vorher stand dort „25.80 %" neben
 * deutschen Beschriftungen.
 */
const ZIFFERN = { minimumFractionDigits: 2, maximumFractionDigits: 2 }

const anzeige = computed(() => {
  if (zahl.value === null) return '—'
  return `${n(zahl.value, ZIFFERN)} %`
})

/** Der eingetragene Wert als Text — für den Hinweis, wenn die Quelle ihn verdeckt. */
const manuellAlsText = computed(() => {
  const roh = manualValue(props.item, props.field)
  if (roh === null) return ''
  if (typeof roh === 'boolean') return roh ? t('table.yes') : t('table.no')
  return `${n(roh, ZIFFERN)} %`
})

const merkmalTitel = computed(() => {
  if (zustand.value === 'manual') return t('overrides.markManual')
  if (zustand.value === 'shadowed') return t('overrides.markShadowed', { value: manuellAlsText.value })
  return ''
})

/*
 * Thesaurierend hat drei Zustände, und „ausschüttend" ist eine Aussage — nicht
 * die Abwesenheit einer. Statt eines Auswahlfelds in jeder Zeile (das die
 * Tabelle mit Rahmen überzöge) reicht ein Klick weiter: ja → nein → nicht
 * gesetzt. Der Titel nennt jeweils den nächsten Zustand, sonst wäre es Raten.
 */
/**
 * Der nächste Zustand: ja → nein → nicht gesetzt → ja.
 *
 * Ausgeschrieben statt als Nachschlagetabelle: Die Tabelle lief über
 * `String(wert)` und brauchte ein `?? true` für den Fall eines unbekannten
 * Schlüssels — das verschluckte aber das **gültige** Ergebnis `null`. Aus
 * „nein" wurde damit wieder „ja", und „nicht gesetzt" war nie erreichbar.
 */
function naechster(wert: boolean | null): boolean | null {
  if (wert === true) return false
  if (wert === false) return null
  return true
}

/*
 * Gezykelt wird der **eingetragene** Wert, nicht der wirksame.
 *
 * Der Unterschied fällt nur auf, solange die Quelle den eigenen Wert verdeckt —
 * dann aber hart: Bei Quelle „ja" und Eingabe „nein" zeigt die Zelle „ja", der
 * nächste Zustand wäre daraus „nein", und genau das steht schon drin. Jeder
 * Klick schriebe denselben Wert.
 *
 * Dass die Zelle sich dabei nicht rührt, ist kein Fehler, sondern die
 * Vorrang-Regel: Die Quelle gewinnt. Was sich ändert, steht im Titel des
 * Merkmals daneben — deshalb trägt es den eingetragenen Wert ausgeschrieben.
 */
const naechsterZustand = computed(() => naechster(props.item.manual_accumulating))

const umschaltTitel = computed(() =>
  t('overrides.cycleTo', {
    value:
      naechsterZustand.value === null
        ? t('overrides.notSet')
        : naechsterZustand.value
          ? t('table.yes')
          : t('table.no'),
  }),
)

function onZahl(value: number | null): void {
  emit('commit', { [props.field]: value } as Partial<InstrumentOverrides>)
}

function onUmschalten(): void {
  emit('commit', { accumulating: naechsterZustand.value })
}
</script>

<template>
  <span class="metric" :class="`metric--${zustand ?? 'plain'}`">
    <template v-if="field === 'accumulating'">
      <button
        class="metric__toggle"
        type="button"
        :disabled="busy"
        :title="umschaltTitel"
        @click.stop="onUmschalten"
      >
        <span v-if="item.accumulating !== null" class="badge thes" :class="{ acc: item.accumulating }">
          {{ item.accumulating ? t('table.yes') : t('table.no') }}
        </span>
        <span v-else class="metric__empty">—</span>
      </button>
    </template>

    <UxInlineNumber
      v-else
      :value="zahl"
      :display="anzeige"
      :precision="2"
      :min="0"
      :max="maximum"
      :empty-value="null"
      :disabled="busy"
      :edit-label="t('overrides.edit')"
      :clear-label="t('overrides.clear')"
      @commit="onZahl"
    />

    <!--
      Das Merkmal ist bewusst klein und trägt seinen Sinn im Titel: Farbe allein
      trüge die Aussage nicht, und ein „?"-Hinweis in jeder Zelle wären bei
      fünfzehn Zellen fünfzehn Fragezeichen.
    -->
    <span v-if="zustand" class="metric__mark" :title="merkmalTitel" aria-hidden="true">•</span>
    <span v-if="zustand" class="visually-hidden">{{ merkmalTitel }}</span>
  </span>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.metric {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  justify-content: flex-end;

  &__toggle {
    border: none;
    background: none;
    padding: 0;
    cursor: pointer;
    font: inherit;
    color: inherit;
  }

  &__empty { color: $color-muted; }

  &__mark {
    font-size: 0.7rem;
    line-height: 1;
  }

  // Der Wert kommt von Hand — das Merkmal trägt die Akzentfarbe.
  &--manual &__mark { color: $color-accent; }

  // Es gibt einen Wert, aber die Quelle überstimmt ihn — leiser.
  &--shadowed &__mark { color: $color-muted; }
}
</style>
