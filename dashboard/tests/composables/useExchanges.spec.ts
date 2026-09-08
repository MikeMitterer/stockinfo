import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('consola', () => ({ consola: { error: vi.fn(), warn: vi.fn(), info: vi.fn() } }))

import { useExchanges } from '../../src/composables/useExchanges'

afterEach(() => vi.unstubAllGlobals())

describe('useExchanges', () => {
  it('verwirft alte Unterstützung bei einem fehlgeschlagenen Neuladen', async () => {
    vi.stubGlobal('fetch', vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ catalog: [{ mic: 'XBUD' }] })))
      .mockRejectedValueOnce(new Error('offline')))
    const { data, load, error, loading } = useExchanges()
    await load()
    expect(data.value?.catalog).toHaveLength(1)
    await load()
    expect(data.value).toBeNull()
    expect(error.value).toBeTruthy()
    expect(loading.value).toBe(false)
  })

  it('lädt die Börsentabelle', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
      JSON.stringify({
        default_exchange: 'XETR',
        default_exchange_kind: 'exchange',
        catalog: [{
          kind: 'exchange', mic: 'XETR', alias: 'DE', name: 'Xetra',
          region: 'germany', currency: 'EUR',
          provenance: { kind: 'core' },
        }],
      }),
      { status: 200 },
    )))
    const { data, load } = useExchanges()
    await load()
    expect(data.value?.default_exchange).toBe('XETR')
    expect(data.value?.default_exchange_kind).toBe('exchange')
    const first = data.value?.catalog[0]
    expect(first?.kind === 'exchange' && first.mic).toBe('XETR')
  })
})
