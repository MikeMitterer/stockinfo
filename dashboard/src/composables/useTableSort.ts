import { ref, type Ref } from 'vue'

import { i18n } from '../i18n'
import type { InstrumentSummary } from '../types'

/** Sortierbare Spalten der Assets-Tabelle (Datenspalten, keine Aktionen). */
export const SORT_KEYS = [
  'symbol',
  'isin',
  'name',
  'type',
  'latest_price',
  'ter',
  'volatility',
  'accumulating',
  'history_count',
] as const
export type SortKey = (typeof SORT_KEYS)[number]
export type SortDirection = 'asc' | 'desc'

const STORAGE_KEY = 'stockinfo-sort'

// Modul-Level-Singleton — Tabelle und Persistenz teilen sich den Zustand.
const sortKey = ref<SortKey | null>(null)
const direction = ref<SortDirection>('asc')

/** Persistiert den aktuellen Sortierzustand (aus = Eintrag entfernen). */
function persist(): void {
  try {
    if (sortKey.value === null) {
      window.localStorage.removeItem(STORAGE_KEY)
    } else {
      window.localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ key: sortKey.value, dir: direction.value }),
      )
    }
  } catch {
    // localStorage nicht verfügbar — Sortierung gilt nur zur Laufzeit.
  }
}

/**
 * Vergleicht zwei Instrumente in einer Spalte — null/undefined immer ans Ende,
 * Strings locale-korrekt (aktive i18n-Sprache), Zahlen/Booleans numerisch.
 * Liefert 0/±1 für null-Fälle unabhängig von der Richtung (Aufrufer dreht nur
 * den Nicht-null-Vergleich).
 */
function compareValues(a: InstrumentSummary, b: InstrumentSummary, key: SortKey): number | null {
  const aValue = a[key]
  const bValue = b[key]
  if (aValue === null || aValue === undefined) {
    return bValue === null || bValue === undefined ? 0 : null
  }
  if (bValue === null || bValue === undefined) return null
  if (typeof aValue === 'string' && typeof bValue === 'string') {
    return aValue.localeCompare(bValue, i18n.global.locale.value)
  }
  return Number(aValue) - Number(bValue)
}

/** Spalten-Sortierung der Assets-Tabelle: Zustand, Toggle, Sortieren, Persistenz. */
export function useTableSort(): {
  sortKey: Ref<SortKey | null>
  direction: Ref<SortDirection>
  toggle: (key: SortKey) => void
  sort: (items: InstrumentSummary[]) => InstrumentSummary[]
  init: () => void
} {
  /** Stellt den persistierten Sortierzustand wieder her (ungültig → Default). */
  function init(): void {
    let raw: string | null = null
    try {
      raw = window.localStorage.getItem(STORAGE_KEY)
    } catch {
      raw = null
    }
    if (!raw) return
    try {
      const saved: unknown = JSON.parse(raw)
      const candidate = saved as { key?: unknown; dir?: unknown }
      if (
        SORT_KEYS.some((key) => key === candidate.key) &&
        (candidate.dir === 'asc' || candidate.dir === 'desc')
      ) {
        sortKey.value = candidate.key as SortKey
        direction.value = candidate.dir
      }
    } catch {
      // kaputter Eintrag — Standard-Reihenfolge behalten
    }
  }

  /** Schaltet die Sortierung einer Spalte durch: auf → ab → aus. */
  function toggle(key: SortKey): void {
    if (sortKey.value !== key) {
      sortKey.value = key
      direction.value = 'asc'
    } else if (direction.value === 'asc') {
      direction.value = 'desc'
    } else {
      sortKey.value = null
      direction.value = 'asc'
    }
    persist()
  }

  /** Sortierte Kopie der Instrumente; ohne aktive Sortierung unverändert. */
  function sort(items: InstrumentSummary[]): InstrumentSummary[] {
    const key = sortKey.value
    if (key === null) return items
    const factor = direction.value === 'asc' ? 1 : -1
    return [...items].sort((a, b) => {
      const base = compareValues(a, b, key)
      if (base === null) {
        // genau ein Wert ist null → dieser ans Ende, richtungsunabhängig
        return a[key] === null || a[key] === undefined ? 1 : -1
      }
      return factor * base
    })
  }

  return { sortKey, direction, toggle, sort, init }
}
