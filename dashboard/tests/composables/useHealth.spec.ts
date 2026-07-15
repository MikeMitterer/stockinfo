import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('consola', () => ({
  consola: { error: vi.fn(), warn: vi.fn(), info: vi.fn() },
}))

import { useHealth } from '../../src/composables/useHealth'

beforeEach(() => vi.useFakeTimers())

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

/** Stubbt fetch mit einer ok-/health-Antwort (frische Response pro Aufruf). */
function stubHealthFetch(): ReturnType<typeof vi.fn> {
  const fetchMock = vi.fn().mockImplementation(() =>
    Promise.resolve(
      new Response(JSON.stringify({ status: 'ok', version: '0.1.0' }), { status: 200 }),
    ),
  )
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

describe('useHealth', () => {
  it('setzt Status und Version nach erfolgreichem Check', async () => {
    stubHealthFetch()
    const { status, version, start, stop } = useHealth(1000)
    start()
    await vi.runOnlyPendingTimersAsync()
    expect(status.value).toBe('ok')
    expect(version.value).toBe('0.1.0')
    stop()
  })

  it('setzt down bei Netzwerkfehler', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')))
    const { status, start, stop } = useHealth(1000)
    start()
    await vi.runOnlyPendingTimersAsync()
    expect(status.value).toBe('down')
    stop()
  })

  it('start ist idempotent — stop beendet das Polling vollständig', async () => {
    const fetchMock = stubHealthFetch()
    const { start, stop } = useHealth(1000)
    start()
    start() // zweiter Aufruf darf kein zweites Intervall anlegen
    await vi.advanceTimersByTimeAsync(2500)
    stop()
    const callsAfterStop = fetchMock.mock.calls.length
    await vi.advanceTimersByTimeAsync(5000)
    expect(fetchMock.mock.calls.length).toBe(callsAfterStop)
  })
})
