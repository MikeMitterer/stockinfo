import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('consola', () => ({
  consola: { error: vi.fn(), warn: vi.fn(), info: vi.fn() },
}))

import { useInstrumentActions } from '../../src/composables/useInstrumentActions'

afterEach(() => vi.unstubAllGlobals())

describe('useInstrumentActions', () => {
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

  it('setIsin ruft PUT und toleriert 204', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }))
    vi.stubGlobal('fetch', fetchMock)
    const { error, setIsin } = useInstrumentActions()
    await setIsin('VGWL.DE', 'IE00B3RBWM25')
    expect(fetchMock.mock.calls[0][0]).toContain('/instruments/by-symbol/VGWL.DE/isin')
    expect((fetchMock.mock.calls[0][1] as RequestInit).method).toBe('PUT')
    expect(error.value).toBeNull()
  })

  it('setIsin setzt error bei Fehler', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('boom', { status: 500 })))
    const { error, setIsin } = useInstrumentActions()
    await setIsin('VGWL.DE', 'IE00B3RBWM25')
    expect(error.value).not.toBeNull()
  })

  it('remove nutzt den by-symbol-Pfad ohne ISIN', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }))
    vi.stubGlobal('fetch', fetchMock)
    await useInstrumentActions().remove({ isin: null, symbol: 'GOLD.SG' })
    expect(fetchMock.mock.calls[0][0]).toContain('/instruments/by-symbol/GOLD.SG')
  })
})
