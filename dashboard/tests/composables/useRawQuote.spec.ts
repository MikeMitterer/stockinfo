import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('consola', () => ({
  consola: { error: vi.fn(), warn: vi.fn(), info: vi.fn() },
}))

import { useRawQuote } from '../../src/composables/useRawQuote'

afterEach(() => vi.unstubAllGlobals())

describe('useRawQuote', () => {
  it('liefert die vollständige absolute URL (nicht nur den Pfad)', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ symbol: 'VGWL.DE' }), { status: 200 }),
    ))
    const { url, load } = useRawQuote()
    await load({ isin: 'IE00B3RBWM25', symbol: 'VGWL.DE' })
    expect(url.value).toBe(`${window.location.origin}/quote/IE00B3RBWM25`)
  })

  it('baut die absolute URL auch für die Symbol-Variante (ohne ISIN)', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ symbol: 'VGWL.DE' }), { status: 200 }),
    ))
    const { url, load } = useRawQuote()
    await load({ isin: null, symbol: 'VGWL.DE' })
    expect(url.value).toBe(`${window.location.origin}/quote?symbol=VGWL.DE`)
  })

  it('lädt die Antwort als formatiertes JSON', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ price: 100 }), { status: 200 }),
    ))
    const { json, load } = useRawQuote()
    await load({ isin: 'IE00B3RBWM25', symbol: 'VGWL.DE' })
    expect(json.value).toBe(JSON.stringify({ price: 100 }, null, 2))
  })

  it('setzt error bei Fehler', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('boom', { status: 502 })))
    const { error, load } = useRawQuote()
    await load({ isin: 'IE00B3RBWM25', symbol: 'VGWL.DE' })
    expect(error.value).not.toBeNull()
  })
})
