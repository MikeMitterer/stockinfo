import { i18n } from '../i18n'

import { ApiError } from './client'

/**
 * Wo ein Satz zu einer Kennung stehen kann — in dieser Reihenfolge.
 *
 * Ein aufnahmespezifischer Satz unter `errors.reason` gewinnt vor einem
 * gemeinsam mit dem Migrationsbericht verwendeten Satz.
 *
 * @param code - Strukturierte Fehlerkennung des Backends.
 * @returns Übersetzungsschlüssel in fachlicher Vorrangfolge.
 */
const reasonKeys = (code: string): readonly string[] => [
  `errors.reason.${code}`,
  `migration.reason.${code}`,
]

/**
 * Der **Grund** hinter einem fehlgeschlagenen Aufruf, in der Sprache des UI.
 *
 * Übersetzt wird die Kennung, nicht der Backendtext. Ohne auswertbare Kennung
 * bleibt die übersetzte Aktionsmeldung stehen; freier Text kann etwa eine
 * Proxy-Fehlerseite statt eines fachlichen Grundes sein.
 *
 * @param error - Was der Aufruf geworfen hat.
 * @returns Der Grund, oder `null` wenn sich keiner benennen lässt.
 */
export function reasonOf(error: unknown): string | null {
  if (!(error instanceof ApiError)) return null

  const body = parse(error.detail)
  if (body === null) return null

  if (typeof body.code === 'string') {
    const params = isRecord(body.params) ? body.params : {}
    for (const key of reasonKeys(body.code)) {
      // `te` fragt, ob der Katalog die Kennung kennt. Ohne diese Frage lieferte
      // vue-i18n den Schlüssel selbst zurück — der Benutzer läse dann
      // `errors.reason.instrument_not_found`, was schlimmer ist als nichts.
      if (i18n.global.te(key)) return i18n.global.t(key, params)
    }
    // **Auch das Unbekannte wird übersetzt.** Die rohe Kennung stehen zu
    // lassen war der erste Anlauf; sie ist ein Bezeichner für Maschinen und in
    // keiner Sprache ein Satz. Der Rückfall sagt ehrlich, dass die Oberfläche
    // sie nicht kennt, und nennt sie — damit sie in einer Fehlermeldung
    // trotzdem weiterhilft.
    return i18n.global.t('errors.reason.unknown', { code: body.code })
  }

  return null
}

/** Der Körper als Objekt — oder `null`, wenn es keiner ist. */
function parse(raw: string): Record<string, unknown> | null {
  try {
    const value: unknown = JSON.parse(raw)
    return isRecord(value) ? value : null
  } catch {
    return null
  }
}

function isRecord(value: unknown): value is Record<string, string> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

/**
 * Kategorie und Grund zu einer Meldung verbinden.
 *
 * @param message - Was schiefging („Hinzufügen fehlgeschlagen").
 * @param error - Der geworfene Fehler.
 */
export function describeFailure(message: string, error: unknown): string {
  const reason = reasonOf(error)
  return reason ? `${message} — ${reason}` : message
}
