/** Basis-URL der StockInfo-API (aus VITE_API_BASE_URL, Default localhost:8000). */
export const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
