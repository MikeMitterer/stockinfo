import { ref, watch, type Ref } from 'vue'
import type { GlobalThemeOverrides } from 'naive-ui'

import { useTheme } from './useTheme'

/**
 * Naive-Overrides, die dem Theme folgen.
 *
 * Es gibt zwei Sätze davon — einen für den Inhalt, einen für die Leisten —,
 * und beide brauchen dieselbe Behandlung: einmal beim Aufbau lesen, danach bei
 * jedem Theme-Wechsel erneut. Stünde das zweimal da, wäre eines davon
 * irgendwann anders.
 *
 * @param build Die Brücke aus dem Fundament, die aus den Token die Overrides baut.
 */
export function useNaiveOverrides(build: () => GlobalThemeOverrides): Ref<GlobalThemeOverrides> {
  const { current } = useTheme()

  /*
   * Beim ersten Bild **synchron**: `main.ts` setzt `data-theme`, bevor die App
   * eingehängt wird, die Werte stehen also schon. Wartete man hier auf
   * `requestAnimationFrame`, blitzte für ein Bild Naives eigenes Grün auf,
   * bevor der Akzent der Palette greift.
   */
  const overrides = ref<GlobalThemeOverrides>(build())

  watch(current, () => {
    // Beim Wechsel dagegen erst im nächsten Bild: `data-theme` muss am Element
    // stehen, bevor `getComputedStyle` die neuen Werte liefert.
    requestAnimationFrame(() => {
      overrides.value = build()
    })
  })

  return overrides
}
