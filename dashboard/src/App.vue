<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  NConfigProvider,
  NDialogProvider,
  NMessageProvider,
  NNotificationProvider,
  darkTheme,
  dateDeDE,
  dateEnUS,
  deDE,
  enUS,
} from 'naive-ui'
import { buildNaiveOverrides, THEMES } from '@mikemitterer/ux-foundation'

import AppDashboard from './components/AppDashboard.vue'
import { useNaiveOverrides } from './composables/useNaiveOverrides'
import { useTheme } from './composables/useTheme'

/**
 * Der Rahmen: Theme-Brücke, Locale und die Provider von Naive UI.
 *
 * Der Inhalt liegt bewusst eine Ebene tiefer in `AppDashboard.vue` —
 * `useNotifier()` braucht einen `NNotificationProvider` **über** sich, und der
 * wird hier erst im Template aufgespannt.
 */

const { locale } = useI18n()
const { current: currentTheme } = useTheme()

/*
 * Die Brücke zu Naive UI: Aus den Token dieser Seite werden dessen Overrides
 * gebaut. Die Richtung ist verbindlich — die Token sind die Quelle, Naive der
 * Verbraucher. Dass zur Laufzeit per `getComputedStyle` gelesen wird, ist
 * erzwungen: Naive rechnet Hover- und Pressed-Zustände selbst aus der
 * Grundfarbe und kann ein `var(--accent)` nicht auflösen.
 */
const naiveOverrides = useNaiveOverrides(buildNaiveOverrides)
const isDark = computed(() => THEMES[currentTheme.value].isDark)

/*
 * Naive mitziehen: Seine eingebauten Beschriftungen — „Bestätigen",
 * „Abbrechen" in jeder Rückfrage — kämen sonst englisch heraus, während die
 * Oberfläche deutsch ist.
 */
const naiveLocale = computed(() => (locale.value === 'de' ? deDE : enUS))
const naiveDateLocale = computed(() => (locale.value === 'de' ? dateDeDE : dateEnUS))
</script>

<template>
  <!--
    Ein Rahmen um alles: `inline-theme-disabled`, weil Naive seine Variablen
    sonst an jedes Element schreibt und der Theme-Wechsel sichtbar langsam wird.
    Die Provider stehen hier, damit Toasts und Rückfragen überall erreichbar
    sind.

    `:max="3"` an den Meldungen ist Absicht: Fallen mehrere Quellen gleichzeitig
    aus, soll daraus keine Stapel-Lawine werden, die den halben Bildschirm deckt.

    Der Versatz nach unten ist keine Kosmetik. Naive setzt die Toasts 12 Pixel
    unter den oberen Rand — also über die Kopfzeile. Da Fehler stehen bleiben,
    bis sie weggeklickt werden, lag die rechte Gruppe der Leiste samt
    „Aktualisieren" dauerhaft darunter. 4 rem ist die Kopfzeile (3.5 rem) plus
    den Abstand, den Naive ohnehin einhält.

    Dass darunter nichts weiter kollidiert, ist der zweite Teil derselben
    Änderung: „Alle aktualisieren" ist aus der Leiste über der Tabelle in die
    Kopfzeile gezogen (siehe `AppHeader.vue`) — dorthin gehört es ohnehin, und
    das obere rechte Eck des Inhalts ist damit frei.
  -->
  <NConfigProvider
    :locale="naiveLocale"
    :date-locale="naiveDateLocale"
    :theme="isDark ? darkTheme : null"
    :theme-overrides="naiveOverrides"
    inline-theme-disabled
  >
    <NMessageProvider>
      <NDialogProvider>
        <NNotificationProvider :max="3" :container-style="{ top: '4rem' }">
          <AppDashboard />
        </NNotificationProvider>
      </NDialogProvider>
    </NMessageProvider>
  </NConfigProvider>
</template>
