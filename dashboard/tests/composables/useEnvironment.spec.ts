import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('consola', () => ({
  consola: { error: vi.fn(), warn: vi.fn(), info: vi.fn() },
}))

import { useEnvironment } from '../../src/composables/useEnvironment'

afterEach(() => vi.unstubAllGlobals())

describe('useEnvironment', () => {
  it('lädt die Env-Infos', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ version: '0.1.0', default_exchange: 'XETR' }), { status: 200 }),
    ))
    const { env, load } = useEnvironment()
    await load()
    expect(env.value?.default_exchange).toBe('XETR')
  })
})
