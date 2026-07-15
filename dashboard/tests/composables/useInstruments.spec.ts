import { afterEach, describe, expect, it, vi } from 'vitest'

// consola stummschalten — Fehlerpfad-Tests würden sonst rote Zeilen ausgeben.
vi.mock('consola', () => ({
  consola: { error: vi.fn(), warn: vi.fn(), info: vi.fn() },
}))

import { useInstruments } from '../../src/composables/useInstruments'

afterEach(() => vi.unstubAllGlobals())

describe('useInstruments', () => {
  it('lädt die Liste', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response(JSON.stringify([{ symbol: 'VGWL.DE', history_count: 2 }]), { status: 200 }),
    ))
    const { instruments, loading, load } = useInstruments()
    await load()
    expect(loading.value).toBe(false)
    expect(instruments.value[0].symbol).toBe('VGWL.DE')
  })

  it('setzt error bei Fehler', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('boom', { status: 500 })))
    const { error, load } = useInstruments()
    await load()
    expect(error.value).not.toBeNull()
  })
})
