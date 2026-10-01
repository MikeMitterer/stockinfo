/**
 * Anzeige der Fondsgröße in den flachen Feldern (`fund_size`, `manual_fund_size`).
 *
 * Die flachen Felder tragen keine eigene Währung. Laut Vertrag stehen sie in
 * Millionen Euro, so wie justETF sie liefert. Der Detailbereich mit eigener
 * Währung formatiert in `DetailEditor.vue` über denselben Katalogtext.
 */
export const FUND_SIZE_CURRENCY = 'EUR'

type Translate = (key: string, values: Record<string, unknown>) => string

/** „129.791,00 Mio. EUR" aus einer bereits formatierten Zahl. */
export function fundSizeText(t: Translate, amount: string): string {
  return t('details.amountMillions', { amount, currency: FUND_SIZE_CURRENCY })
}
