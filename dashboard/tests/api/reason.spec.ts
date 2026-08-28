import { describe, expect, it } from 'vitest'

import { ApiError } from '../../src/api/client'
import { describeFailure, reasonOf } from '../../src/api/reason'
import { i18n, LOCALES } from '../../src/i18n'

/**
 * Der Übersetzer zwischen `ErrorDetail` und dem, was ein Mensch liest.
 *
 * Bis T-36 gab es ihn ohne Test — und der UI-Lauf hat gezeigt, wie teuer das
 * ist: Der Benutzer las „Hinzufügen fehlgeschlagen" und fand den eigentlichen
 * Grund nur in der Browserkonsole.
 */
describe('reasonOf', () => {
  it('übersetzt eine bekannte Kennung und setzt ihre Werte ein', () => {
    const reason = reasonOf(
      new ApiError(404, JSON.stringify({ code: 'instrument_not_found', params: { identifier: 'XX0000000000' } })),
    )

    expect(reason).toContain('XX0000000000')
    // Der Satz kommt aus dem Katalog, nicht vom Server.
    expect(reason).not.toBe('instrument_not_found')
  })

  it('nennt keine eingebaute Quelle beim Namen', () => {
    // Welche Quellen antworten, entscheidet `sources.yaml`. Mit einem
    // CSV-Profil waere „ueber OpenFIGI und Yahoo" schlicht falsch — und genau
    // so stand es hier, bis Codex es aufgegriffen hat.
    for (const locale of LOCALES) {
      i18n.global.locale.value = locale
      const reason = reasonOf(
        new ApiError(404, JSON.stringify({ code: 'instrument_not_found', params: { identifier: 'IE00B4L5Y983' } })),
      )
      expect(reason?.toLowerCase()).not.toContain('openfigi')
      expect(reason?.toLowerCase()).not.toContain('yahoo')
      expect(reason?.toLowerCase()).not.toContain('justetf')
    }
    i18n.global.locale.value = 'de'
  })

  it('behauptet bei quote_unavailable nicht, dass es das Papier gibt', () => {
    // `Unavailable` heisst: **niemand hat nachgesehen.** Ob es das Papier
    // gibt, ist damit offen — und der Unterschied zu `instrument_not_found`
    // ist der ganze Sinn der beiden Kennungen.
    //
    // Geprueft wird die **Aussage**, nicht eine Zeichenkette: „Whether the
    // security exists is therefore open" enthaelt „the security exists" und
    // behauptet trotzdem das Gegenteil. Ein Teilstring-Verbot haette hier
    // falsch angeschlagen — der erste Anlauf dieses Tests tat genau das.
    // Verlangt wird deshalb der Unsicherheitsmarker in jeder Sprache.
    const ungewiss: Record<string, RegExp> = { de: /\boffen\b/i, en: /\bwhether\b/i }

    for (const locale of LOCALES) {
      i18n.global.locale.value = locale
      const reason = reasonOf(
        new ApiError(502, JSON.stringify({ code: 'quote_unavailable', params: { identifier: 'yfinance' } })),
      )
      expect(reason, `${locale}: die Existenz wird als offen dargestellt`).toMatch(
        ungewiss[locale],
      )
    }
    i18n.global.locale.value = 'de'
  })

  it('faellt bei einer unbekannten Kennung auf einen uebersetzten Satz zurueck', () => {
    // Die rohe Kennung ist ein Bezeichner fuer Maschinen und in keiner Sprache
    // ein Satz. Sie zu nennen ist trotzdem richtig — nur eben in einem Satz.
    const reason = reasonOf(new ApiError(418, JSON.stringify({ code: 'aus_der_zukunft', params: {} })))

    expect(reason).not.toBe('aus_der_zukunft')
    expect(reason).toContain('aus_der_zukunft')
  })

  it('reicht einen alten Fliesstext-Koerper durch, statt ihn zu verschlucken', () => {
    // Es gibt sie noch: Die 502-Faelle nennen im `detail` die ausgefallenen
    // Quellen. Unuebersetzt anzuzeigen ist besser als gar nicht.
    const reason = reasonOf(new ApiError(502, JSON.stringify({ detail: 'openfigi; yfinance' })))

    expect(reason).toBe('openfigi; yfinance')
  })

  it('nimmt auch einen Koerper, der gar kein JSON ist', () => {
    expect(reasonOf(new ApiError(500, 'Internal Server Error'))).toBe('Internal Server Error')
  })

  it('macht aus einem leeren Koerper keinen leeren Grund', () => {
    // Sonst haenge ein einsames Trennzeichen an der Meldung.
    expect(reasonOf(new ApiError(500, '   '))).toBeNull()
    expect(reasonOf(new ApiError(500, JSON.stringify({ detail: '' })))).toBeNull()
  })

  it('liefert fuer alles, was kein ApiError ist, keinen Grund', () => {
    expect(reasonOf(new TypeError('kaputt'))).toBeNull()
    expect(reasonOf('irgendwas')).toBeNull()
    expect(reasonOf(undefined)).toBeNull()
  })
})

describe('describeFailure', () => {
  it('haengt den Grund an die Kategorie', () => {
    const text = describeFailure(
      'Hinzufügen fehlgeschlagen',
      new ApiError(404, JSON.stringify({ code: 'instrument_not_found', params: { identifier: 'XX0000000000' } })),
    )

    expect(text).toMatch(/^Hinzufügen fehlgeschlagen — /)
    expect(text).toContain('XX0000000000')
  })

  it('laesst die Kategorie allein stehen, wenn es keinen Grund gibt', () => {
    expect(describeFailure('Löschen fehlgeschlagen', new TypeError('kaputt'))).toBe(
      'Löschen fehlgeschlagen',
    )
  })
})

describe('Sprachkataloge', () => {
  it('kennen dieselben Kennungen in DE und EN', () => {
    // Ein Grund, den es nur auf Deutsch gibt, ist in der englischen
    // Oberflaeche eine rohe Kennung — genau das, was `ErrorDetail` verhindern
    // soll.
    const keys = (locale: string): string[] => {
      const messages = i18n.global.getLocaleMessage(locale) as Record<string, any>
      return Object.keys(messages.errors.reason).sort()
    }

    expect(keys('de')).toEqual(keys('en'))
  })

  it('haben fuer jede Kennung einen echten Satz', () => {
    for (const locale of LOCALES) {
      const messages = i18n.global.getLocaleMessage(locale) as Record<string, any>
      for (const [code, sentence] of Object.entries(messages.errors.reason)) {
        expect(String(sentence).trim().length, `${locale}.${code}`).toBeGreaterThan(15)
        expect(String(sentence), `${locale}.${code}`).not.toBe(code)
      }
    }
  })
})
