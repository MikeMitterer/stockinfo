import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('consola', () => ({
  consola: { error: vi.fn(), warn: vi.fn(), info: vi.fn() },
}))

import { useDaily } from '../../src/composables/useDaily'

afterEach(() => vi.unstubAllGlobals())

/** Erzeugt ein von außen auflösbares Promise (für Race-Tests). */
function deferred<T>(): { promise: Promise<T>; resolve: (value: T) => void } {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((promiseResolve) => {
    resolve = promiseResolve
  })
  return { promise, resolve }
}

describe('useDaily', () => {
  it('lädt EOD-Punkte mit period-Parameter', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify([{ date: '2026-07-13', close: 100 }]), { status: 200 }),
    )
    vi.stubGlobal('fetch', fetchMock)
    const { daily, load } = useDaily()
    await load({ isin: null, symbol: 'GOLD.SG' }, '1m')
    expect(fetchMock.mock.calls[0][0]).toContain('/quote/by-symbol/GOLD.SG/daily?period=1m')
    expect(daily.value).toHaveLength(1)
  })

  it('setzt error bei Fehler', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('boom', { status: 502 })))
    const { error, load } = useDaily()
    await load({ isin: 'IE00B3RBWM25', symbol: 'VGWL.DE' }, '1w')
    expect(error.value).not.toBeNull()
  })

  it('verwirft veraltete Antworten (Race-Guard)', async () => {
    const slowRequest = deferred<Response>()
    const fastRequest = deferred<Response>()
    const fetchMock = vi
      .fn()
      .mockReturnValueOnce(slowRequest.promise)
      .mockReturnValueOnce(fastRequest.promise)
    vi.stubGlobal('fetch', fetchMock)

    const { daily, load } = useDaily()
    const firstLoad = load({ isin: 'AAAAAAAAAAA1', symbol: 'A' }, '1m')
    const secondLoad = load({ isin: 'BBBBBBBBBBB2', symbol: 'B' }, '1m')

    fastRequest.resolve(new Response(JSON.stringify([{ close: 2 }]), { status: 200 }))
    await secondLoad
    slowRequest.resolve(new Response(JSON.stringify([{ close: 1 }]), { status: 200 }))
    await firstLoad

    expect(daily.value).toEqual([{ close: 2 }])
  })

  it('clear leert Punkte und Fehler', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response(JSON.stringify([{ close: 100 }]), { status: 200 }),
    ))
    const { daily, error, load, clear } = useDaily()
    await load({ isin: 'IE00B3RBWM25', symbol: 'VGWL.DE' }, 'max')
    clear()
    expect(daily.value).toEqual([])
    expect(error.value).toBeNull()
  })
})
