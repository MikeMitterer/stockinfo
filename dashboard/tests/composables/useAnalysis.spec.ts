import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('consola', () => ({
  consola: { error: vi.fn(), warn: vi.fn(), info: vi.fn() },
}))

import { useAnalysis } from '../../src/composables/useAnalysis'

afterEach(() => vi.unstubAllGlobals())

describe('useAnalysis', () => {
  it('lädt das Analyse-Ergebnis', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({ symbol: 'EUNL.DE', isin: 'IE00B4L5Y983', total: 1.2, stages: [] }),
        { status: 200 },
      ),
    ))
    const { result, analyze } = useAnalysis()
    await analyze({ isin: 'IE00B4L5Y983', symbol: 'EUNL.DE' })
    expect(result.value?.symbol).toBe('EUNL.DE')
  })

  it('setzt error bei Fehlschlag', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('boom', { status: 502 })))
    const { error, analyze } = useAnalysis()
    await analyze({ isin: null, symbol: 'NOPE' })
    expect(error.value).not.toBeNull()
  })
})
