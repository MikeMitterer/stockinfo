import type { InstrumentSummary } from '../../src/types'

/**
 * Ein Instrument für Tests — an **einer** Stelle.
 *
 * Vorher stand derselbe Satz Felder in drei Spec-Dateien. Beim Nachtragen der
 * manuellen Kennzahlen (T-09) mussten alle drei angefasst werden, obwohl keine
 * davon etwas mit Overrides zu tun hat. Genau das soll hier nicht wieder
 * passieren: Ein neues Feld kommt hier hinein, und die Tests laufen weiter.
 *
 * `isin` darf einzeln überschrieben werden und wandert hier in die Identität —
 * bequemer als in jedem Test die ganze Form zu nennen, und die Tests, denen die
 * Form egal ist, müssen sie nicht kennen. Wer eine **andere** Form braucht,
 * übergibt `identity` ausdrücklich; das gewinnt.
 *
 * @param overrides Felder, auf die es im jeweiligen Test ankommt.
 */
export function makeInstrument(
  overrides: Partial<InstrumentSummary> & { isin?: string | null } = {},
): InstrumentSummary {
  const { isin, ...rest } = overrides
  // **`in` statt `??`**: `isin: null` ist die Aussage „dieses Papier hat keine",
  // und genau darauf prüft der ISIN-Editor. Ein `??` hätte sie als „nicht
  // angegeben" gelesen und den Vorgabewert eingesetzt — der Test wäre grün
  // geworden, ohne den Fall je zu erzeugen.
  const identityIsin = 'isin' in overrides ? (isin ?? null) : 'US0378331005'
  return {
    identity: { kind: 'listed', ticker: 'APC', mic: 'XETR', isin: identityIsin },
    symbol: 'APC.DE',
    listing_id: '00000000-0000-4000-8000-000000000001',
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
    source: 'yfinance',
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
    ...rest,
  }
}
