import { afterEach, describe, expect, it, vi } from 'vitest'

// consola stummschalten — Fehlerpfad-Tests würden sonst rote Zeilen ausgeben.
import { sourceProvides, useOverrides } from '../../src/composables/useOverrides'
import { i18n } from '../../src/i18n'
import { OVERRIDE_FIELDS } from '../../src/types'
import { makeInstrument } from '../fixtures/instrument'

afterEach(() => vi.unstubAllGlobals())

/*
 * Nacharbeit Sichtprüfung, I4: Die Vorrang-Regel steht an einer Stelle,
 * `sourceProvides()`; dieser Test deckt die Regel selbst ab, unabhängig von
 * den Komponenten, die sie aufrufen.
 */
describe('sourceProvides', () => {
  it('ist wahr, wenn die Quelle einen Wert liefert', () => {
    expect(sourceProvides(makeInstrument({ ter: 0.2 }), 'ter')).toBe(true)
  })

  it('ist falsch, wenn kein Wert gesetzt ist', () => {
    expect(sourceProvides(makeInstrument({ ter: null }), 'ter')).toBe(false)
  })

  it('ist falsch, wenn der Wert von Hand kommt (Zustand `manual`)', () => {
    // Die Quelle hat nichts geliefert — der wirksame Wert ist der eingetragene.
    const item = makeInstrument({ ter: 0.2, manual_ter: 0.2, manual_fields: ['ter'] })

    expect(sourceProvides(item, 'ter')).toBe(false)
  })

  it('ist wahr, wenn die Quelle einen eingetragenen Wert verdeckt (Zustand `shadowed`)', () => {
    const item = makeInstrument({ ter: 0.3, manual_ter: 0.2, shadowed_fields: ['ter'] })

    expect(sourceProvides(item, 'ter')).toBe(true)
  })
})

/*
 * Der Payload muss **immer** alle acht Felder tragen: Das Backend behandelt ein
 * fehlendes Feld als „löschen". Aufgezählt wurden sie hier aus acht getippten
 * `manual_*`, obwohl `manualValue(item, field)` daneben generisch ist — eine
 * neunte Kennzahl wäre stillschweigend bei jedem Schreiben gelöscht worden.
 */
describe('useOverrides.save', () => {
  /** Fängt den PUT ab und gibt den gesendeten Rumpf zurück. */
  function captureBody(): { body: () => Record<string, unknown> } {
    const fetchMock = vi.fn().mockResolvedValue(new Response('{}', { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)
    return {
      body: () => JSON.parse(fetchMock.mock.calls[0][1].body as string),
    }
  }

  it('nennt bei einer Ablehnung den übersetzten Grund des Backends, nicht nur „fehlgeschlagen“', async () => {
    // Vor T-141 blieb nur die Kategorie stehen; der Grund ging verloren.
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ code: 'quote_unavailable', params: { identifier: 'EUNL.DE' } }),
      { status: 422 },
    )))
    const overrides = useOverrides()

    await overrides.save(makeInstrument(), { ter: 0.19 })

    expect(overrides.error.value).toContain(i18n.global.t('errors.overrides'))
    expect(overrides.error.value).toContain(
      i18n.global.t('errors.reason.quote_unavailable', { identifier: 'EUNL.DE' }),
    )
  })

  it('schickt alle acht Kennzahlen, nicht nur die geänderte', async () => {
    const captured = captureBody()
    const item = makeInstrument({
      manual_ter: 0.25,
      manual_volatility: 30,
      manual_accumulating: true,
      manual_provider: 'iShares',
      manual_replication: 'physisch',
      manual_fund_size: 1200,
      manual_fund_domicile: 'IE',
      manual_fund_currency: 'EUR',
    })

    await useOverrides().save(item, { ter: 0.19 })

    const sent = captured.body()
    expect(Object.keys(sent).sort()).toEqual([...OVERRIDE_FIELDS].sort())
    // Der Patch gewinnt, die übrigen sieben kommen unverändert mit.
    expect(sent.ter).toBe(0.19)
    expect(sent.provider).toBe('iShares')
    expect(sent.fund_currency).toBe('EUR')
    expect(sent.accumulating).toBe(true)
  })

  it('schickt auch die leeren Felder als null — sie sollen gelöscht bleiben', async () => {
    const captured = captureBody()

    await useOverrides().save(makeInstrument(), { provider: 'Vanguard' })

    const sent = captured.body()
    expect(Object.keys(sent).sort()).toEqual([...OVERRIDE_FIELDS].sort())
    expect(sent.ter).toBeNull()
  })
})
