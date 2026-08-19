import { afterEach, describe, expect, it, vi } from 'vitest'

// consola stummschalten — Fehlerpfad-Tests würden sonst rote Zeilen ausgeben.
vi.mock('consola', () => ({
  consola: { error: vi.fn(), warn: vi.fn(), info: vi.fn() },
}))

import { sourceProvides, useOverrides } from '../../src/composables/useOverrides'
import { OVERRIDE_FIELDS } from '../../src/types'
import { makeInstrument } from '../fixtures/instrument'

afterEach(() => vi.unstubAllGlobals())

/*
 * Nacharbeit Sichtprüfung, I4: Die Vorrang-Regel stand bislang dreimal im
 * Frontend — je einmal anders formuliert in `MetricValue.vue`,
 * `MetricEditor.vue` und `InstrumentDrilldown.vue`. `sourceProvides()` ist die
 * eine Stelle, die alle drei jetzt verwenden; dieser Test deckt die Regel
 * selbst ab, unabhängig von den Komponenten, die sie aufrufen.
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
