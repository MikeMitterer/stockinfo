import { onMounted, onUnmounted, ref, watch, type Ref } from 'vue'

import type { TabKey } from '../types'

const TABS: TabKey[] = ['assets', 'exchanges', 'environment', 'links', 'themes']
const DEFAULT_TAB: TabKey = 'assets'

/** Liest den aktiven Tab aus der URL-Hash-Route (#/assets …). */
function fromHash(): TabKey {
  const key = window.location.hash.replace(/^#\/?/, '') as TabKey
  return TABS.includes(key) ? key : DEFAULT_TAB
}

/** Aktiver Tab, synchron mit einer deep-linkbaren Hash-Route (#/<tab>). */
export function useHashTab(): Ref<TabKey> {
  const active = ref<TabKey>(fromHash())

  function onHashChange(): void {
    active.value = fromHash()
  }

  watch(active, (tab) => {
    if (fromHash() !== tab) {
      window.location.hash = `#/${tab}`
    }
  })

  onMounted(() => {
    if (!window.location.hash) {
      window.location.hash = `#/${active.value}`
    }
    window.addEventListener('hashchange', onHashChange)
  })

  onUnmounted(() => window.removeEventListener('hashchange', onHashChange))

  return active
}
