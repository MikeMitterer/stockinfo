import { describe, expect, it } from 'vitest'

import { ApiError } from '../../src/api/client'
import { describeFailure, reasonOf } from '../../src/api/reason'
import { i18n, LOCALES } from '../../src/i18n'

/**
 * Nur so viel vom Katalog, wie diese Tests anfassen.
 *
 * `Record<string, any>` stand hier zweimal und machte jeden Tippfehler im
 * Pfad zu einem Laufzeitfehler statt zu einem Typfehler — `any` schaltet
 * genau die Pruefung ab, für die der Compiler da ist.
 */
type LocaleMessages = {
  errors: { reason: Record<string, string> }
  drilldown: Record<string, string>
}

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
    const uncertain: Record<string, RegExp> = { de: /\boffen\b/i, en: /\bwhether\b/i }

    for (const locale of LOCALES) {
      i18n.global.locale.value = locale
      const reason = reasonOf(
        new ApiError(502, JSON.stringify({ code: 'quote_unavailable', params: { identifier: 'yfinance' } })),
      )
      expect(reason, `${locale}: die Existenz wird als offen dargestellt`).toMatch(
        uncertain[locale],
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
      const messages = i18n.global.getLocaleMessage(locale) as LocaleMessages
      return Object.keys(messages.errors.reason).sort()
    }

    expect(keys('de')).toEqual(keys('en'))
  })

  it('haben fuer jede Kennung einen echten Satz', () => {
    for (const locale of LOCALES) {
      const messages = i18n.global.getLocaleMessage(locale) as LocaleMessages
      for (const [code, sentence] of Object.entries(messages.errors.reason)) {
        expect(String(sentence).trim().length, `${locale}.${code}`).toBeGreaterThan(15)
        expect(String(sentence), `${locale}.${code}`).not.toBe(code)
      }
    }
  })
})

/**
 * Was `input_failure()` in `app/exchanges.py` zurueckgeben kann.
 *
 * **Von Hand aufgezaehlt, und das ist der Punkt.** Diese Liste aus einem
 * Katalog zu ziehen hiesse, den Katalog gegen sich selbst zu pruefen — sie
 * waere immer vollstaendig und faende nie etwas. Sie ist eine unabhaengige
 * Behauptung ueber das Backend; laeuft sie ihm davon, wird dieser Test rot,
 * und genau dafuer ist er da.
 *
 * Der Befund aus T-58 entstand, weil ich drei davon im Migrationskatalog
 * gezaehlt habe statt vier an ihrer Quelle. `ambiguous_exchange_suffix` kann
 * nur beim Eintippen entstehen und fehlt dort zu Recht.
 */
const INTAKE_REASON_CODES = [
  'symbol_without_exchange_suffix',
  'unknown_exchange_suffix',
  'non_canonical_ticker',
  'ambiguous_exchange_suffix',
] as const

describe('Identitaetskennungen des Aufnahmewegs', () => {
  it.each(LOCALES)('hat in %s fuer jede Kennung einen Satz statt der rohen Kennung', (locale) => {
    i18n.global.locale.value = locale

    for (const code of INTAKE_REASON_CODES) {
      const reason = reasonOf(new ApiError(400, JSON.stringify({ code })))

      expect(reason, `${locale}.${code}`).not.toBeNull()
      // Der Rueckfall nennt die Kennung im Satz — genau das soll hier nicht
      // mehr passieren.
      expect(String(reason), `${locale}.${code}`).not.toContain(code)
      expect(String(reason).trim().length, `${locale}.${code}`).toBeGreaterThan(25)
    }
  })

  /*
   * **Die Gegenprobe zur Gegenprobe.** Ohne sie koennte man den Rueckfall
   * loeschen und der Test oben bliebe gruen — waehrend eine Kennung aus einem
   * neueren Backend danach wortlos verschwaende. Vorwaertskompatibilitaet ist
   * nicht dasselbe wie Vollstaendigkeit.
   */
  it('laesst eine wirklich unbekannte Kennung im uebersetzten Rueckfall', () => {
    const reason = reasonOf(new ApiError(400, JSON.stringify({ code: 'aus_einem_neueren_backend' })))

    expect(reason).toContain('aus_einem_neueren_backend')
    expect(reason).not.toBe('aus_einem_neueren_backend')
  })
})

describe('Erklaertexte im Aufklappbereich', () => {
  it('nennen keine eingebaute Quelle beim Namen', () => {
    // **Derselbe Waechter wie fuer `errors.reason`, eine Textgruppe weiter.**
    //
    // Codex' Finding 2 aus T-36 galt den Fehlermeldungen; die Erklaerungen im
    // Drilldown standen nicht darin und nannten weiter viermal justETF. Im
    // CSV-Profil heisst die Kennzahlen-Quelle `metadata-file` — und die
    // Oberflaeche zeigt das eine Zeile darueber sogar korrekt an.
    const forbidden = [/justetf/i, /yfinance/i, /openfigi/i, /\byahoo\b/i]

    for (const locale of LOCALES) {
      const messages = i18n.global.getLocaleMessage(locale) as LocaleMessages
      for (const [key, text] of Object.entries(messages.drilldown)) {
        for (const name of forbidden) {
          expect(String(text), `${locale}.drilldown.${key}`).not.toMatch(name)
        }
      }
    }
  })

  it('haben fuer jeden Fall einen echten Satz', () => {
    for (const locale of LOCALES) {
      const messages = i18n.global.getLocaleMessage(locale) as LocaleMessages
      for (const key of ['explain', 'notEtf', 'noIsin', 'nothingProvided']) {
        expect(String(messages.drilldown[key]).trim().length, `${locale}.${key}`)
          .toBeGreaterThan(25)
      }
    }
  })
})
