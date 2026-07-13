export interface InstrumentSummary {
  isin: string | null
  symbol: string
  exchange: string | null
  name: string | null
  type: string | null
  currency: string | null
  provider: string | null
  ter: number | null
  replication: string | null
  fund_size: number | null
  meta_fetched_at: string | null
  latest_price: number | null
  latest_quote_time: string | null
  latest_currency: string | null
  latest_fetched_at: string | null
  history_count: number
}

export interface EnvInfo {
  version: string
  database_path: string
  cache_ttl_hours: number
  refresh_interval_hours: number
  metadata_ttl_days: number
  default_exchange: string
  host: string
  port: number
  api_key_set: boolean
  openfigi_key_set: boolean
  extraetf_etf_url: string
  extraetf_stock_url: string
  yahoo_url: string
}

export interface QuotePoint {
  price: number
  quote_time: string
  volume: number | null
  currency: string | null
  fetched_at: string
}

export interface DailyPoint {
  date: string
  close: number
  currency: string | null
}

export interface RefreshResult {
  total: number
  refreshed: number
}

/** Aktive Unterseite/Tab des Dashboards. */
export type TabKey = 'assets' | 'exchanges' | 'environment' | 'links' | 'themes'

/** Ausgewählter Chart-Zeitraum. 'intraday' = Tagesverlauf (Ticks), Rest = EOD. */
export type RangeKey = 'intraday' | '1w' | '1m' | '3m' | '1y' | 'max'
