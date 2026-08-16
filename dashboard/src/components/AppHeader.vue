<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { UxNavItem, UxTopbar, type NavIconName } from '@mikemitterer/ux-foundation'

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
defineProps<{ active: TabKey }>()

const emit = defineEmits<{
  (event: 'navigate', tab: TabKey): void
}>()

const { t } = useI18n()

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
  </UxTopbar>
</template>
