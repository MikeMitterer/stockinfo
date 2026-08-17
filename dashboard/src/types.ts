/** Ein Instrument, identifiziert per ISIN (falls vorhanden) oder Symbol. */
export interface InstrumentRef {
  isin: string | null
  symbol: string
}

/**
 * Kennzahlen, die sich von Hand nachtragen lassen (T-09, erweitert um die
 * ETF-Extras aus T-15).
 *
 * Dieselbe Menge wie `OVERRIDE_FIELDS` im Backend (`app/models.py`) — genau
 * das, was justETFs `get_etf_overview` beisteuert: Wo die Quelle nichts hat,
 * springt der Mensch ein.
 */
export type OverrideField =
  | 'ter'
  | 'volatility'
  | 'accumulating'
  | 'provider'
  | 'replication'
  | 'fund_size'
  | 'fund_domicile'
  | 'fund_currency'

export const OVERRIDE_FIELDS: OverrideField[] = [
  'ter',
  'volatility',
  'accumulating',
  'provider',
  'replication',
  'fund_size',
  'fund_domicile',
  'fund_currency',
]

/**
 * Von Hand nachgetragene Kennzahlen.
 *
 * `null` heißt „nicht gepflegt" — und beim Schreiben „löschen": Es geht immer
 * der vollständige Satz zum Backend.
 */
export interface InstrumentOverrides {
  ter: number | null
  volatility: number | null
  accumulating: boolean | null
  provider: string | null
  replication: string | null
  fund_size: number | null
  fund_domicile: string | null
  fund_currency: string | null
}

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
  fund_domicile: string | null
  fund_currency: string | null
  volatility: number | null
  accumulating: boolean | null
  /** Herkunft der Metadaten: `yfinance` oder `yfinance+justetf`. */
  source: string | null
  meta_fetched_at: string | null
  latest_price: number | null
  latest_quote_time: string | null
  latest_currency: string | null
  latest_fetched_at: string | null
  history_count: number

  /*
   * `ter`, `volatility` und `accumulating` oben sind die **wirksamen** Werte —
   * die Vorrang-Regel wendet das Backend an. Hier stehen die manuellen Werte
   * roh, damit die Oberfläche sie im Editor zeigen und im Hinweis nennen kann.
   */
  manual_ter: number | null
  manual_volatility: number | null
  manual_accumulating: boolean | null
  manual_provider: string | null
  manual_replication: string | null
  manual_fund_size: number | null
  manual_fund_domicile: string | null
  manual_fund_currency: string | null
  /** Kennzahlen, deren angezeigter Wert gerade von Hand kommt. */
  manual_fields: OverrideField[]
  /** Kennzahlen mit manuellem Wert, den die Quelle gerade verdeckt. */
  shadowed_fields: OverrideField[]
}

export interface EnvInfo {
  version: string
  database_path: string
  cache_ttl_hours: number
  refresh_interval_hours: number
  metadata_ttl_days: number
  default_exchange: string
  strict_exchange: boolean
  host: string
  port: number
  openfigi_key_set: boolean
  extraetf_etf_url: string
  extraetf_stock_url: string
  yahoo_url: string
}

/** Eine weltweit unterstützte Börse mit Yahoo-Suffix und Notierungswährung. */
export interface ExchangeInfo {
  mic: string
  suffix: string
  name: string
  region: string
  currency: string
}

/** Antwort von GET /exchanges: die volle Börsentabelle plus konfigurierte Default-Börse. */
export interface ExchangesResponse {
  default_exchange: string
  exchanges: ExchangeInfo[]
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

/** Ein Wechselkurs: 1 base = rate quote. */
export interface FxRate {
  base: string
  quote: string
  rate: number
  quote_time: string
  source: string | null
  cached: boolean
  stale: boolean
  fetched_at: string
}

/** Aktive Unterseite/Tab des Dashboards. */
export type TabKey = 'assets' | 'exchanges' | 'analysis' | 'fx' | 'settings'

/** Reiter innerhalb der Einstellungsseite (adressierbar via #/settings?tab=…). */
export type SettingsTab = 'appearance' | 'language' | 'links' | 'environment'

/** Bekannte Icon-Namen der Navigation (deckungsgleich mit den Tabs). */
export type NavIconName = TabKey

/** Ausgewählter Chart-Zeitraum. 'intraday' = Tagesverlauf (Ticks), Rest = EOD. */
export type RangeKey = 'intraday' | '1w' | '1m' | '3m' | '1y' | 'max'

/** Eine einzelne Stufe der On-Demand-Analyse (z.B. Kurs, Historie, Metadaten). */
export interface AnalyzeStage {
  stage: string
  seconds: number
  status: string
  detail: string | null
}

/** Ergebnis einer On-Demand-Stage-Analyse für ein Instrument. */
export interface AnalyzeResult {
  symbol: string
  isin: string | null
  total: number
  stages: AnalyzeStage[]
}
