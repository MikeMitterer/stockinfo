import { afterEach, describe, expect, it, vi } from 'vitest'

// consola stummschalten — der Fehlerpfad-Test würde sonst eine rote Zeile ausgeben.
vi.mock('consola', () => ({
  consola: { error: vi.fn(), warn: vi.fn(), info: vi.fn() },
}))

import { useEnvironment } from '../src/composables/useEnvironment'
import { useHistory } from '../src/composables/useHistory'
import { useInstruments } from '../src/composables/useInstruments'

afterEach(() => vi.unstubAllGlobals())

function stubFetch(body: unknown, status = 200): void {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status })),
  )
}

describe('composables', () => {
  it('useInstruments lädt Liste', async () => {
    stubFetch([{ symbol: 'VGWL.DE', history_count: 2 }])
    const { instruments, loading, load } = useInstruments()
    await load()
    expect(loading.value).toBe(false)
    expect(instruments.value[0].symbol).toBe('VGWL.DE')
  })

  it('useEnvironment lädt Env', async () => {
    stubFetch({ version: '0.1.0', default_exchange: 'XETR' })
    const { env, load } = useEnvironment()
    await load()
    expect(env.value?.default_exchange).toBe('XETR')
  })

  it('useHistory setzt error bei Fehler', async () => {
    stubFetch('boom', 502)
    const { error, load } = useHistory()
    await load('IE00B3RBWM25')
    expect(error.value).not.toBeNull()
  })
})
