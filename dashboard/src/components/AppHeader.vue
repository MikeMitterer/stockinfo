<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { NButton, NConfigProvider } from 'naive-ui'
import {
  UxNavItem,
  UxTopbar,
  buildBarNaiveOverrides,
  type NavIconName,
} from '@mmit/ux-foundation'

import { useNaiveOverrides } from '../composables/useNaiveOverrides'
import type { TabKey } from '../types'

/**
 * Die Kopfzeile dieser App.
 *
 * Rahmen, Plakette und Wortmarke liefert das Fundament (`UxTopbar`), den
 * einzelnen Menüpunkt `UxNavItem`. Hier bleibt, was diese App ausmacht: welche
 * Bereiche es gibt, welches Zeichen in der Plakette steht und wie ein Klick
 * zum Tab wird.
 *
 * **Kein Hamburger mehr** (T-11g): Unterhalb `md` fällt die Beschriftung weg,
 * nicht der Punkt. Fünf Symbole passen auf jedes Telefon, und die Navigation
 * ist damit einen Griff entfernt statt zwei. Die Einstellungen stehen dabei
 * links bei den anderen Punkten — sie sind eine Seite, also ein Ort, kein
 * Werkzeug.
 */
const props = defineProps<{ active: TabKey; refreshing: boolean }>()

const emit = defineEmits<{
  (event: 'navigate', tab: TabKey): void
  (event: 'refresh'): void
}>()

const { t } = useI18n()

/*
 * Ein zweiter Satz Naive-Farben, nur für die rechte Gruppe.
 *
 * Die Leiste holt ihre Flächen und Textfarben aus eigenen Token — genau
 * deshalb darf ein Theme sie umkehren. Naive bekommt global aber die Farben
 * des **Inhalts**: In `sepia` (heller Inhalt, dunkle Leisten) stand der Knopf
 * mit 1,38:1 auf der Leiste, also unsichtbar.
 */
const barOverrides = useNaiveOverrides(buildBarNaiveOverrides)

const aktionLabel = computed(() =>
  props.refreshing ? t('toolbar.refreshing') : t('toolbar.refreshAll'),
)

/*
 * Die Symbole stehen im Fundament, nicht hier — sie sind über alle Apps
 * dieselben. `assets` heißt dort `instruments`: benannt nach der Rolle, nicht
 * nach dem Wort, das diese App dafür verwendet.
 */
const tabs = computed<{ key: TabKey; label: string; icon: NavIconName }[]>(() => [
  { key: 'assets', label: t('nav.assets'), icon: 'instruments' },
  { key: 'exchanges', label: t('nav.exchanges'), icon: 'exchanges' },
  { key: 'fx', label: t('nav.fx'), icon: 'fx' },
  { key: 'analysis', label: t('nav.analysis'), icon: 'analysis' },
  { key: 'settings', label: t('nav.settings'), icon: 'settings' },
])
</script>

<template>
  <UxTopbar
    :brand-lead="t('app.brandLead')"
    :brand-accent="t('app.brandAccent')"
    href="#/assets"
    :aria-label="t('nav.home')"
  >
    <template #badge>
      <!--
        Drei aufsteigende Balken — **dasselbe Motiv** wie in
        `public/stockinfo-icon.svg`, dort nur mit der Kachel darunter; die
        trägt hier das Fundament. Weichen Plakette und FavIcon voneinander ab,
        erkennt man die App im Reiter nicht wieder.

        Nur Formen, kein `text`: Ein SVG in einer geladenen Datei ist ein
        eigenes Dokument, sieht die Schriften der Seite nicht und erbt keine
        Textfarbe. Genau daran hing hier die falsche Schrift samt fest
        eingetragener Füllung.
      -->
      <svg
        viewBox="0 0 24 24"
        fill="rgb(var(--brand-contrast))"
        width="16"
        height="16"
      >
        <rect x="4" y="14" width="3.5" height="6" rx="1.2" />
        <rect x="10.25" y="9.5" width="3.5" height="10.5" rx="1.2" />
        <rect x="16.5" y="5" width="3.5" height="15" rx="1.2" />
      </svg>
    </template>

    <template #nav>
      <UxNavItem
        v-for="tab in tabs"
        :key="tab.key"
        :icon="tab.icon"
        :label="tab.label"
        :active="tab.key === active"
        :href="`#/${tab.key}`"
        @select="emit('navigate', tab.key)"
      />
    </template>

    <!--
      Rechts steht nur, was **nicht** Navigation ist: die eine Handlung, die
      überall gilt. Sie stand vorher in der Leiste über der Tabelle, also im
      oberen rechten Eck des Inhalts — genau dort, wo Meldungen erscheinen.
      Ein Fehler-Toast verdeckte damit den Knopf, mit dem man ihn behebt.
    -->
    <template #actions>
      <NConfigProvider :theme-overrides="barOverrides" inline-theme-disabled>
        <!--
          Rahmenlos wie ein Menüpunkt: Ein umrandeter Kasten rechts ruft lauter
          als die Punkte links, obwohl er nicht wichtiger ist. `quaternary` ist
          dabei eine Spielart derselben Sorte Knopf — kein eigenes CSS.
        -->
        <NButton
          quaternary
          size="small"
          :disabled="refreshing"
          :loading="refreshing"
          :aria-label="aktionLabel"
          @click="emit('refresh')"
        >
          <!--
            Unterhalb `md` fällt die **Beschriftung** weg, nicht die Handlung —
            dieselbe Reihenfolge wie bei den Menüpunkten links. Das ↻ steht
            deshalb im Markup und nicht im Katalog: Es ist kein übersetzbarer
            Text, und im Katalog ließe es sich nicht getrennt ausblenden.
            `aria-label` trägt den Namen weiter, wenn der Text verschwindet.
          -->
          <span v-if="!refreshing" aria-hidden="true">↻</span>
          <span class="topbar-action__label">{{ aktionLabel }}</span>
        </NButton>
      </NConfigProvider>
    </template>
  </UxTopbar>
</template>

<style scoped lang="scss">
/*
 * Wird es eng, verschwindet die Beschriftung — das Symbol bleibt. Dieselbe
 * Stufe wie bei den Menüpunkten links, damit die Kopfzeile nicht halb
 * beschriftet dasteht.
 */
.topbar-action__label {
  display: none;

  // Abstand zum Zeichen erst dort, wo die Beschriftung auch steht.
  @include up(md) {
    display: inline;
    margin-left: 0.35rem;
  }
}
</style>
