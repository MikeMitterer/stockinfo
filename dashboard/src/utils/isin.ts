/**
 * Länderpräfixe europäischer UCITS-Fondsdomizile (EU + EWR + CH/UK).
 *
 * Spiegel der Allow-List aus `is_european_isin` im Backend
 * (`app/providers/justetf_provider.py`) — justETF liefert für alle anderen
 * ISINs garantiert nichts, das Backend scraped dort erst gar nicht. Diese
 * kleine Fassung dient nur der Erklärung im Detailbereich (Task 8), nicht der
 * Entscheidung, ob gescraped wird — die bleibt allein im Backend.
 */
const EUROPEAN_DOMICILES = new Set([
  // EU
  'AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR', 'DE', 'GR',
  'HU', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL', 'PL', 'PT', 'RO', 'SK',
  'SI', 'ES', 'SE',
  // EWR
  'IS', 'LI', 'NO',
  // Schweiz, UK
  'CH', 'GB',
])

/**
 * Prüft anhand des ISIN-Länderpräfix, ob ein europäisches UCITS-Domizil vorliegt.
 *
 * @param isin - ISIN des Wertpapiers, oder `null` ohne bekannte ISIN.
 * @returns `true` bei europäischem Domizil (EU/EWR/CH/UK), sonst `false`.
 */
export function isEuropeanIsin(isin: string | null): boolean {
  if (!isin || isin.length < 2) return false
  return EUROPEAN_DOMICILES.has(isin.slice(0, 2).toUpperCase())
}
