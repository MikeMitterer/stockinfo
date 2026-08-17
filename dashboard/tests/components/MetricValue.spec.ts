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
})
