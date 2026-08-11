import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('consola', () => ({ consola: { error: vi.fn(), warn: vi.fn(), info: vi.fn() } }))

import { useExchanges } from '../../src/composables/useExchanges'

afterEach(() => vi.unstubAllGlobals())

describe('useExchanges', () => {
  it('lädt die Börsentabelle', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ default_exchange: 'XETR', exchanges: [{ mic: 'XETR', suffix: '.DE', name: 'Xetra', region: 'germany', currency: 'EUR' }] }),
      { status: 200 },
    )))
    const { data, load } = useExchanges()
    await load()
    expect(data.value?.default_exchange).toBe('XETR')
    expect(data.value?.exchanges[0].mic).toBe('XETR')
  })
})
