/** Zwei feste Nachkommastellen — für Kurse, Geldbeträge und Kennzahlen. */
export const TWO_DECIMALS: Intl.NumberFormatOptions = {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
}

/**
 * Formatiert eine Zahl mit zwei Nachkommastellen in der Sprache der Oberfläche.
 *
 * @param value - Die Zahl.
 * @param locale - Sprache der Oberfläche, etwa `de` oder `en`.
 * @returns Die Zahl mit Tausender- und Dezimaltrennzeichen dieser Sprache.
 */
export function formatTwoDecimals(value: number, locale: string): string {
  return value.toLocaleString(locale, TWO_DECIMALS)
}
