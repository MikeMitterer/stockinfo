/** Basis-URL der StockInfo-API.
 *
 * Leer (Default) → relative Aufrufe (`/quote/…`): in Prod same-origin (FastAPI
 * serviert das Dashboard), im Dev leitet der vite-Proxy die API-Präfixe ans
 * Backend weiter. Über `VITE_API_BASE_URL` bei Bedarf überschreibbar.
 */
export const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? ''

/** Projekt und Anleitung für zusätzliche Plugin-Handelsplätze. */
export const REPOSITORY_URL = 'https://github.com/MikeMitterer/stockinfo'
export const PLUGIN_AUTHORS_URL = `${REPOSITORY_URL}/blob/master/docs/plugin-authors.md`
