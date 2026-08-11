import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('consola', () => ({ consola: { error: vi.fn() } }))
import FxPanel from '../../src/components/FxPanel.vue'
import { i18n } from '../../src/i18n'

afterEach(() => vi.unstubAllGlobals())

describe('FxPanel', () => {
  it('zeigt den Kurs nach dem Umrechnen', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ base: 'EUR', quote: 'USD', rate: 1.15, quote_time: 't', source: 'yfinance', cached: false, stale: false, fetched_at: 't' }),
      { status: 200 },
    )))
    const wrapper = mount(FxPanel, { global: { plugins: [i18n] } })
    await wrapper.find('button:last-of-type').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('1 EUR = 1.15 USD')
  })
})
