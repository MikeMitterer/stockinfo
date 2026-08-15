import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'

import InstrumentCard from '../../src/components/InstrumentCard.vue'
import { i18n } from '../../src/i18n'
import type { InstrumentSummary } from '../../src/types'

const item: InstrumentSummary = {
  isin: 'US0378331005', symbol: 'APC.DE', exchange: 'XETR', name: 'Apple Inc.',
  type: 'stock', currency: 'EUR', provider: null, ter: null, replication: null,
  fund_size: null, volatility: 25.8, accumulating: null, meta_fetched_at: null,
  latest_price: 265, latest_quote_time: null, latest_currency: 'EUR',
  latest_fetched_at: null, history_count: 2,
}

function mountCard(overrides: Partial<InstrumentSummary> = {}) {
  return mount(InstrumentCard, {
    props: {
      item: { ...item, ...overrides },
      selected: false, refreshing: false,
      extraetfUrl: '', yahooUrl: '',
    },
    global: { plugins: [i18n] },
  })
}

beforeEach(() => {
  i18n.global.locale.value = 'de'
})

describe('InstrumentCard', () => {
  it('zeigt Symbol, Typ, Kurs und Name', () => {
    const wrapper = mountCard()
    expect(wrapper.find('.icard__symbol').text()).toBe('APC.DE')
    expect(wrapper.find('.icard__type').text()).toBe('stock')
    expect(wrapper.find('.icard__price').text()).toContain('265,00')
    expect(wrapper.find('.icard__name').text()).toBe('Apple Inc.')
  })

  it('hält die Kennzahlen bis zum Aufklappen verborgen', async () => {
    const wrapper = mountCard()
    expect(wrapper.find('.icard__details').exists()).toBe(false)
    await wrapper.find('.icard__toggle').trigger('click')
    expect(wrapper.find('.icard__details').exists()).toBe(true)
    expect(wrapper.find('.icard__details').text()).toContain('25.80')
  })

  it('emittiert select beim Antippen der Karte', async () => {
    const wrapper = mountCard()
    await wrapper.find('.icard__head').trigger('click')
    expect(wrapper.emitted('select')).toHaveLength(1)
  })

  it('löst beim Aufklappen kein select aus', async () => {
    const wrapper = mountCard()
    await wrapper.find('.icard__toggle').trigger('click')
    expect(wrapper.emitted('select')).toBeUndefined()
  })

  it('emittiert refresh und remove aus den Aktionen', async () => {
    const wrapper = mountCard()
    await wrapper.find('.icard__action--refresh').trigger('click')
    await wrapper.find('.icard__action--remove').trigger('click')
    expect(wrapper.emitted('refresh')).toHaveLength(1)
    expect(wrapper.emitted('remove')).toHaveLength(1)
    expect(wrapper.emitted('select')).toBeUndefined()
  })

  it('bietet den ISIN-Editor, wenn keine ISIN da ist', async () => {
    const wrapper = mountCard({ isin: null })
    await wrapper.find('.icard__toggle').trigger('click')
    expect(wrapper.find('.isin__add').exists()).toBe(true)
  })
})
