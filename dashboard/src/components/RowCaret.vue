<script setup lang="ts">
/**
 * Der Pfeil, der eine aufklappbare Zeile als solche kenntlich macht.
 *
 * Er steht **zusätzlich** zur Kennung (ux-standards, „Die Kennung öffnet die
 * Zeile"): Geklickt wird der Name, aber ohne sichtbares Merkmal sieht man der
 * Zeile nicht an, dass sie aufgeht.
 *
 * **Warum ein SVG und kein `⌄`.** Vorher stand hier das Zeichen U+2304. Es
 * sitzt tief in seinem Em-Quadrat, klebte damit am unteren Rand der Zeile —
 * und beim Drehen um 180° kippt es nach oben. Eine feste optische Korrektur
 * kann deshalb immer nur einen der beiden Zustände treffen. Die Form hier
 * liegt symmetrisch um die Kastenmitte (x 6…18, y 9…15, Mitte also 12/12), die
 * Drehung verschiebt sie folglich nicht.
 *
 * Damit folgt er auch der Symbolregel: Strichsymbol, `currentColor`,
 * Strichstärke 2, runde Enden, als Inline-SVG eingebunden.
 *
 * Er liegt hier und nicht im Fundament, weil ihn bisher nur diese App braucht.
 * Gebaut ist er dafür: keine Stores, kein Katalog, kein Router — ein Prop, ein
 * Symbol. Braucht eine zweite App eine aufklappbare Zeile, zieht er um.
 */
defineProps<{
  /** Ist die zugehörige Zeile gerade aufgeklappt? */
  open: boolean
}>()
</script>

<template>
  <svg
    class="caret"
    :class="{ 'caret--open': open }"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!--
      `aria-hidden` am Element darüber: Den Zustand sagt bereits `aria-expanded`
      am Knopf, in den dieser Pfeil eingebettet ist. Ein vorgelesener Pfeil wäre
      dieselbe Auskunft ein zweites Mal, nur stummer.

      Der Kommentar steht **innerhalb** des `svg` und nicht davor: Ein
      Kommentar vor dem Wurzelelement macht die Komponente mehrwurzelig, und
      damit greift weder das Durchreichen von Attributen noch findet ein Test
      die Wurzel.
    -->
    <path d="M6 9 L12 15 L18 9" />
  </svg>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

/*
 * `vertical-align: middle` statt der Grundlinie: Ein Inline-Block sitzt sonst
 * mit seiner Unterkante auf der Grundlinie und hängt damit unter der Kennung
 * daneben. Die Größe ist bewusst etwas kleiner als der Text — der Pfeil weist
 * hin, er ruft nicht.
 */
.caret {
  display: inline-block;
  width: 0.95rem;
  height: 0.95rem;
  vertical-align: middle;
  color: $color-accent;
  transition: transform 0.12s ease;

  &--open { transform: rotate(180deg); }
}
</style>
