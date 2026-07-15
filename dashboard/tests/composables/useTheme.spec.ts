import { afterEach, describe, expect, it } from 'vitest'

import { useTheme } from '../../src/composables/useTheme'

afterEach(() => {
  window.localStorage.clear()
  delete document.documentElement.dataset.theme
})

describe('useTheme', () => {
  it('setTheme setzt data-theme und persistiert', () => {
    const { current, setTheme } = useTheme()
    setTheme('ocean')
    expect(current.value).toBe('ocean')
    expect(document.documentElement.dataset.theme).toBe('ocean')
    expect(window.localStorage.getItem('stockinfo-theme')).toBe('ocean')
  })

  it('init stellt ein gespeichertes Theme wieder her', () => {
    window.localStorage.setItem('stockinfo-theme', 'forest')
    const { current, init } = useTheme()
    init()
    expect(current.value).toBe('forest')
    expect(document.documentElement.dataset.theme).toBe('forest')
  })

  it('init fällt bei ungültigem gespeicherten Wert auf den Default zurück', () => {
    window.localStorage.setItem('stockinfo-theme', 'kaputt')
    const { current, init } = useTheme()
    init()
    expect(current.value).toBe('classic')
  })
})
