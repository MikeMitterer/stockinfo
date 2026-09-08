import type { ExchangeSupport } from '../types'

/** Nur aktive Kursquellen machen eine Börse für Kursabrufe verfügbar. */
export function availableQuoteSources(entries: ExchangeSupport[] = []): ExchangeSupport[] {
  return entries.filter(entry => entry.role === 'quotes' && entry.usable)
}
