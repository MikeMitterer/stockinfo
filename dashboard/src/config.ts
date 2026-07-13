/** Basis-URL der StockInfo-API.
 *
 * Leer (Default) → relative Aufrufe (`/quote/…`): in Prod same-origin (FastAPI
 * serviert das Dashboard), im Dev leitet der vite-Proxy die API-Präfixe ans
 * Backend weiter. Über `VITE_API_BASE_URL` bei Bedarf überschreibbar.
 */
export const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? ''
