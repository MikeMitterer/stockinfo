import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('consola', () => ({ consola: { error: vi.fn(), warn: vi.fn(), info: vi.fn() } }))

import { useFx } from '../../src/composables/useFx'

afterEach(() => vi.unstubAllGlobals())

describe('useFx', () => {
  it('holt den Kurs', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ base: 'EUR', quote: 'USD', rate: 1.15, quote_time: 't', source: 'yfinance', cached: false, stale: false, fetched_at: 't' }),
      { status: 200 },
    )))
    const { result, convert } = useFx()
    await convert('EUR', 'USD')
    expect(result.value?.rate).toBe(1.15)
  })

  it('setzt error bei Fehlschlag', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('boom', { status: 502 })))
    const { error, convert } = useFx()
    await convert('EUR', 'XXX')
    expect(error.value).not.toBeNull()
  })
})
