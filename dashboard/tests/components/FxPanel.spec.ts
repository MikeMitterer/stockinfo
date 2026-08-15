import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('consola', () => ({ consola: { error: vi.fn() } }))
import FxPanel from '../../src/components/FxPanel.vue'
import { i18n } from '../../src/i18n'

beforeEach(() => {
  i18n.global.locale.value = 'en' // deterministisches Dezimaltrennzeichen '.'
})
afterEach(() => vi.unstubAllGlobals())

describe('FxPanel', () => {
  it('rendert Währungs-Dropdowns aus der currencies-Prop', () => {
    const wrapper = mount(FxPanel, {
      global: { plugins: [i18n] },
      props: { currencies: ['EUR', 'GBP', 'USD'] },
    })
    const selects = wrapper.findAll('select')
    expect(selects).toHaveLength(2)
    const options = selects[0].findAll('option').map((o) => o.text())
    expect(options).toEqual(['EUR', 'GBP', 'USD'])
  })

  it('zeigt den Kurs auf 3 Nachkommastellen gerundet, Rohwert im title', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ base: 'EUR', quote: 'USD', rate: 1.1527377367019653, quote_time: '2026-08-13T07:41:13.759837+00:00', source: 'yfinance', cached: false, stale: false, fetched_at: 't' }),
      { status: 200 },
    )))
    const wrapper = mount(FxPanel, {
      global: { plugins: [i18n] },
      props: { currencies: ['EUR', 'USD'] },
    })
    await wrapper.find('button:last-of-type').trigger('click')
    await flushPromises()

    const rate = wrapper.find('.rate')
    expect(rate.text()).toContain('1 EUR = 1.153 USD')      // 3 Nachkommastellen
    expect(rate.text()).not.toContain('1.1527377367019653') // nicht roh
    expect(rate.attributes('title')).toBe('1.1527377367019653')
  })

  it('rechnet einen Betrag mit der Rate um (2 Nachkommastellen)', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ base: 'EUR', quote: 'USD', rate: 1.15, quote_time: 't', source: 'yfinance', cached: false, stale: false, fetched_at: 't' }),
      { status: 200 },
    )))
    const wrapper = mount(FxPanel, {
      global: { plugins: [i18n] },
      props: { currencies: ['EUR', 'USD'] },
    })
    await wrapper.find('.amount').setValue('200')
    await wrapper.find('button:last-of-type').trigger('click')
    await flushPromises()
    expect(wrapper.find('.amount-result').text()).toContain('200 EUR = 230.00 USD')
  })

  it('fällt bei leerem Betrag auf 1 zurück (kein Crash)', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ base: 'EUR', quote: 'USD', rate: 1.15, quote_time: 't', source: 'yfinance', cached: false, stale: false, fetched_at: 't' }),
      { status: 200 },
    )))
    const wrapper = mount(FxPanel, {
      global: { plugins: [i18n] },
      props: { currencies: ['EUR', 'USD'] },
    })
    await wrapper.find('.amount').setValue('')
    await wrapper.find('button:last-of-type').trigger('click')
    await flushPromises()
    expect(wrapper.find('.amount-result').text()).toContain('1 EUR = 1.15 USD')
  })

  it('zeigt die Kurszeit formatiert (kein roher ISO-String)', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ base: 'EUR', quote: 'USD', rate: 1.15, quote_time: '2026-08-13T07:41:13.759837+00:00', source: 'yfinance', cached: false, stale: false, fetched_at: 't' }),
      { status: 200 },
    )))
    const wrapper = mount(FxPanel, {
      global: { plugins: [i18n] },
      props: { currencies: ['EUR', 'USD'] },
    })
    await wrapper.find('button:last-of-type').trigger('click')
    await flushPromises()
    expect(wrapper.text()).not.toContain('2026-08-13T07:41:13') // kein ISO-Rohstring
    expect(wrapper.text()).toContain('2026')                    // Jahr sichtbar
  })
})
