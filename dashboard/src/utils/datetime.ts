/** Ein reines Kalenderdatum wie `2026-10-01`, ohne Uhrzeit und Zeitzone. */
const dateOnlyPattern = /^(\d{4})-(\d{2})-(\d{2})$/

/**
 * Formatiert einen ISO-Zeitstempel lokalisiert (Datum + Uhrzeit).
 *
 * Ein reines Datum (`2026-10-01`, etwa der Tag eines Schlusskurses) erscheint
 * nur als Datum. `new Date('2026-10-01')` läse es als Mitternacht UTC und
 * zeigte je nach Zeitzone eine erfundene Uhrzeit oder sogar den Vortag.
 *
 * @param iso - ISO-8601-Zeitstempel (z.B. aus `quote_time`) oder reines Datum.
 * @param locale - aktive Locale (z.B. 'de' | 'en').
 * @returns Lokalisiertes „13. Aug. 2026, 09:41" bzw. „01.10.2026"; bei
 *   ungültigem Input der Rohwert.
 */
export function formatDateTime(iso: string, locale: string): string {
  const dateOnly = dateOnlyPattern.exec(iso)
  if (dateOnly) {
    const [, year, month, day] = dateOnly
    const date = new Date(Number(year), Number(month) - 1, Number(day))
    return new Intl.DateTimeFormat(locale, { dateStyle: 'medium' }).format(date)
  }
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  return new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}
