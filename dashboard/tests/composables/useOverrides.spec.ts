import { describe, expect, it } from 'vitest'

import { sourceProvides } from '../../src/composables/useOverrides'
import { makeInstrument } from '../fixtures/instrument'

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
