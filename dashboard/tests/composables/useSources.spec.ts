import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('consola', () => ({
  consola: { error: vi.fn(), warn: vi.fn(), info: vi.fn() },
}))

import { useSources } from '../../src/composables/useSources'

afterEach(() => vi.unstubAllGlobals())

/** Baut eine `/sources`-Antwort aus Kurzangaben — nur die Rolle `quotes` variiert. */
function answerWith(entries: Array<{ name: string; position: number; configured: boolean }>): void {
  const sources = entries.map((entry) => ({
    ...entry,
    role: 'quotes',
    reason: entry.configured ? '' : 'Pflichtangaben fehlen',
    cost: 'free',
  }))
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ config_path: null, profile: null, sources }), { status: 200 }),
    ),
  )
}

describe('useSources', () => {
  /*
   * **Beide Namen, und in dieser Reihenfolge.** `/sources` beschreibt, wer
   * gefragt wird — nicht, wer eine gespeicherte Quote geliefert hat. Ein
   * einzelner Name waere eine Aussage, die diese Daten nicht decken.
   */
  it('nennt die einsatzbereite Kurskette in Rangfolge', async () => {
    answerWith([
      { name: 'yfinance', position: 1, configured: true },
      { name: 'yaml-file', position: 2, configured: true },
    ])
    const { quoteChain, load } = useSources()
    await load()

    expect(quoteChain.value).toEqual(['yfinance', 'yaml-file'])
  })

  /*
   * Eine Quelle, die nicht arbeiten kann, wird aus der Laufzeitkette entfernt
   * und gehoert deshalb nicht in die Anzeige.
   */
  it('laesst eine Quelle weg, die nicht arbeiten kann', async () => {
    answerWith([
      { name: 'openfigi', position: 1, configured: false },
      { name: 'yaml-file', position: 2, configured: true },
    ])
    const { quoteChain, load } = useSources()
    await load()

    expect(quoteChain.value).toEqual(['yaml-file'])
  })

  /*
   * Die Rangfolge steht in `position`, nicht in der Reihenfolge der Antwort.
   * Ohne die Sortierung haenge die Anzeige daran, wie der Server serialisiert.
   */
  it('folgt der Rangfolge, nicht der Reihenfolge der Antwort', async () => {
    answerWith([
      { name: 'yaml-file', position: 2, configured: true },
      { name: 'yfinance', position: 1, configured: true },
    ])
    const { quoteChain, load } = useSources()
    await load()

    expect(quoteChain.value).toEqual(['yfinance', 'yaml-file'])
  })

  it('behauptet keine Quelle, wenn keine bereitsteht', async () => {
    answerWith([{ name: 'openfigi', position: 1, configured: false }])
    const { quoteChain, load } = useSources()
    await load()

    expect(quoteChain.value).toEqual([])
  })

  /* Ein Nebenabruf darf die Seite nicht mitnehmen: `load()` faengt den Fehler. */
  it('bleibt still, wenn /sources nicht antwortet', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')))
    const { quoteChain, load } = useSources()

    await expect(load()).resolves.toBeUndefined()
    expect(quoteChain.value).toEqual([])
  })

  /*
   * Die Gegenprobe zur Rollenwahl: Ohne diesen Fall waere der Filter auf
   * `role === 'quotes'` entbehrlich, und niemand haette es gemerkt.
   */
  it('nimmt keine Quelle aus einer anderen Rolle', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            config_path: null,
            profile: null,
            sources: [
              { name: 'fx-only', role: 'fx', position: 1, configured: true, reason: '', cost: 'free' },
              { name: 'yfinance', role: 'quotes', position: 1, configured: true, reason: '', cost: 'free' },
            ],
          }),
          { status: 200 },
        ),
      ),
    )
    const { quoteChain, load } = useSources()
    await load()

    expect(quoteChain.value).toEqual(['yfinance'])
  })
})
