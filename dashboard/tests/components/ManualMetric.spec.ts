import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import ManualMetric from '../../src/components/ManualMetric.vue'
import { i18n } from '../../src/i18n'
import type { InstrumentSummary } from '../../src/types'
import { makeInstrument } from '../fixtures/instrument'

/**
 * Der Umschalter für „thesaurierend" — drei Zustände per Klick.
 *
 * Der Anlass ist ein Fehler: Gezykelt wurde der **wirksame** Wert. Solange die
 * Quelle nichts liefert, ist das derselbe wie der eingetragene und fällt nicht
 * auf. Verdeckt die Quelle den eigenen Wert, läuft es in eine Sackgasse — jeder
 * Klick schreibt, was schon drinsteht.
 */

/** Hängt die Zelle für „thesaurierend" ein und liefert den Umschalter dazu. */
function mountToggle(item: InstrumentSummary) {
  const wrapper = mount(ManualMetric, {
    global: { plugins: [i18n] },
    props: { item, field: 'accumulating' },
  })
  return { wrapper, toggle: wrapper.get('.metric__toggle') }
}

/** Der Wert, den ein Klick auf den Umschalter schreiben würde. */
async function geklickterWert(item: InstrumentSummary): Promise<boolean | null | undefined> {
  const { wrapper, toggle } = mountToggle(item)
  await toggle.trigger('click')
  const commits = wrapper.emitted('commit')
  return (commits?.[0]?.[0] as { accumulating?: boolean | null })?.accumulating
}

describe('ManualMetric — Umschalter', () => {
  it('zykelt ohne Eingabe von „nicht gesetzt" auf „ja"', async () => {
    const item = makeInstrument({ accumulating: null, manual_accumulating: null })

    expect(await geklickterWert(item)).toBe(true)
  })

  it('zykelt die eigene Eingabe weiter, wenn die Quelle nichts liefert', async () => {
    const item = makeInstrument({
      accumulating: true,
      manual_accumulating: true,
      manual_fields: ['accumulating'],
    })

    expect(await geklickterWert(item)).toBe(false)
  })

  it('zykelt die Eingabe und nicht den Wert der Quelle, wenn diese ihn verdeckt', async () => {
    /*
     * Der eigentliche Fehler: Quelle „ja", eingetragen „nein". Angezeigt wird
     * „ja", der nächste Zustand daraus wäre „nein" — und das steht schon drin.
     * Vorher schrieb jeder Klick `false`, „nicht gesetzt" und „ja" waren nicht
     * erreichbar.
     */
    const item = makeInstrument({
      accumulating: true,
      manual_accumulating: false,
      shadowed_fields: ['accumulating'],
    })

    expect(await geklickterWert(item)).toBeNull()
  })

  it('kommt aus dem verdeckten Zustand wieder bis „ja" herum', async () => {
    // Der Rundlauf schließt sich: nein → nicht gesetzt → ja.
    const item = makeInstrument({
      accumulating: true,
      manual_accumulating: null,
      shadowed_fields: ['accumulating'],
    })

    expect(await geklickterWert(item)).toBe(true)
  })

  it('zeigt weiter den Wert der Quelle, nicht den eingetragenen', async () => {
    // Die Vorrang-Regel bleibt unangetastet — geändert hat sich nur, was ein
    // Klick schreibt.
    const item = makeInstrument({
      accumulating: true,
      manual_accumulating: false,
      shadowed_fields: ['accumulating'],
    })
    const { toggle } = mountToggle(item)

    expect(toggle.text()).toBe(i18n.global.t('table.yes'))
  })
})
