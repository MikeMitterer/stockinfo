import type { ExchangesResponse } from '../types'

/** London notiert in Pence; der Code unterscheidet sich von GBP nur im Kleinbuchstaben. */
export const PENCE_CURRENCY = 'GBp'

/** Notiert eine Börse in Pence statt in Pfund? */
export function isPenceQuoted(currency: string): boolean {
  return currency === PENCE_CURRENCY
}

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
    isPenceQuoted(entry.currency) ? 'GBP' : entry.currency,
  )
  return [...new Set(codes)].sort()
}
