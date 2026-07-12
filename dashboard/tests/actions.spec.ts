import { afterEach, describe, expect, it, vi } from 'vitest'

import { isIsin, useInstrumentActions } from '../src/composables/useInstrumentActions'
import { useRefresh } from '../src/composables/useRefresh'

afterEach(() => vi.unstubAllGlobals())

describe('actions', () => {
  it('isIsin erkennt ISINs', () => {
    expect(isIsin('IE00B3RBWM25')).toBe(true)
    expect(isIsin('VGWL.DE')).toBe(false)
  })

  it('add ruft /quote/{isin} bei ISIN', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('{}', { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)
    await useInstrumentActions().add('IE00B3RBWM25')
    expect(fetchMock.mock.calls[0][0]).toContain('/quote/IE00B3RBWM25')
  })

  it('add ruft /quote?symbol bei Symbol', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('{}', { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)
    await useInstrumentActions().add('VGWL.DE')
    expect(fetchMock.mock.calls[0][0]).toContain('/quote?symbol=VGWL.DE')
  })

  it('trigger setzt result', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ total: 2, refreshed: 2 }), { status: 200 }),
      ),
    )
    const { result, trigger } = useRefresh()
    await trigger()
    expect(result.value?.refreshed).toBe(2)
  })
})
