import type { InstrumentSummary } from '../types'

/** Textfelder, für die es keine feste Werteliste gibt (T-15). */
export type SuggestibleField = 'provider' | 'replication' | 'fund_domicile'

/**
 * Eindeutige, sortierte Werte eines Textfelds über alle geladenen Instrumente.
 *
 * Speist die Auswahl-mit-freier-Eingabe im `MetricEditor` (T-15): Anbieter,
 * Replikationsart und Fondsdomizil haben keine feste Liste — anders als die
 * Fondswährung, für die es bereits `currenciesFromExchanges()` gibt. Statt
 * eine zweite, redaktionell gepflegte Liste zu erfinden, wächst diese Auswahl
 * mit dem eigenen Bestand: Was schon einmal eingetragen wurde (ob von der
 * Quelle oder von Hand — `InstrumentSummary` trägt hier bereits den
 * wirksamen Wert), taucht beim nächsten Papier als Vorschlag auf.
 *
 * @param instruments Die bereits geladene Instrumentenliste (Tabelle).
 * @param field Eines der drei Textfelder ohne feste Werteliste.
 * @returns Sortierte, eindeutige Werte; `[]` ohne Treffer.
 */
export function distinctFieldValues(
  instruments: InstrumentSummary[],
  field: SuggestibleField,
): string[] {
  const values = instruments
    .map((instrument) => instrument[field])
    .filter((value): value is string => value !== null && value !== '')
  return [...new Set(values)].sort()
}
