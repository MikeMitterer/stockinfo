import type { InstrumentRef } from '../types'

/** Prüft, ob ein String das ISIN-Format hat (2 Buchstaben, 9 alphanum., 1 Ziffer). */
export function isIsin(value: string): boolean {
  return /^[A-Z]{2}[A-Z0-9]{9}[0-9]$/.test(value)
}

/**
 * Baut einen API-Pfad für ein Instrument — per ISIN oder (ohne ISIN) per Symbol.
 * Beide Kennungen werden URL-enkodiert.
 *
 * @param prefix - Pfad-Präfix, z.B. '/quote' oder '/refresh'
 * @param ref - Instrument mit ISIN und/oder Symbol
 * @param suffix - Optionaler Pfad-/Query-Anhang, z.B. '/history?limit=500'
 * @returns Pfad der Form `{prefix}/{isin}{suffix}` bzw. `{prefix}/by-symbol/{symbol}{suffix}`
 */
export function instrumentPath(prefix: string, ref: InstrumentRef, suffix = ''): string {
  const identifier = ref.isin
    ? `/${encodeURIComponent(ref.isin)}`
    : `/by-symbol/${encodeURIComponent(ref.symbol)}`
  return `${prefix}${identifier}${suffix}`
}

/**
 * Baut den /quote-Pfad eines Instruments — ISIN als Pfadsegment,
 * Symbol (ohne ISIN) als Query-Parameter.
 *
 * @param ref - Instrument mit ISIN und/oder Symbol
 * @returns `/quote/{isin}` bzw. `/quote?symbol={symbol}`
 */
export function quotePath(ref: InstrumentRef): string {
  return ref.isin
    ? `/quote/${encodeURIComponent(ref.isin)}`
    : `/quote?symbol=${encodeURIComponent(ref.symbol)}`
}

/**
 * Baut den /analyze-Pfad — ISIN bevorzugt, sonst Symbol, jeweils als Query.
 *
 * @param ref - Instrument mit ISIN und/oder Symbol
 * @returns `/analyze?isin={isin}` bzw. `/analyze?symbol={symbol}`
 */
export function analyzePath(ref: InstrumentRef): string {
  return ref.isin
    ? `/analyze?isin=${encodeURIComponent(ref.isin)}`
    : `/analyze?symbol=${encodeURIComponent(ref.symbol)}`
}

/**
 * Baut den /fx-Pfad für ein Währungspaar. rate = 1 base in quote.
 *
 * @param base - Ausgangswährung (von)
 * @param quote - Zielwährung (nach)
 */
export function fxPath(base: string, quote: string): string {
  return `/fx?base=${encodeURIComponent(base)}&quote=${encodeURIComponent(quote)}`
}
