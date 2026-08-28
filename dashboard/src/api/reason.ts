import { i18n } from '../i18n'

import { ApiError } from './client'

/**
 * Der **Grund** hinter einem fehlgeschlagenen Aufruf, in der Sprache des UI.
 *
 * Bis T-35 zeigte jeder Fehlschlag nur seine Kategorie — „Hinzufügen
 * fehlgeschlagen". Warum, stand ausschließlich in der Browserkonsole. Für eine
 * unauflösbare ISIN hieß das: Der Benutzer sah, *dass* etwas nicht ging, und
 * hatte keine Möglichkeit zu erfahren, *was*. Genau der Fall, den T-28 Zeile 3
 * mit „die App sagt das verständlich" meint.
 *
 * **Übersetzt wird die Kennung, nicht der Backendtext.** `ErrorDetail` sagt
 * das ausdrücklich zu: Der Server nennt `code` und `params`, den Satz bildet
 * das UI — sonst stünde in der englischen Oberfläche ein deutscher Satz.
 *
 * Der Rückfall auf einen mitgelieferten Fließtext ist bewusst und **nicht**
 * der Regelweg: Es gibt im Backend noch Stellen, die `{"detail": "…"}`
 * schicken (die `502`-Fälle nennen dort die ausgefallenen Quellen, was
 * niemand verlieren will). Sie stumm zu verschlucken wäre schlechter, als sie
 * unübersetzt zu zeigen. Wo eine Kennung existiert, gewinnt sie.
 *
 * @param error - Was der Aufruf geworfen hat.
 * @returns Der Grund, oder `null` wenn sich keiner benennen lässt.
 */
export function reasonOf(error: unknown): string | null {
  if (!(error instanceof ApiError)) return null

  const body = parse(error.detail)
  if (body === null) return trimmed(error.detail)

  if (typeof body.code === 'string') {
    const key = `errors.reason.${body.code}`
    const params = isRecord(body.params) ? body.params : {}
    // `te` fragt, ob der Katalog die Kennung kennt. Ohne diese Frage lieferte
    // vue-i18n den Schlüssel selbst zurück — der Benutzer läse dann
    // `errors.reason.instrument_not_found`, was schlimmer ist als nichts.
    if (i18n.global.te(key)) return i18n.global.t(key, params)
    return body.code
  }

  return typeof body.detail === 'string' ? trimmed(body.detail) : null
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

/** Leerer Text ist kein Grund — er erzeugte sonst ein einsames Trennzeichen. */
function trimmed(text: string): string | null {
  const value = text.trim()
  return value.length > 0 ? value : null
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
