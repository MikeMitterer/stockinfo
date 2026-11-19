import type { ExchangeSupport } from '../types'

/** Name der mitgelieferten Quelle, die Kurse aus einer YAML-Datei liest. */
export const YAML_FILE_SOURCE = 'yaml-file'

/** Nur aktive Kursquellen machen eine Börse für Kursabrufe verfügbar. */
export function availableQuoteSources(entries: ExchangeSupport[] = []): ExchangeSupport[] {
  return entries.filter(entry => entry.role === 'quotes' && entry.usable)
}
