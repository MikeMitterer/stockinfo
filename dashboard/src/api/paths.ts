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
  return ref.isin
    ? `${prefix}/${encodeURIComponent(ref.isin)}${suffix}`
    : symbolPath(prefix, ref.symbol, suffix)
}

/**
 * Baut einen API-Pfad über das Symbol, auch wenn das Instrument eine ISIN hat.
 *
 * @param prefix - Pfad-Präfix, z.B. '/instruments'
 * @param symbol - Symbol des Instruments
 * @param suffix - Optionaler Pfad-Anhang, z.B. '/isin'
 * @returns `{prefix}/by-symbol/{symbol}{suffix}`
 */
export function symbolPath(prefix: string, symbol: string, suffix = ''): string {
  return `${prefix}/by-symbol/${encodeURIComponent(symbol)}${suffix}`
}

/**
 * Baut einen API-Pfad über die Listing-Kennung.
 *
 * @param prefix - Pfad-Präfix, z.B. '/instruments'
 * @param listingId - Stabile Kennung des Listings
 * @param suffix - Optionaler Pfad-Anhang, z.B. '/details'
 * @returns `{prefix}/by-id/{listingId}{suffix}`
 */
export function listingPath(prefix: string, listingId: string, suffix = ''): string {
  return `${prefix}/by-id/${encodeURIComponent(listingId)}${suffix}`
}

/**
 * Baut den Pfad, der eine Sicherung zurückspielt.
 *
 * @param name - Dateiname der Sicherung
 * @param force - Auch eine unpassende Sicherung zurückspielen
 * @returns `/backups/{name}/restore`, mit `?force=true` bei `force`
 */
export function backupRestorePath(name: string, force: boolean): string {
  return `/backups/${encodeURIComponent(name)}/restore${force ? '?force=true' : ''}`
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
