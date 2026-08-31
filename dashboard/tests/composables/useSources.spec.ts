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
  it('nennt die erste einsatzbereite Quelle der Kursrolle', async () => {
    answerWith([
      { name: 'yfinance', position: 1, configured: true },
      { name: 'yaml-file', position: 2, configured: true },
    ])
    const { quoteSource, load } = useSources()
    await load()

    expect(quoteSource.value).toBe('yfinance')
  })

  /*
   * **Nicht die erste konfigurierte, sondern die erste einsatzbereite.** Eine
   * Quelle, die nicht arbeiten kann, liefert auch keinen Kurs — sie zu nennen
   * waere die Umkehrung dessen, wofuer die Zeile da ist.
   */
  it('ueberspringt eine Quelle, die nicht arbeiten kann', async () => {
    answerWith([
      { name: 'openfigi', position: 1, configured: false },
      { name: 'yaml-file', position: 2, configured: true },
    ])
    const { quoteSource, load } = useSources()
    await load()

    expect(quoteSource.value).toBe('yaml-file')
  })

  /*
   * Die Reihenfolge steht in `position`, nicht in der Reihenfolge der Liste.
   * Ohne die Sortierung haenge die Anzeige daran, wie der Server serialisiert.
   */
  it('folgt der Rangfolge, nicht der Reihenfolge der Antwort', async () => {
    answerWith([
      { name: 'yaml-file', position: 2, configured: true },
      { name: 'yfinance', position: 1, configured: true },
    ])
    const { quoteSource, load } = useSources()
    await load()

    expect(quoteSource.value).toBe('yfinance')
  })

  it('behauptet keine Quelle, wenn keine bereitsteht', async () => {
    answerWith([{ name: 'openfigi', position: 1, configured: false }])
    const { quoteSource, load } = useSources()
    await load()

    expect(quoteSource.value).toBeNull()
  })

  /*
   * Ein Nebenabruf darf die Seite nicht mitnehmen: `load()` faengt den Fehler,
   * und die Angabe fehlt einfach.
   */
  it('bleibt still, wenn /sources nicht antwortet', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')))
    const { quoteSource, load } = useSources()

    await expect(load()).resolves.toBeUndefined()
    expect(quoteSource.value).toBeNull()
  })

  /*
   * Die Gegenprobe zur Rollenwahl: Eine Devisenquelle an erster Stelle darf
   * die Kursangabe nicht besetzen. Ohne diesen Fall waere der Filter auf
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
    const { quoteSource, load } = useSources()
    await load()

    expect(quoteSource.value).toBe('yfinance')
  })
})
