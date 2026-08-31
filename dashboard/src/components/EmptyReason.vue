<script setup lang="ts">
import { NTooltip } from 'naive-ui'

/**
 * Ein Strich, der auf Nachfrage sagt, warum er da steht.
 *
 * **Der Strich ist der Auslöser, nicht ein Zeichen daneben.** Ein zusätzliches
 * Fragezeichen wäre an einer einzelnen Zelle inkonsistent: Die Tabelle ist
 * voller Striche — TER, Vola, Thesaurierung —, und keiner davon trägt eins.
 * Eines nur dort zu setzen, wo zufällig ein Text existiert, sieht willkürlich
 * aus.
 *
 * **Und es bleibt erreichbar, nicht nur schwebend.** Der Auslöser ist ein
 * `button`: Damit greift der Hinweis bei Maus, bei Tastaturfokus und bei
 * Berührung. Ein reines `title`-Attribut kann das erste, nicht die beiden
 * anderen.
 *
 * Sichtbar unterscheidet ihn der gepunktete Unterstrich von einem Strich, der
 * nichts zu sagen hat — dieselbe Konvention wie bei einer Abkürzung.
 */
defineProps<{
  /** Bereits übersetzter Grund. */
  reason: string
}>()
</script>

<template>
  <NTooltip trigger="hover" :style="{ maxWidth: '20rem' }">
    <template #trigger>
      <!--
        Der Klick endet **hier**, nicht beim Aufrufer. Ein `@click.stop` an der
        Komponente liefe ins Leere: Wurzelelement ist das Tooltip, und dort
        landen durchgereichte Attribute — nicht am Knopf. Der Strich erklärt
        nur; er darf die Zeilenaktion darunter nie auslösen.
      -->
      <button
        type="button"
        class="empty-reason"
        :aria-label="reason"
        @click.stop.prevent
      >
        —
      </button>
    </template>
    {{ reason }}
  </NTooltip>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.empty-reason {
  padding: 0;
  border: 0;
  background: none;
  font: inherit;
  color: $color-muted;
  cursor: help;

  // Der einzige sichtbare Unterschied zu einem stummen Strich.
  text-decoration: underline dotted;
  text-underline-offset: 0.25em;

  &:focus-visible {
    outline: 2px solid $color-accent;
    outline-offset: 2px;
  }
}
</style>
