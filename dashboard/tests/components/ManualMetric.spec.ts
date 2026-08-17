import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import ManualMetric from '../../src/components/ManualMetric.vue'
import { i18n } from '../../src/i18n'
import type { InstrumentSummary, OverrideField } from '../../src/types'
import { makeInstrument } from '../fixtures/instrument'

/**
 * Die Zelle für eine von Hand nachtragbare Kennzahl (T-09).
 *
 * Zwei Regeln entscheiden hier alles Weitere:
 *
 * 1. **Gepflegt wird nur, was fehlt.** Liefert die Quelle einen Wert, ist die
 *    Zelle nicht bedienbar — vorher war jede editierbar, und eine Eingabe auf
 *    einem Papier mit Provider-Wert verschwand wortlos hinter diesem.
 * 2. **Gezykelt und geleert wird der eingetragene Wert**, nicht der wirksame.
 */

/** Hängt die Zelle ein. */
function mountCell(item: InstrumentSummary, field: OverrideField = 'accumulating') {
  return mount(ManualMetric, { global: { plugins: [i18n] }, props: { item, field } })
}

/** Der Wert, den ein Klick auf den Umschalter schreiben würde. */
async function geklickterWert(item: InstrumentSummary): Promise<boolean | null | undefined> {
  const wrapper = mountCell(item)
  await wrapper.get('.metric__toggle').trigger('click')
  const commits = wrapper.emitted('commit')
  return (commits?.[0]?.[0] as { accumulating?: boolean | null })?.accumulating
}

describe('ManualMetric — was die Quelle liefert, wird nicht gepflegt', () => {
  it('lässt eine Zelle mit Provider-Wert unbedienbar', () => {
    const wrapper = mountCell(makeInstrument({ accumulating: true }))

    expect(wrapper.find('.metric__toggle').exists()).toBe(false)
    expect(wrapper.find('.metric__static').exists()).toBe(true)
  })

  it('lässt auch eine verdeckte Eingabe unbedienbar', () => {
    /*
     * Der Fall, der die Regel ausgelöst hat: Quelle „ja", eigene Eingabe
     * „nein". Angezeigt wurde „ja", ein Klick schrieb ins Leere, und das
     * Merkmal daneben war die einzige Spur. Jetzt steht dort nur noch der Wert
     * der Quelle — das Merkmal nennt die Eingabe weiterhin.
     */
    const wrapper = mountCell(
      makeInstrument({
        accumulating: true,
        manual_accumulating: false,
        shadowed_fields: ['accumulating'],
      }),
    )

    expect(wrapper.find('.metric__toggle').exists()).toBe(false)
    expect(wrapper.find('.metric__mark').exists()).toBe(true)
  })

  it('sperrt auch die Zahlenspalten, sobald die Quelle etwas hat', () => {
    const wrapper = mountCell(makeInstrument({ ter: 0.2 }), 'ter')

    expect(wrapper.findComponent({ name: 'UxInlineNumber' }).exists()).toBe(false)
    // Dezimaltrenner je Sprache — geprüft wird der Wert, nicht das Format.
    expect(wrapper.get('.metric__static').text()).toMatch(/0[.,]20/)
  })

  it('lässt eine leere Zahlenspalte bearbeiten', () => {
    const wrapper = mountCell(makeInstrument({ ter: null }), 'ter')

    expect(wrapper.findComponent({ name: 'UxInlineNumber' }).exists()).toBe(true)
  })

  it('zeigt den Wert der Quelle unverändert an, nicht den eingetragenen', () => {
    const wrapper = mountCell(
      makeInstrument({
        accumulating: true,
        manual_accumulating: false,
        shadowed_fields: ['accumulating'],
      }),
    )

    expect(wrapper.get('.metric__static').text()).toBe(i18n.global.t('table.yes'))
  })
})

describe('ManualMetric — Umschalter', () => {
  it('zykelt ohne Eingabe von „nicht gesetzt" auf „ja"', async () => {
    const item = makeInstrument({ accumulating: null, manual_accumulating: null })

    expect(await geklickterWert(item)).toBe(true)
  })

  it('zykelt die eigene Eingabe von „ja" auf „nein"', async () => {
    const item = makeInstrument({
      accumulating: true,
      manual_accumulating: true,
      manual_fields: ['accumulating'],
    })

    expect(await geklickterWert(item)).toBe(false)
  })

  it('erreicht von „nein" aus wieder „nicht gesetzt"', async () => {
    /*
     * Der dritte Zustand war nie erreichbar: Die Nachschlagetabelle lief über
     * `String(wert)` und brauchte ein `?? true` für unbekannte Schlüssel — das
     * verschluckte aber das gültige Ergebnis `null`. Aus „nein" wurde damit
     * wieder „ja".
     */
    const item = makeInstrument({
      accumulating: false,
      manual_accumulating: false,
      manual_fields: ['accumulating'],
    })

    expect(await geklickterWert(item)).toBeNull()
  })
})
