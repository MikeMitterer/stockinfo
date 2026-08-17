import type { ExchangesResponse, InstrumentSummary, OverrideField } from '../types'
import { currenciesFromExchanges } from './currencies'
import { distinctFieldValues } from './suggestions'

/**
 * Baut die Vorschlagslisten für die vier Textfelder der Schublade (Task 8).
 *
 * Einziger Ort, an dem `currenciesFromExchanges()` (Fondswährung) und
 * `distinctFieldValues()` (Anbieter, Replikationsart, Fondsdomizil)
 * zusammengeführt werden — `AppDashboard.vue` ruft das **einmal** auf, nicht
 * jede Zeile für sich. Bei zwanzig Zeilen wäre das sonst zwanzigmal dieselbe
 * Ableitung.
 *
 * @param instruments - Die bereits geladene Instrumentenliste.
 * @param exchanges - Antwort von GET /exchanges (oder `null`, solange nicht geladen).
 * @returns Vorschläge je Textfeld; leere Arrays ohne Daten.
 */
export function buildFieldOptions(
  instruments: InstrumentSummary[],
  exchanges: ExchangesResponse | null,
): Partial<Record<OverrideField, string[]>> {
  return {
    provider: distinctFieldValues(instruments, 'provider'),
    replication: distinctFieldValues(instruments, 'replication'),
    fund_domicile: distinctFieldValues(instruments, 'fund_domicile'),
    fund_currency: currenciesFromExchanges(exchanges),
  }
}
