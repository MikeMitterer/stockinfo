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
  it('zeigt den Kurs auf 3 Nachkommastellen gerundet, Rohwert im title', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ base: 'EUR', quote: 'USD', rate: 1.1527377367019653, quote_time: '2026-08-13T07:41:13.759837+00:00', source: 'yfinance', cached: false, stale: false, fetched_at: 't' }),
      { status: 200 },
    )))
    const wrapper = mount(FxPanel, { global: { plugins: [i18n] } })
    await wrapper.find('button:last-of-type').trigger('click')
    await flushPromises()

    const rate = wrapper.find('.rate')
    expect(rate.text()).toContain('1 EUR = 1.153 USD')      // 3 Nachkommastellen
    expect(rate.text()).not.toContain('1.1527377367019653') // nicht roh
    expect(rate.attributes('title')).toBe('1.1527377367019653')
  })

  it('zeigt die Kurszeit formatiert (kein roher ISO-String)', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ base: 'EUR', quote: 'USD', rate: 1.15, quote_time: '2026-08-13T07:41:13.759837+00:00', source: 'yfinance', cached: false, stale: false, fetched_at: 't' }),
      { status: 200 },
    )))
    const wrapper = mount(FxPanel, { global: { plugins: [i18n] } })
    await wrapper.find('button:last-of-type').trigger('click')
    await flushPromises()
    expect(wrapper.text()).not.toContain('2026-08-13T07:41:13') // kein ISO-Rohstring
    expect(wrapper.text()).toContain('2026')                    // Jahr sichtbar
  })
})
