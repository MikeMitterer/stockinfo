import { mount } from '@vue/test-utils'
import { NSelect } from 'naive-ui'
import { describe, expect, it } from 'vitest'

import MetricEditor from '../../src/components/MetricEditor.vue'
import { i18n } from '../../src/i18n'
import type { InstrumentSummary, OverrideField } from '../../src/types'
import { makeInstrument } from '../fixtures/instrument'

function mountEditor(item: InstrumentSummary, field: OverrideField = 'ter') {
  return mount(MetricEditor, { global: { plugins: [i18n] }, props: { item, field } })
}

describe('MetricEditor', () => {
  it('lässt ein Feld pflegen, das die Quelle nicht liefert', () => {
    const wrapper = mountEditor(makeInstrument({ ter: null }))

    expect(wrapper.findComponent({ name: 'UxInlineNumber' }).exists()).toBe(true)
  })

  it('sperrt das Feld, sobald die Quelle etwas hat', () => {
    const wrapper = mountEditor(makeInstrument({ ter: 0.2 }))

    expect(wrapper.findComponent({ name: 'UxInlineNumber' }).exists()).toBe(false)
  })

  it('lässt einen verdeckten Eintrag entfernen', async () => {
    /*
     * Ohne diese Aktion wäre das Feature eine Falle: Wer während eines
     * Quellen-Ausfalls acht Felder nachträgt, käme nach dessen Ende an keinen
     * davon mehr heran.
     */
    const wrapper = mountEditor(
      makeInstrument({ ter: 0.2, manual_ter: 0.1, shadowed_fields: ['ter'] }),
    )

    await wrapper.get('.metric-editor__remove').trigger('click')

    expect(wrapper.emitted('commit')?.[0]?.[0]).toEqual({ ter: null })
  })

  it('bietet nichts zum Entfernen, wo es keine Eingabe gibt', () => {
    const wrapper = mountEditor(makeInstrument({ ter: 0.2 }))

    expect(wrapper.find('.metric-editor__remove').exists()).toBe(false)
  })

  /*
   * Der Umschalter (Thesaurierung) — bislang ungetestet in dieser Datei.
   * Genau der gesperrte Zustand mit verdecktem Eintrag hat in diesem Projekt
   * bereits mehrfach Fehler verursacht: Bedienelement weg, Entfernen-Knopf da.
   */
  it('lässt die Thesaurierung umschalten, wenn die Quelle nichts liefert', async () => {
    const wrapper = mountEditor(
      makeInstrument({ accumulating: null, manual_accumulating: null }),
      'accumulating',
    )

    await wrapper.get('.metric-editor__toggle').trigger('click')

    expect(wrapper.emitted('commit')?.[0]?.[0]).toEqual({ accumulating: true })
  })

  it('sperrt den Umschalter bei einem verdeckten Eintrag, bietet aber das Entfernen an', () => {
    const wrapper = mountEditor(
      makeInstrument({ accumulating: true, manual_accumulating: false, shadowed_fields: ['accumulating'] }),
      'accumulating',
    )

    expect(wrapper.find('.metric-editor__toggle').exists()).toBe(false)
    expect(wrapper.find('.metric-editor__remove').exists()).toBe(true)
  })

  /*
   * Die vier Textfelder (provider, replication, fund_domicile, fund_currency)
   * sind Auswahlfelder mit freier Eingabe: Reine Auswahl wäre falsch — ein
   * Fonds mit unbekanntem Anbieter oder Domizil wäre sonst gar nicht
   * pflegbar, und genau für solche Fälle ist das Feature gedacht.
   */
  it('bietet ein Textfeld als Auswahl mit freier Eingabe an', () => {
    const wrapper = mountEditor(makeInstrument({ provider: null }), 'provider')

    const select = wrapper.findComponent(NSelect)
    expect(select.exists()).toBe(true)
    expect(select.props('filterable')).toBe(true)
    expect(select.props('tag')).toBe(true)
  })

  it('reicht die von außen übergebenen Vorschläge als Optionen durch', () => {
    const wrapper = mount(MetricEditor, {
      global: { plugins: [i18n] },
      props: {
        item: makeInstrument({ provider: null }),
        field: 'provider',
        options: ['Vanguard', 'iShares'],
      },
    })

    const select = wrapper.findComponent(NSelect)
    expect(select.props('options')).toEqual([
      { label: 'Vanguard', value: 'Vanguard' },
      { label: 'iShares', value: 'iShares' },
    ])
  })

  it('committet eine neu getippte oder aus den Vorschlägen gewählte Auswahl', async () => {
    const wrapper = mountEditor(makeInstrument({ provider: null }), 'provider')

    await wrapper.findComponent(NSelect).vm.$emit('update:value', 'Xtrackers')

    expect(wrapper.emitted('commit')?.[0]?.[0]).toEqual({ provider: 'Xtrackers' })
  })

  it('sperrt das Auswahlfeld bei einem verdeckten Eintrag, bietet aber das Entfernen an', () => {
    const wrapper = mountEditor(
      makeInstrument({ provider: 'iShares', manual_provider: 'Vanguard', shadowed_fields: ['provider'] }),
      'provider',
    )

    expect(wrapper.findComponent(NSelect).exists()).toBe(false)
    expect(wrapper.find('.metric-editor__remove').exists()).toBe(true)
  })
})
