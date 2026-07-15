import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('consola', () => ({
  consola: { error: vi.fn(), warn: vi.fn(), info: vi.fn() },
}))

import { useHistory } from '../../src/composables/useHistory'

afterEach(() => vi.unstubAllGlobals())

/** Erzeugt ein von außen auflösbares Promise (für Race-Tests). */
function deferred<T>(): { promise: Promise<T>; resolve: (value: T) => void } {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((promiseResolve) => {
    resolve = promiseResolve
  })
  return { promise, resolve }
}

describe('useHistory', () => {
  it('lädt Punkte per ISIN-Pfad', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify([{ price: 100 }]), { status: 200 }),
    )
    vi.stubGlobal('fetch', fetchMock)
    const { points, load } = useHistory()
    await load({ isin: 'IE00B3RBWM25', symbol: 'VGWL.DE' })
    expect(fetchMock.mock.calls[0][0]).toContain('/quote/IE00B3RBWM25/history')
    expect(points.value).toHaveLength(1)
  })

  it('setzt error bei Fehler', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('boom', { status: 502 })))
    const { error, load } = useHistory()
    await load({ isin: 'IE00B3RBWM25', symbol: 'VGWL.DE' })
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

    const { points, load } = useHistory()
    const firstLoad = load({ isin: 'AAAAAAAAAAA1', symbol: 'A' })
    const secondLoad = load({ isin: 'BBBBBBBBBBB2', symbol: 'B' })

    // Die zweite (jüngere) Anfrage antwortet zuerst …
    fastRequest.resolve(new Response(JSON.stringify([{ price: 2 }]), { status: 200 }))
    await secondLoad
    // … die erste (veraltete) danach — sie darf das Ergebnis nicht überschreiben.
    slowRequest.resolve(new Response(JSON.stringify([{ price: 1 }]), { status: 200 }))
    await firstLoad

    expect(points.value).toEqual([{ price: 2 }])
  })

  it('clear leert Punkte und Fehler', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response(JSON.stringify([{ price: 100 }]), { status: 200 }),
    ))
    const { points, error, load, clear } = useHistory()
    await load({ isin: 'IE00B3RBWM25', symbol: 'VGWL.DE' })
    clear()
    expect(points.value).toEqual([])
    expect(error.value).toBeNull()
  })
})
