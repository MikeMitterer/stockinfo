/**
 * Formatiert einen ISO-Zeitstempel lokalisiert (Datum + Uhrzeit).
 *
 * @param iso - ISO-8601-Zeitstempel (z.B. aus `quote_time`).
 * @param locale - aktive Locale (z.B. 'de' | 'en').
 * @returns Lokalisiertes „13. Aug. 2026, 09:41"; bei ungültigem Input der Rohwert.
 */
export function formatDateTime(iso: string, locale: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  return new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}
