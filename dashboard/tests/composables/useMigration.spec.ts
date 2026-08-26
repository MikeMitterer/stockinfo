/**
 * Tests des Zustandsautomaten vor dem Dashboard.
 *
 * Der Kern ist die Abbildung von `/ready` auf eine Lage. Sie ist der Grund,
 * warum das UI überhaupt `/ready` fragt und nicht `/migration`: Ein
 * festgeschriebener Umzug mit nicht angelaufenem Betrieb sagt dort
 * `pending: false` — das Dashboard käme hoch, und dass der Hintergrund-Abruf
 * tot ist, merkte niemand.
 */
import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('consola', () => ({
  consola: { error: vi.fn(), warn: vi.fn(), info: vi.fn() },
}))

import { useMigration } from '../../src/composables/useMigration'

afterEach(() => {
  vi.unstubAllGlobals()
  vi.useRealTimers()
})

/** Ein leerer Bericht — „noch nie ein Umzug gelaufen". */
const NO_REPORT = { completed: false, rejected: [] }

/** Eine Vorschau mit genau einer Ablehnung. */
const PREVIEW = {
  pending: true,
  migrating: 2,
  unchanged: 0,
  rejected: [
    {
      symbol: 'VTI',
      isin: null,
      name: null,
      exchange: null,
      type: null,
      currency: null,
      reason: 'symbol_without_exchange_suffix',
      quotes: 3,
      daily_closes: 7,
    },
  ],
  lost_quotes: 3,
  lost_daily_closes: 7,
}

/**
 * Beantwortet jeden Pfad aus einer Tabelle.
 *
 * Absichtlich **nach Pfad** und nicht der Reihe nach: Ein Test, der die
 * Aufrufreihenfolge festschreibt, bricht bei jeder Umstellung, ohne dass sich
 * das Verhalten geändert hätte.
 */
function stubApi(routes: Record<string, { status?: number; body: unknown }>): ReturnType<typeof vi.fn> {
  const fetchMock = vi.fn().mockImplementation((url: string) => {
    const path = url.replace(/^https?:\/\/[^/]+/, '').split('?')[0]
    const route = routes[path]
    if (!route) return Promise.reject(new Error(`unerwarteter Pfad: ${path}`))
    return Promise.resolve(
      new Response(JSON.stringify(route.body), { status: route.status ?? 200 }),
    )
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

describe('useMigration.check', () => {
  it('erkennt den ausstehenden Umzug und holt die Vorschau', async () => {
    stubApi({
      '/ready': { status: 503, body: { status: 'migration_pending', version: '1', database: 'ok' } },
      '/migration': { body: PREVIEW },
    })

    const { phase, preview, check } = useMigration()
    await check()

    expect(phase.value).toBe('pending')
    expect(preview.value?.rejected).toHaveLength(1)
  })

  it('lässt den Normalbetrieb durch', async () => {
    stubApi({
      '/ready': { body: { status: 'ok', version: '1', database: 'ok' } },
      '/migration/report': { body: NO_REPORT },
    })

    const { phase, check } = useMigration()
    await check()

    expect(phase.value).toBe('serving')
  })

  /*
   * **Der Grund für diesen Test.** `degraded` trägt zwei völlig verschiedene
   * Lagen, und `status` allein trennt sie nicht — das ist keine Nachlässigkeit
   * im Vertrag, sondern Absicht: Beide sagen „hier ist etwas kaputt". Wer die
   * beiden zusammenwirft, schickt den Benutzer in den falschen Ablauf: einmal
   * „Server prüfen", einmal „Betrieb erneut starten".
   */
  it('trennt den gescheiterten Betriebsstart von der toten Datenbank', async () => {
    stubApi({
      '/ready': { status: 503, body: { status: 'degraded', version: '1', database: 'ok' } },
      '/migration/report': { body: { completed: true, rejected: PREVIEW.rejected } },
    })

    const { phase, report, check } = useMigration()
    await check()

    expect(phase.value).toBe('startupFailed')
    expect(report.value?.rejected).toHaveLength(1)
  })

  it('erkennt die unerreichbare Datenbank an genau derselben Kennung', async () => {
    stubApi({
      '/ready': { status: 503, body: { status: 'degraded', version: '1', database: 'error' } },
    })

    const { phase, check } = useMigration()
    await check()

    expect(phase.value).toBe('databaseDown')
  })

  it('fragt einen anlaufenden Betrieb noch einmal', async () => {
    vi.useFakeTimers()
    const routes: Record<string, { status?: number; body: unknown }> = {
      '/ready': { status: 503, body: { status: 'starting', version: '1', database: 'ok' } },
      '/migration/report': { body: NO_REPORT },
    }
    stubApi(routes)

    const { phase, check } = useMigration()
    await check()
    expect(phase.value).toBe('starting')

    // Der Start ist inzwischen durch — die Wiederholung muss es sehen.
    routes['/ready'] = { body: { status: 'ok', version: '1', database: 'ok' } }
    await vi.runOnlyPendingTimersAsync()

    expect(phase.value).toBe('serving')
  })
})

describe('useMigration.confirm', () => {
  it('führt aus und zeigt den Bericht', async () => {
    stubApi({
      '/migration/confirm': { body: { completed: true, rejected: PREVIEW.rejected } },
    })

    const { phase, report, confirm } = useMigration()
    await confirm()

    expect(phase.value).toBe('done')
    expect(report.value?.rejected[0].symbol).toBe('VTI')
  })

  /*
   * Der Fall aus Übergabe 2A: Der Umzug ist festgeschrieben, der Betrieb nicht
   * angelaufen. Ihn hier als gescheitert darzustellen wäre die entgegengesetzte
   * Lüge — die Daten *sind* umgezogen, und der Bericht muss trotzdem kommen.
   */
  it('meldet den gescheiterten Betriebsstart, ohne den Umzug zu bestreiten', async () => {
    stubApi({
      '/migration/confirm': { status: 503, body: 'startup_failed' },
      '/migration/report': { body: { completed: true, rejected: PREVIEW.rejected } },
    })

    const { phase, report, confirm } = useMigration()
    await confirm()

    expect(phase.value).toBe('startupFailed')
    expect(report.value?.rejected).toHaveLength(1)
  })

  it('fragt bei 409 neu nach, statt zu raten', async () => {
    stubApi({
      '/migration/confirm': { status: 409, body: 'läuft bereits' },
      '/ready': { body: { status: 'ok', version: '1', database: 'ok' } },
      '/migration/report': { body: { completed: true, rejected: [] } },
    })

    const { phase, confirm } = useMigration()
    await confirm()

    expect(phase.value).toBe('serving')
  })
})
