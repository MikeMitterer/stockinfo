import type { InstrumentSummary } from '../types'

/**
 * Anzeige der Fondsgröße in den flachen Feldern (`fund_size`, `manual_fund_size`).
 *
 * Die Fondsgröße steht immer in Millionen. Ihre Währung trägt der
 * `details`-Eintrag: Quellenwerte kommen in EUR, ein manueller Wert in der
 * Währung, mit der er eingegeben wurde. Ohne `details` (älterer Weg) gilt EUR,
 * wie bei justETF. Der Detailbereich formatiert in `DetailEditor.vue` über
 * denselben Katalogtext.
 */
export const defaultFundSizeCurrency = 'EUR'

type Translate = (key: string, values: Record<string, unknown>) => string

/** Welcher Wert gemeint ist: der wirksame oder der von Hand eingetragene. */
export type FundSizeValue = 'effective' | 'manual'

/** Währung der Fondsgröße eines Instruments. */
export function fundSizeCurrency(item: InstrumentSummary, which: FundSizeValue): string {
  const detail = item.details?.fund_size
  const currency = which === 'manual' ? detail?.manual_currency : detail?.currency
  return currency || defaultFundSizeCurrency
}

/** „129.791,00 Mio. EUR" aus einer bereits formatierten Zahl. */
export function fundSizeText(t: Translate, amount: string, currency: string): string {
  return t('details.amountMillions', { amount, currency })
}
