import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import ExchangesPanel from '../../src/components/ExchangesPanel.vue'
import { i18n } from '../../src/i18n'

describe('ExchangesPanel', () => {
  it('rendert Börsen und markiert die Default-Börse', () => {
    const wrapper = mount(ExchangesPanel, {
      global: { plugins: [i18n] },
      props: { data: { default_exchange: 'XETR', exchanges: [
        { mic: 'XETR', suffix: '.DE', name: 'Xetra', region: 'germany', currency: 'EUR' },
        { mic: 'US', suffix: '', name: 'NYSE / NASDAQ', region: 'usa', currency: 'USD' },
      ] } },
    })
    expect(wrapper.text()).toContain('Xetra')
    expect(wrapper.text()).toContain('NYSE / NASDAQ')
    expect(wrapper.find('tr.is-default').text()).toContain('Xetra')
  })
})
