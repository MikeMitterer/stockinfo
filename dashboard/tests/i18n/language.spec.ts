import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

// Modul wird pro Test frisch importiert — createI18n läuft auf Modul-Ebene
// und liest navigator/localStorage bereits beim Import.
beforeEach(() => {
  vi.resetModules()
  window.localStorage.clear()
})
afterEach(() => vi.unstubAllGlobals())

describe('i18n', () => {
  it('nutzt die gespeicherte Sprache aus dem localStorage', async () => {
    window.localStorage.setItem('stockinfo-lang', 'en')
    vi.stubGlobal('navigator', { language: 'de-AT' })
    const { detectLocale } = await import('../../src/i18n')
    expect(detectLocale()).toBe('en')
  })

  it('erkennt Deutsch aus der Browser-Sprache', async () => {
    vi.stubGlobal('navigator', { language: 'de-AT' })
    const { detectLocale } = await import('../../src/i18n')
    expect(detectLocale()).toBe('de')
  })

  it('fällt bei anderen Browser-Sprachen auf Englisch zurück', async () => {
    vi.stubGlobal('navigator', { language: 'fr-FR' })
    const { detectLocale } = await import('../../src/i18n')
    expect(detectLocale()).toBe('en')
  })

  it('setLanguage persistiert, stellt um und setzt <html lang>', async () => {
    const { i18n, setLanguage } = await import('../../src/i18n')
    setLanguage('en')
    expect(window.localStorage.getItem('stockinfo-lang')).toBe('en')
    expect(i18n.global.locale.value).toBe('en')
    expect(document.documentElement.lang).toBe('en')
    expect(i18n.global.t('status.degraded')).toBe('Checking…')

    setLanguage('de')
    expect(i18n.global.t('status.degraded')).toBe('Prüfe…')
  })

  it('translate() liefert Texte außerhalb von Komponenten', async () => {
    const { setLanguage, translate } = await import('../../src/i18n')
    setLanguage('de')
    expect(translate('errors.refresh')).toBe('Refresh fehlgeschlagen')
  })
})
