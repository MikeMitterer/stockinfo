<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { UxInfoHint } from '@mmit/ux-foundation'

import { tabHref } from '../composables/useHashTab'
import type { SettingsTab, TabKey } from '../types'

/**
 * Fragezeichen mit Kurzerklärung — die App-Hälfte davon.
 *
 * Aussehen und Verhalten liefert `UxInfoHint` aus dem Fundament; hier bleibt,
 * was das Paket nicht wissen kann: wie die Verweise heißen (Katalog) und wohin
 * sie führen (die Hash-Route dieser App).
 *
 * Die Aufrufstellen sprechen in Tabs, nicht in Adressen — welche Schreibweise
 * eine Route hat, gehört `useHashTab` und sonst niemandem.
 */
const props = defineProps<{
  /** Bereits übersetzter Erklärungstext. */
  text: string
  /** Tab, der den Begriff vertieft — etwa die Börsentabelle. */
  moreTab?: TabKey
  /**
   * Reiter der Einstellungen, in dem die zugehörige Stellschraube sitzt.
   *
   * Erklärung und Stellschraube gehören zusammen: Wer liest, woran das Alter
   * der Kurse hängt, will als Nächstes das Intervall sehen — und sucht sonst
   * selbst, in welchem Reiter es steckt.
   */
  settingsTab?: SettingsTab
}>()

const { t } = useI18n()

const moreHref = computed(() => (props.moreTab ? tabHref(props.moreTab) : undefined))

const settingHref = computed(() =>
  props.settingsTab ? tabHref('settings', props.settingsTab) : undefined,
)
</script>

<template>
  <UxInfoHint
    :text="text"
    :more-href="moreHref"
    :more-label="moreTab ? t('hints.more') : undefined"
    :setting-href="settingHref"
    :setting-label="settingsTab ? t('hints.openSetting') : undefined"
  />
</template>
