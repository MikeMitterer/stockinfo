import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { DEFAULT_DARK_THEME, DEFAULT_LIGHT_THEME } from '@mikemitterer/ux-foundation'

import { useTheme } from '../../src/composables/useTheme'

/**
 * Das Theme nach der Umstellung auf das Fundament (T-12).
 *
 * Die App hatte acht eigene Paletten; vier ihrer Namen (`earth`, `night`,
 * `sunset`, `neon`) gibt es dort nicht. Der letzte Test hält fest, was mit
 * einer solchen gespeicherten Wahl passiert — ohne die Prüfung stünde ein
 * ungültiges `data-theme` am Wurzelelement und die App wäre farblos.
 */
afterEach(() => {
  window.localStorage.clear()
  delete document.documentElement.dataset.theme
  vi.unstubAllGlobals()
})

/** Stellt `matchMedia` so, als sei das System hell oder dunkel eingestellt. */
function pretendSystem(dark: boolean): void {
  vi.stubGlobal(
    'matchMedia',
    (query: string) => ({ matches: dark && query.includes('dark') }) as MediaQueryList,
  )
}

beforeEach(() => {
  pretendSystem(true)
})

describe('useTheme', () => {
  it('setTheme setzt data-theme und persistiert', () => {
    const { current, setTheme } = useTheme()

    setTheme('ocean')

    expect(current.value).toBe('ocean')
    expect(document.documentElement.dataset.theme).toBe('ocean')
    expect(window.localStorage.getItem('stockinfo-theme')).toBe('ocean')
  })

  it('setzt color-scheme mit — Naive UI und Formularelemente hängen daran', () => {
    const { setTheme } = useTheme()

    setTheme('paper')

    expect(document.documentElement.style.colorScheme).toBe('light')
  })

  it('init stellt ein gespeichertes Theme wieder her', () => {
    window.localStorage.setItem('stockinfo-theme', 'forest')
    const { current, init } = useTheme()

    init()

    expect(current.value).toBe('forest')
    expect(document.documentElement.dataset.theme).toBe('forest')
  })

  it('init fällt bei ungültigem gespeicherten Wert auf die Systemvorgabe zurück', () => {
    window.localStorage.setItem('stockinfo-theme', 'kaputt')
    const { current, init } = useTheme()

    init()

    expect(current.value).toBe(DEFAULT_DARK_THEME)
  })

  it('vergisst die vier Paletten, die es nur in dieser App gab', () => {
    // `earth`, `night`, `sunset` und `neon` sind mit der Umstellung entfallen —
    // wer eines davon gewählt hatte, landet auf der Vorgabe statt im Nichts.
    for (const alt of ['earth', 'night', 'sunset', 'neon']) {
      window.localStorage.setItem('stockinfo-theme', alt)
      const { current, init } = useTheme()

      init()

      expect(current.value, alt).toBe(DEFAULT_DARK_THEME)
    }
  })

  it('folgt ohne gespeicherte Wahl der Systemeinstellung', () => {
    pretendSystem(false)
    const { current, init } = useTheme()

    init()

    expect(current.value).toBe(DEFAULT_LIGHT_THEME)
  })
})
