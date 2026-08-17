import { mount } from '@vue/test-utils'
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
})
