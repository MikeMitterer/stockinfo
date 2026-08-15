import { onMounted, onUnmounted, ref, type Ref } from 'vue'

/**
 * Grenze `md` aus den UX-Standards: darunter eine Spalte, Kartenliste statt
 * Tabelle. 767.98 statt 767, damit auch gebrochene Breiten (Zoom, DPR) sauber
 * kippen — ab genau 768px gilt das volle Layout.
 */
export const COMPACT_QUERY = '(max-width: 767.98px)'

/**
 * True, solange der Viewport schmaler als `md` ist. Einzige Stelle, die den
 * Umschaltpunkt kennt — die Darstellung folgt der Logik, nicht umgekehrt.
 */
export function useIsCompact(): Ref<boolean> {
  const query = window.matchMedia(COMPACT_QUERY)
  const compact = ref(query.matches)

  function onChange(event: MediaQueryListEvent): void {
    compact.value = event.matches
  }

  onMounted(() => query.addEventListener('change', onChange))
  onUnmounted(() => query.removeEventListener('change', onChange))

  return compact
}
