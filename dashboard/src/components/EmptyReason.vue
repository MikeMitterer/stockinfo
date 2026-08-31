<script setup lang="ts">
import { NTooltip } from 'naive-ui'

/**
 * Eine Erklärung für einen Strich, der an der Stelle eines Werts steht.
 *
 * **Die Hülle bestimmt die Auskunft, nicht das Verhalten.** Was der Benutzer
 * anfasst, gibt der Aufrufer als Inhalt hinein — sinnvollerweise dieselbe
 * Schaltfläche, die dort stünde, wenn es einen Wert gäbe. Ein Klick tut damit
 * an dieser Stelle genau das, was er hier immer tut: In der Symbolspalte
 * öffnet er den Detailbereich, wie es das Symbol selbst täte.
 *
 * Die Alternative wäre ein Fragezeichen daneben gewesen, und sie war schlecht:
 * Die Tabelle ist voller Striche — TER, Vola, Thesaurierung —, und keiner
 * davon trägt eins.
 *
 * Sichtbar unterscheidet der gepunktete Unterstrich diesen Strich von einem,
 * der nichts zu sagen hat — dieselbe Konvention wie bei einer Abkürzung. Weil
 * der Inhalt üblicherweise eine Schaltfläche ist, greift der Hinweis auch bei
 * Tastaturfokus und Berührung, nicht nur bei der Maus.
 */
defineProps<{
  /** Bereits übersetzter Grund. */
  reason: string
}>()
</script>

<template>
  <NTooltip trigger="hover" :style="{ maxWidth: '20rem' }">
    <template #trigger>
      <span class="empty-reason" :aria-label="reason">
        <slot>—</slot>
      </span>
    </template>
    {{ reason }}
  </NTooltip>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.empty-reason {
  color: $color-muted;
  text-decoration: underline dotted;
  text-underline-offset: 0.25em;
  cursor: help;

  // Der Inhalt bringt sein eigenes Verhalten mit; die Hülle fügt keins hinzu.
  :deep(button) {
    padding: 0;
    border: 0;
    background: none;
    font: inherit;
    color: inherit;
    cursor: inherit;
  }
}
</style>
