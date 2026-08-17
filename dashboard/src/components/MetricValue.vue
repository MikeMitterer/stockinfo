<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { manualValue, overrideState } from '../composables/useOverrides'
import type { InstrumentSummary, OverrideField } from '../types'

/**
 * Eine Kennzahl, rein anzeigend — die lesende Hälfte von T-09.
 *
 * Zeigt den **wirksamen** Wert und, falls von Hand nachgetragen oder von der
 * Quelle verdeckt, das Merkmal daneben. Gepflegt wird nicht mehr hier,
 * sondern in der aufklappbaren Zeile (Task 8) — deshalb ohne Umschalter, ohne
 * Eingabefeld, ohne `commit`-Event.
 *
 * Anzeige und Merkmal sind aus `ManualMetric.vue` übernommen — dort bleiben
 * sie bestehen, weil die Kartenliste (`InstrumentCard.vue`) dort noch mobil
 * pflegt.
 */
const props = defineProps<{
  item: InstrumentSummary
  field: OverrideField
}>()

const { t, n } = useI18n()

const state = computed(() => overrideState(props.item, props.field))

/** Der wirksame Wert — das, was die Zelle zeigt. */
const value = computed<number | boolean | null>(() => {
  if (props.field === 'ter') return props.item.ter
  if (props.field === 'volatility') return props.item.volatility
  return props.item.accumulating
})

const numericValue = computed(() => (typeof value.value === 'number' ? value.value : null))

/**
 * Kommt der gezeigte Wert wirklich aus der Quelle — nicht aus der Eingabe?
 *
 * `item.accumulating`/`item.ter`/`item.volatility` sind bereits die
 * **wirksamen** Werte (das Backend löst die Vorrang-Regel auf), deshalb
 * reicht „nicht null" allein nicht: Im Zustand `manual` ist der wirksame Wert
 * der eingetragene, und der Hinweis „Kommt aus der Quelle" wäre dann falsch.
 */
const fromSource = computed(() => state.value !== 'manual' && value.value !== null)

/*
 * Immer zwei Nachkommastellen, und über `n()` statt `toFixed`.
 *
 * Zwei Gründe: Die Spalte trägt `tabular-nums` und richtet sich nur aus, wenn
 * jede Zahl gleich viele Stellen hat. Und `toFixed` schreibt einen Punkt, auch
 * wenn die Oberfläche deutsch ist — vorher stand dort „25.80 %" neben
 * deutschen Beschriftungen.
 */
const DIGITS = { minimumFractionDigits: 2, maximumFractionDigits: 2 }

const display = computed(() => {
  if (numericValue.value === null) return '—'
  return `${n(numericValue.value, DIGITS)} %`
})

/** Der eingetragene Wert als Text — für den Hinweis, wenn die Quelle ihn verdeckt. */
const manualAsText = computed(() => {
  const raw = manualValue(props.item, props.field)
  if (raw === null) return ''
  if (typeof raw === 'boolean') return raw ? t('table.yes') : t('table.no')
  // `field` ist hier immer eines der drei alten Zahlenfelder (T-15 erweitert
  // `manualValue` generisch auf acht Felder, diese Komponente kennt nur drei).
  if (typeof raw === 'number') return `${n(raw, DIGITS)} %`
  return ''
})

const markTitle = computed(() => {
  if (state.value === 'manual') return t('overrides.markManual')
  if (state.value === 'shadowed') return t('overrides.markShadowed', { value: manualAsText.value })
  return ''
})
</script>

<template>
  <span
    class="metric"
    :class="`metric--${state ?? 'plain'}`"
    :title="fromSource ? t('overrides.fromSource') : undefined"
  >
    <span class="metric__static" :class="{ 'metric__static--fixed': field === 'accumulating' }">
      <template v-if="field === 'accumulating'">
        <span v-if="item.accumulating !== null" class="badge thes" :class="{ acc: item.accumulating }">
          {{ item.accumulating ? t('table.yes') : t('table.no') }}
        </span>
        <span v-else class="metric__empty">—</span>
      </template>
      <template v-else>{{ display }}</template>
    </span>

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
      v-if="state"
      class="metric__mark"
      :title="markTitle"
      aria-hidden="true"
      >•</span
    >
    <span v-if="state" class="visually-hidden">{{ markTitle }}</span>
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

  /* In der Thes.-Spalte eine feste Breite — sonst wandert die Spalte, je
     nachdem wie breit „Ja"/„Nein"/„—" ausfallen. In den Zahlenspalten
     unnötig: Die sind rechtsbündig. */
  &__static--fixed {
    display: inline-flex;
    justify-content: center;
    min-width: 2.75rem;
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
