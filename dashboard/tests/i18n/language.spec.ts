import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

// Modul wird pro Test frisch importiert — createI18n läuft auf Modul-Ebene
// und liest navigator/localStorage bereits beim Import.
beforeEach(() => {
  vi.resetModules()
  window.localStorage.clear()
})
afterEach(() => vi.unstubAllGlobals())

/**
 * Stellt die Sprachliste des Browsers.
 *
 * `userAgent` gehört dazu, auch wenn ihn keine Prüfung hier liest: Der
 * Import zieht über das Fundament auch Naive UI herein, und dessen
 * Umgebungs-Erkennung greift beim Laden auf `navigator.userAgent` zu. Ein
 * Stub ohne ihn lässt schon den Import scheitern.
 */
function pretendBrowser(...sprachen: string[]): void {
  vi.stubGlobal('navigator', {
    languages: sprachen,
    language: sprachen[0] ?? '',
    userAgent: 'vitest',
  })
}

describe('i18n', () => {
  it('nutzt die gespeicherte Sprache aus dem localStorage', async () => {
    window.localStorage.setItem('stockinfo-lang', 'en')
    pretendBrowser('de-AT')
    const { startLocale } = await import('../../src/i18n')
    expect(startLocale()).toBe('en')
  })

  it('erkennt Deutsch aus der Browser-Sprache', async () => {
    pretendBrowser('de-AT')
    const { startLocale } = await import('../../src/i18n')
    expect(startLocale()).toBe('de')
  })

  it('nimmt die erste Sprache mit Katalog, nicht die erste überhaupt', async () => {
    // Die frühere Fassung las nur `navigator.language`: Wer Französisch zuerst
    // und Deutsch danach führt, bekam Englisch, obwohl es den Katalog gibt.
    pretendBrowser('fr-FR', 'de-CH', 'en-US')
    const { startLocale } = await import('../../src/i18n')
    expect(startLocale()).toBe('de')
  })

  it('fällt bei anderen Browser-Sprachen auf Englisch zurück', async () => {
    pretendBrowser('fr-FR')
    const { startLocale } = await import('../../src/i18n')
    expect(startLocale()).toBe('en')
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
