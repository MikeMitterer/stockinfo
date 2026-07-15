import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { InstrumentSummary } from '../../src/types'

/** Baut ein minimales InstrumentSummary mit überschreibbaren Feldern. */
function item(overrides: Partial<InstrumentSummary>): InstrumentSummary {
  return {
    isin: null,
    symbol: 'SYM',
    exchange: null,
    name: null,
    type: null,
    currency: null,
    provider: null,
    ter: null,
    replication: null,
    fund_size: null,
    volatility: null,
    accumulating: null,
    meta_fetched_at: null,
    latest_price: null,
    latest_quote_time: null,
    latest_currency: null,
    latest_fetched_at: null,
    history_count: 0,
    ...overrides,
  }
}

beforeEach(() => {
  vi.resetModules()
  window.localStorage.clear()
})

describe('useTableSort', () => {
  it('toggle durchläuft auf → ab → aus', async () => {
    const { useTableSort } = await import('../../src/composables/useTableSort')
    const { sortKey, direction, toggle } = useTableSort()

    toggle('symbol')
    expect(sortKey.value).toBe('symbol')
    expect(direction.value).toBe('asc')

    toggle('symbol')
    expect(direction.value).toBe('desc')

    toggle('symbol')
    expect(sortKey.value).toBeNull()
  })

  it('Wechsel auf andere Spalte startet wieder aufsteigend', async () => {
    const { useTableSort } = await import('../../src/composables/useTableSort')
    const { sortKey, direction, toggle } = useTableSort()

    toggle('symbol')
    toggle('symbol')
    toggle('ter')
    expect(sortKey.value).toBe('ter')
    expect(direction.value).toBe('asc')
  })

  it('sortiert Zahlen auf- und absteigend', async () => {
    const { useTableSort } = await import('../../src/composables/useTableSort')
    const { toggle, sort } = useTableSort()
    const items = [item({ symbol: 'A', ter: 0.3 }), item({ symbol: 'B', ter: 0.1 })]

    toggle('ter')
    expect(sort(items).map((entry) => entry.symbol)).toEqual(['B', 'A'])
    toggle('ter')
    expect(sort(items).map((entry) => entry.symbol)).toEqual(['A', 'B'])
  })

  it('sortiert Strings locale-korrekt', async () => {
    const { useTableSort } = await import('../../src/composables/useTableSort')
    const { toggle, sort } = useTableSort()
    const items = [item({ symbol: 'A', name: 'Österreich' }), item({ symbol: 'B', name: 'Polen' })]

    toggle('name')
    // localeCompare: Ö sortiert vor P (naiver Codepoint-Vergleich täte es nicht)
    expect(sort(items).map((entry) => entry.symbol)).toEqual(['A', 'B'])
  })

  it('null-Werte stehen in beiden Richtungen am Ende', async () => {
    const { useTableSort } = await import('../../src/composables/useTableSort')
    const { toggle, sort } = useTableSort()
    const items = [
      item({ symbol: 'NULL', latest_price: null }),
      item({ symbol: 'HIGH', latest_price: 200 }),
      item({ symbol: 'LOW', latest_price: 10 }),
    ]

    toggle('latest_price')
    expect(sort(items).map((entry) => entry.symbol)).toEqual(['LOW', 'HIGH', 'NULL'])
    toggle('latest_price')
    expect(sort(items).map((entry) => entry.symbol)).toEqual(['HIGH', 'LOW', 'NULL'])
  })

  it('ohne aktive Sortierung bleibt die Reihenfolge unverändert', async () => {
    const { useTableSort } = await import('../../src/composables/useTableSort')
    const { sort } = useTableSort()
    const items = [item({ symbol: 'Z' }), item({ symbol: 'A' })]
    expect(sort(items).map((entry) => entry.symbol)).toEqual(['Z', 'A'])
  })

  it('persistiert die Sortierung und stellt sie via init wieder her', async () => {
    const first = await import('../../src/composables/useTableSort')
    const sortA = first.useTableSort()
    sortA.toggle('volatility')
    sortA.toggle('volatility')
    expect(JSON.parse(window.localStorage.getItem('stockinfo-sort') ?? '')).toEqual({
      key: 'volatility',
      dir: 'desc',
    })

    vi.resetModules()
    const second = await import('../../src/composables/useTableSort')
    const sortB = second.useTableSort()
    sortB.init()
    expect(sortB.sortKey.value).toBe('volatility')
    expect(sortB.direction.value).toBe('desc')
  })

  it('ignoriert ungültige Werte im localStorage', async () => {
    window.localStorage.setItem('stockinfo-sort', '{"key":"kaputt","dir":"sideways"}')
    const { useTableSort } = await import('../../src/composables/useTableSort')
    const { sortKey, init } = useTableSort()
    init()
    expect(sortKey.value).toBeNull()
  })
})
