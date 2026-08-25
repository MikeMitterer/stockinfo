import type { ExchangesResponse } from '../types'

/**
 * Leitet die wählbaren FX-Währungen aus der Börsentabelle ab.
 * `GBp` (Londoner Pence) wird zu `GBP` normalisiert; Ergebnis ist eindeutig
 * und alphabetisch sortiert.
 *
 * @param data - Antwort von GET /exchanges (oder null, solange nicht geladen).
 * @returns Sortierte, eindeutige Währungscodes; `[]` ohne Daten.
 */
export function currenciesFromExchanges(data: ExchangesResponse | null): string[] {
  if (!data) return []
  const codes = data.catalog.map((entry) =>
    entry.currency === 'GBp' ? 'GBP' : entry.currency,
  )
  return [...new Set(codes)].sort()
}
