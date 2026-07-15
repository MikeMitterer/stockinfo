import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('consola', () => ({
  consola: { error: vi.fn(), warn: vi.fn(), info: vi.fn() },
}))

import { useRefresh } from '../../src/composables/useRefresh'

afterEach(() => vi.unstubAllGlobals())

describe('useRefresh', () => {
  it('trigger setzt result', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ total: 2, refreshed: 2 }), { status: 200 }),
    ))
    const { result, trigger } = useRefresh()
    await trigger()
    expect(result.value?.refreshed).toBe(2)
  })

  it('trigger setzt error bei Fehler', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('boom', { status: 500 })))
    const { error, trigger } = useRefresh()
    await trigger()
    expect(error.value).not.toBeNull()
  })
})
