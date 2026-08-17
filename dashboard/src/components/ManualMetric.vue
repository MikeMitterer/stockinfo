<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { UxInlineNumber } from '@mmit/ux-foundation'

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
 * Liefert die **Quelle** für dieses Feld etwas? Dann wird hier nichts gepflegt.
 *
 * Nachgetragen wird, was fehlt — nicht, was schon dasteht. Vorher war jede
 * Zelle editierbar: Wer bei einem Papier mit Provider-Wert etwas eintrug, sah
 * unverändert den alten Wert und daneben ein neues Merkmal. Das liest sich wie
 * ein Fehler, obwohl die Vorrang-Regel genau das vorsieht.
 *
 * Erkannt am Zustand, nicht an einem zweiten Feld: Steht der angezeigte Wert
 * `manual`, kommt er aus der Eingabe und die Quelle hat nichts. Sonst ist der
 * angezeigte Wert der der Quelle — und ist er gesetzt, ist hier zu.
 */
const quelleHatWert = computed(() => zustand.value !== 'manual' && wert.value !== null)

/**
 * Der **eingetragene** Wert als Zahl — das, was bearbeitet und geleert wird.
 *
 * Getrennt vom wirksamen Wert, und zwar aus demselben Grund wie beim
 * Umschalter: Angezeigt wird, was gilt; bearbeitet wird, was man selbst
 * hinterlegt hat. Vorher bekam das Feld den wirksamen Wert — mit zwei Folgen:
 * Das Löschkreuz erschien auch dort, wo es nichts zu löschen gab (ein Klick
 * darauf schrieb `null` auf ein leeres Feld, sichtbar passierte nichts), und
 * die Bearbeitung startete auf dem Wert der Quelle, den man mit Enter
 * versehentlich als eigenen übernahm.
 */
const manuelleZahl = computed(() => {
  const roh = manualValue(props.item, props.field)
  return typeof roh === 'number' ? roh : null
})

/**
 * Obergrenze je Kennzahl — dieselben Werte prüft das Backend noch einmal.
 *
 * Zwei Stellen sind hier unvermeidbar: Das Feld soll beim Tippen begrenzen,
 * und der Endpoint darf sich nicht auf die Oberfläche verlassen. Die Zahlen
 * sind bewusst großzügig — sie fangen Tippfehler ab, nicht Meinungen.
 */
const maximum = computed(() => (props.field === 'ter' ? 5 : 500))

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
  // `field` ist hier immer eines der drei alten Zahlenfelder (T-15 erweitert
  // `manualValue` generisch auf acht Felder, diese Komponente kennt nur drei).
  if (typeof roh === 'number') return `${n(roh, ZIFFERN)} %`
  return ''
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
  <span
    class="metric"
    :class="`metric--${zustand ?? 'plain'}`"
    :title="quelleHatWert ? t('overrides.fromSource') : undefined"
  >
    <!--
      Liefert die Quelle etwas, steht hier nur der Wert — kein Knopf, kein Feld.
      Nachgetragen wird, was fehlt; was schon dasteht, gehört der Quelle. Der
      Titel an der Zelle sagt das, sonst wirkt die tote Zelle wie ein Fehler.
    -->
    <span
      v-if="quelleHatWert"
      class="metric__static"
      :class="{ 'metric__static--fest': field === 'accumulating' }"
    >
      <span
        v-if="field === 'accumulating'"
        class="badge thes"
        :class="{ acc: item.accumulating }"
      >{{ item.accumulating ? t('table.yes') : t('table.no') }}</span>
      <template v-else>{{ anzeige }}</template>
    </span>

    <template v-else-if="field === 'accumulating'">
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
      :value="manuelleZahl"
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

      Es liegt **außerhalb** des Flusses, rechts neben dem Wert im Innenabstand
      der Zelle. Als Flex-Kind kostete es Breite, und zwar nur in markierten
      Zeilen — der Wert rutschte dort nach links. Platz dafür zu reservieren
      behob das zwar zeilenweise, verschob aber die ganze Spalte gegen ihren
      Kopf: Gemessen endete „TER" bei 826 und die Zahl darunter bei 810, das
      Prozentzeichen stand also unter dem T.

      Ohne Breite stimmt beides: Zeilen untereinander und Spalte gegen Kopf.
    -->
    <span
      v-if="zustand"
      class="metric__mark"
      :title="merkmalTitel"
      aria-hidden="true"
      >•</span
    >
    <span v-if="zustand" class="visually-hidden">{{ merkmalTitel }}</span>
  </span>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.metric {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  justify-content: flex-end;

  /*
   * Eine Breite für alle drei Zustände.
   *
   * „—", „Ja" und „Nein" sind 13.6, 28.7 und 40.5 Pixel breit; mittig gesetzt
   * steht damit jede Zeile auf einer anderen Kante, und die Spalte wirkt
   * verrutscht. Das ist dieselbe Regel wie beim Statusetikett: gleiche Breite
   * über alle Zeilen, sonst wandert die Spalte. 2.75 rem fasst das längste
   * Wort mit etwas Luft.
   */
  /* In der Thes.-Spalte dieselbe feste Breite wie der Umschalter — sonst
     wandert die Spalte, je nachdem ob eine Zeile aus der Quelle kommt oder von
     Hand. In den Zahlenspalten unnötig: Die sind rechtsbündig. */
  &__static--fest {
    display: inline-flex;
    justify-content: center;
    min-width: 2.75rem;
  }

  &__toggle {
    display: inline-flex;
    justify-content: center;
    min-width: 2.75rem;
    border: none;
    background: none;
    padding: 0;
    cursor: pointer;
    font: inherit;
    color: inherit;
  }

  &__empty { color: $color-muted; }

  /*
   * Hängt rechts neben dem Wert, im Innenabstand der Zelle — ohne Breite.
   * Nur so bleiben Zeilen mit und ohne Merkmal auf derselben Kante, und die
   * Spalte bleibt bündig mit ihrem Kopf.
   */
  &__mark {
    position: absolute;
    top: 50%;
    left: 100%;
    margin-left: 0.15rem;
    font-size: 0.7rem;
    line-height: 1;
    transform: translateY(-50%);
  }

  // Der Wert kommt von Hand — das Merkmal trägt die Akzentfarbe.
  &--manual &__mark { color: $color-accent; }

  // Es gibt einen Wert, aber die Quelle überstimmt ihn — leiser.
  &--shadowed &__mark { color: $color-muted; }
}
</style>
