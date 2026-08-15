import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import InstrumentsTable from '../../src/components/InstrumentsTable.vue'
import { i18n } from '../../src/i18n'
import type { InstrumentSummary } from '../../src/types'

const base: InstrumentSummary = {
  isin: 'US0378331005', symbol: 'APC.DE', exchange: 'XETR', name: 'Apple Inc.',
  type: 'stock', currency: 'EUR', provider: null, ter: null, replication: null,
  fund_size: null, volatility: 25.8, accumulating: null, meta_fetched_at: null,
  latest_price: 265, latest_quote_time: null, latest_currency: 'EUR',
  latest_fetched_at: null, history_count: 2,
}
const instruments = [base, { ...base, symbol: 'VGWL.DE', name: 'Vanguard FTSE All-World' }]

/** Setzt die Viewport-Breite für useIsCompact. */
function stubMatchMedia(compact: boolean) {
  vi.stubGlobal('matchMedia', vi.fn().mockReturnValue({
    matches: compact, media: '',
    addEventListener: () => {}, removeEventListener: () => {},
  }))
}

function mountTable() {
  return mount(InstrumentsTable, {
    props: {
      instruments, selectedSymbol: null, refreshingSymbol: null,
      extraetfEtfUrl: '', extraetfStockUrl: '', yahooUrl: '',
    },
    global: { plugins: [i18n] },
  })
}

beforeEach(() => {
  i18n.global.locale.value = 'de'
})
afterEach(() => {
  vi.unstubAllGlobals()
})

describe('InstrumentsTable — Darstellung nach Breite', () => {
  it('zeigt ab md die Tabelle und keine Karten', () => {
    stubMatchMedia(false)
    const wrapper = mountTable()
    expect(wrapper.find('table').exists()).toBe(true)
    expect(wrapper.findAll('.icard')).toHaveLength(0)
  })

  it('zeigt unter md Karten und keine Tabelle', () => {
    stubMatchMedia(true)
    const wrapper = mountTable()
    expect(wrapper.find('table').exists()).toBe(false)
    expect(wrapper.findAll('.icard')).toHaveLength(2)
  })

  it('bietet unter md eine Sortier-Auswahl', () => {
    stubMatchMedia(true)
    const wrapper = mountTable()
    expect(wrapper.find('.tsort__select').exists()).toBe(true)
    expect(wrapper.find('.tsort__dir').exists()).toBe(true)
  })

  it('reicht select aus einer Karte nach oben durch', async () => {
    stubMatchMedia(true)
    const wrapper = mountTable()
    await wrapper.find('.icard__head').trigger('click')
    expect(wrapper.emitted('select')).toHaveLength(1)
  })

  it('zeigt den Leerzustand unabhängig von der Breite', () => {
    stubMatchMedia(true)
    const wrapper = mount(InstrumentsTable, {
      props: {
        instruments: [], selectedSymbol: null, refreshingSymbol: null,
        extraetfEtfUrl: '', extraetfStockUrl: '', yahooUrl: '',
      },
      global: { plugins: [i18n] },
    })
    expect(wrapper.find('.empty').exists()).toBe(true)
  })
})
