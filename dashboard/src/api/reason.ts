import { i18n } from '../i18n'

import { ApiError } from './client'

/**
 * Wo ein Satz zu einer Fehlerkennung stehen kann — in dieser Reihenfolge.
 *
 * Ein aufnahmespezifischer Satz unter `errors.reason` gewinnt vor einem
 * gemeinsam mit dem Migrationsbericht verwendeten Satz.
 */
const ERROR_REASON_CATALOGS = ['errors.reason', 'migration.reason'] as const

/**
 * Der Satz zu einer Kennung des Backends, in der Sprache der Oberfläche.
 *
 * **Auch das Unbekannte wird übersetzt.** Die rohe Kennung stehen zu lassen
 * ist ein Bezeichner für Maschinen und in keiner Sprache ein Satz. Der
 * Rückfall sagt ehrlich, dass die Oberfläche sie nicht kennt, und nennt sie —
 * damit sie in einer Meldung trotzdem weiterhilft.
 *
 * @param code - Kennung, wie das Backend sie liefert.
 * @param params - Werte für den Satz.
 * @param catalogs - Katalogpräfixe in Vorrangfolge, etwa `['migration.reason']`.
 * @param unknownKey - Satz mit `{code}` für eine Kennung, die kein Katalog kennt.
 */
export function reasonText(
  code: string,
  params: Record<string, unknown>,
  catalogs: readonly string[],
  unknownKey: string,
): string {
  for (const catalog of catalogs) {
    const key = `${catalog}.${code}`
    // `te` fragt, ob der Katalog die Kennung kennt. Ohne diese Frage lieferte
    // vue-i18n den Schlüssel selbst zurück — der Benutzer läse dann
    // `errors.reason.instrument_not_found`, was schlimmer ist als nichts.
    if (i18n.global.te(key)) return i18n.global.t(key, params)
  }
  return i18n.global.t(unknownKey, { code })
}

/**
 * Der **Grund** hinter einem fehlgeschlagenen Aufruf, in der Sprache des UI.
 *
 * Übersetzt wird die Kennung, nicht der Backendtext. Ohne auswertbare Kennung
 * bleibt die übersetzte Aktionsmeldung stehen; freier Text kann etwa eine
 * Proxy-Fehlerseite statt eines fachlichen Grundes sein.
 *
 * @param error - Was der Aufruf geworfen hat.
 * @param fieldLabels - Angezeigte Beschriftung je Feldname. Nennt die Kennung
 *   ein Feld (`params.field`, etwa `fund_domicile`), steht im Satz die
 *   Beschriftung statt des Namens.
 * @returns Der Grund, oder `null` wenn sich keiner benennen lässt.
 */
export function reasonOf(error: unknown, fieldLabels?: Record<string, string>): string | null {
  if (!(error instanceof ApiError)) return null

  const body = parse(error.detail)
  if (body === null) return null

  if (typeof body.code === 'string') {
    const params: Record<string, unknown> = isRecord(body.params) ? { ...body.params } : {}
    const label = typeof params.field === 'string' ? fieldLabels?.[params.field] : undefined
    if (label) params.field = label
    return errorDetailText({ code: body.code, params })
  }

  return null
}

/**
 * Der Satz zu einer Kennung, die nicht als Fehler, sondern in einer Antwort
 * steht — etwa `restore_error` in `GET /backups` (T-148).
 *
 * @param detail - `{code, params}` aus dem Backend.
 */
export function errorDetailText(detail: { code: string; params: Record<string, unknown> }): string {
  return reasonText(detail.code, detail.params, ERROR_REASON_CATALOGS, 'errors.reason.unknown')
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
 * @param fieldLabels - Wie bei `reasonOf`.
 */
export function describeFailure(
  message: string,
  error: unknown,
  fieldLabels?: Record<string, string>,
): string {
  const reason = reasonOf(error, fieldLabels)
  return reason ? `${message} — ${reason}` : message
}
