import { onMounted, onUnmounted, ref, watch, type Ref } from 'vue'

import type { SettingsTab, TabKey } from '../types'

const TABS: TabKey[] = ['assets', 'exchanges', 'analysis', 'fx', 'settings']
const DEFAULT_TAB: TabKey = 'assets'

export const SETTINGS_TABS: SettingsTab[] = ['appearance', 'language', 'links', 'environment']
export const DEFAULT_SETTINGS_TAB: SettingsTab = 'appearance'

interface HashRoute {
  tab: TabKey
  settingsTab: SettingsTab
}

/** Zerlegt die Hash-Route in Tab und (bei settings) Reiter — z.B. "#/settings?tab=language". */
function parseHash(): HashRoute {
  const raw = window.location.hash.replace(/^#\/?/, '')
  const [tabPart, queryPart = ''] = raw.split('?')
  const tab = (TABS as string[]).includes(tabPart) ? (tabPart as TabKey) : DEFAULT_TAB
  const rawSettingsTab = new URLSearchParams(queryPart).get('tab') ?? ''
  const settingsTab = (SETTINGS_TABS as string[]).includes(rawSettingsTab)
    ? (rawSettingsTab as SettingsTab)
    : DEFAULT_SETTINGS_TAB
  return { tab, settingsTab }
}

/** Baut die Hash-Route: bei settings mit ?tab=<reiter>, sonst schlicht #/<tab>. */
function toHash(tab: TabKey, settingsTab: SettingsTab): string {
  return tab === 'settings' ? `#/settings?tab=${settingsTab}` : `#/${tab}`
}

/**
 * Adresse eines Tabs — für Verweise irgendwo in der App.
 *
 * Die URL-Struktur gehört dieser Datei; ein zusammengesetztes `#/settings?tab=…`
 * an anderer Stelle wäre eine zweite Quelle, die beim ersten Umbau falsch wird.
 */
export function tabHref(tab: TabKey, settingsTab: SettingsTab = DEFAULT_SETTINGS_TAB): string {
  return toHash(tab, settingsTab)
}

/**
 * Aktiver Tab + Settings-Reiter, synchron mit einer deep-linkbaren Hash-Route.
 * Einzige Stelle, die die URL-Struktur besitzt.
 */
export function useHashTab(): { tab: Ref<TabKey>; settingsTab: Ref<SettingsTab> } {
  const initial = parseHash()
  const tab = ref<TabKey>(initial.tab)
  const settingsTab = ref<SettingsTab>(initial.settingsTab)

  function onHashChange(): void {
    const route = parseHash()
    tab.value = route.tab
    settingsTab.value = route.settingsTab
  }

  watch([tab, settingsTab], ([t, s]) => {
    const next = toHash(t, s)
    if (window.location.hash !== next) {
      window.location.hash = next
    }
  })

  onMounted(() => {
    const next = toHash(tab.value, settingsTab.value)
    if (window.location.hash !== next) {
      window.location.hash = next
    }
    window.addEventListener('hashchange', onHashChange)
  })

  onUnmounted(() => window.removeEventListener('hashchange', onHashChange))

  return { tab, settingsTab }
}
