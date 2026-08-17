import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import MetricValue from '../../src/components/MetricValue.vue'
import { i18n } from '../../src/i18n'
import { makeInstrument } from '../fixtures/instrument'

describe('MetricValue', () => {
  it('zeigt den wirksamen Wert ohne jede Bedienung', () => {
    const wrapper = mount(MetricValue, {
      global: { plugins: [i18n] },
      props: { item: makeInstrument({ ter: 0.2 }), field: 'ter' },
    })

    expect(wrapper.text()).toMatch(/0[.,]20/)
    expect(wrapper.find('button').exists()).toBe(false)
  })

  it('markiert einen von Hand eingetragenen Wert', () => {
    const wrapper = mount(MetricValue, {
      global: { plugins: [i18n] },
      props: {
        item: makeInstrument({ ter: 0.2, manual_ter: 0.2, manual_fields: ['ter'] }),
        field: 'ter',
      },
    })

    expect(wrapper.find('.metric__mark').exists()).toBe(true)
  })

  it('zeigt bei einem verdeckten Eintrag den Wert der Quelle, nicht den eingetragenen', () => {
    /*
     * Genau der Zustand, der in diesem Projekt bereits mehrfach Fehler
     * verursacht hat: Es gibt eine eigene Eingabe, aber die Quelle liefert
     * etwas und hat Vorrang. Angezeigt wird der Wert der Quelle — die eigene
     * Eingabe bleibt gespeichert, greift aber gerade nicht.
     */
    const wrapper = mount(MetricValue, {
      global: { plugins: [i18n] },
      props: {
        item: makeInstrument({ ter: 0.3, manual_ter: 0.2, shadowed_fields: ['ter'] }),
        field: 'ter',
      },
    })

    expect(wrapper.text()).toMatch(/0[.,]30/)
    expect(wrapper.find('.metric--shadowed').exists()).toBe(true)
    expect(wrapper.find('.metric__mark').exists()).toBe(true)
  })
})
