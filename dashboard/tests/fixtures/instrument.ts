import type { InstrumentSummary } from '../../src/types'

/**
 * Ein Instrument für Tests — an **einer** Stelle.
 *
 * Vorher stand derselbe Satz Felder in drei Spec-Dateien. Beim Nachtragen der
 * manuellen Kennzahlen (T-09) mussten alle drei angefasst werden, obwohl keine
 * davon etwas mit Overrides zu tun hat. Genau das soll hier nicht wieder
 * passieren: Ein neues Feld kommt hier hinein, und die Tests laufen weiter.
 *
 * @param overrides Felder, auf die es im jeweiligen Test ankommt.
 */
export function makeInstrument(overrides: Partial<InstrumentSummary> = {}): InstrumentSummary {
  return {
    isin: 'US0378331005',
    symbol: 'APC.DE',
    exchange: 'XETR',
    name: 'Apple Inc.',
    type: 'stock',
    currency: 'EUR',
    provider: null,
    ter: null,
    replication: null,
    fund_size: null,
    fund_domicile: null,
    fund_currency: null,
    volatility: 25.8,
    accumulating: null,
    meta_fetched_at: null,
    latest_price: 265,
    latest_quote_time: null,
    latest_currency: 'EUR',
    latest_fetched_at: null,
    history_count: 2,
    manual_ter: null,
    manual_volatility: null,
    manual_accumulating: null,
    manual_provider: null,
    manual_replication: null,
    manual_fund_size: null,
    manual_fund_domicile: null,
    manual_fund_currency: null,
    manual_fields: [],
    shadowed_fields: [],
    ...overrides,
  }
}
