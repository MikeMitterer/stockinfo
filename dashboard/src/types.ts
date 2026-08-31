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
export const OVERRIDE_FIELDS = [
  'ter',
  'volatility',
  'accumulating',
  'provider',
  'replication',
  'fund_size',
  'fund_domicile',
  'fund_currency',
] as const

/**
 * Abgeleitet aus der Liste, nicht daneben geschrieben.
 *
 * Beides stand hier bis zur Gesamtprüfung nebeneinander — einmal als Union,
 * einmal als Array, acht Namen doppelt. Eine neunte Kennzahl hätte an beiden
 * Stellen nachgetragen werden müssen, und wer nur eine anfasst, merkt davon
 * nichts: Die Union allein erweitern lässt das Feld aus jeder Schleife fallen,
 * das Array allein erweitern lässt es nicht durch den Typcheck.
 */
export type OverrideField = (typeof OVERRIDE_FIELDS)[number]

/**
 * Von Hand nachgetragene Kennzahlen.
 *
 * `null` heißt „nicht gepflegt" — und beim Schreiben „löschen": Es geht immer
 * der vollständige Satz zum Backend.
 *
 * Die acht Namen standen hier ein drittes Mal (nach Union und Array). Jetzt
 * bilden sie sich aus `OVERRIDE_FIELDS`, und die Werttypen kommen von den
 * `manual_*`-Feldern in `InstrumentSummary` — Editor und Payload können sich
 * über den Typ einer Kennzahl damit gar nicht mehr uneinig sein.
 *
 * Der Nutzen zeigt sich bei einer neunten Kennzahl: Sie kommt in
 * `OVERRIDE_FIELDS` dazu, wächst hier von selbst mit, und `vue-tsc` meldet
 * anschließend jede Stelle, die den Satz aufbaut, ohne sie mitzuschicken.
 */
export type InstrumentOverrides = {
  [Field in OverrideField]: InstrumentSummary[`manual_${Field}`]
}

/** Ein Listing an einem echten Handelsplatz — Ticker und MIC. */
export interface ListedIdentity {
  kind: 'listed'
  ticker: string
  mic: string
  isin: string | null
}

/** Ein Währungspaar — die Form für natives Krypto, das nirgends notiert. */
export interface PairIdentity {
  kind: 'pair'
  base: string
  quote_currency: string
}

/** Nur eine ISIN — die Form der OTC-Anleihe ohne Handelsplatz. */
export interface IsinOnlyIdentity {
  kind: 'isin_only'
  isin: string
}

/**
 * Die Identität eines Papiers, unterschieden über `kind` (T-31).
 *
 * **Warum die Oberfläche das sehen muss.** Nicht jedes Papier hat einen
 * Handelsplatz: Eine Coin hat keinen MIC, eine OTC-Anleihe keinen Ticker. Ein
 * flaches `mic: string | null` konnte den Unterschied nicht ausdrücken — ein
 * leeres Feld hieß dort wahlweise „gibt es nicht" oder „wurde nicht
 * ermittelt", und die Anzeige musste raten. Über `kind` weiß sie es.
 */
export type Identity = ListedIdentity | PairIdentity | IsinOnlyIdentity

/**
 * Die ISIN dieser Identität — oder `null`, wenn die Form keine trägt.
 *
 * Ein Währungspaar **hat** keine; `null` erfindet hier nichts. Die Funktion
 * steht neben dem Typ, damit die Fallunterscheidung nicht in jeder Komponente
 * neu entsteht.
 */
export function isinOf(identity: Identity): string | null {
  return identity.kind === 'pair' ? null : identity.isin
}

/**
 * Das **Anbieter-Symbol** dieser Identität — oder `null`, wenn es keins gibt.
 *
 * Das Gegenstück zu `isinOf`, und aus demselben Grund: `instruments.symbol`
 * ist in der Datenbank Pflicht, weil jede Zeile einen Schlüssel braucht. Für
 * ein Papier der Form `isin_only` steht dort deshalb die **ISIN** — ein
 * technischer Platzhalter, kein Symbol, und nichts, was die Oberfläche als
 * eines ausgeben darf.
 */
export function symbolOf(instrument: { identity: Identity; symbol: string }): string | null {
  return instrument.identity.kind === 'isin_only' ? null : instrument.symbol
}

/**
 * Lässt sich für dieses Papier überhaupt eine ISIN nachtragen?
 *
 * **Bei einem Währungspaar nicht** (T-31). Eine Coin hat keine ISIN — das ist
 * keine Lücke, die jemand füllen könnte, sondern eine Eigenschaft der Form.
 * Der Editor dort anzubieten wäre eine Einladung in einen Fehler: Der
 * Speicherversuch liefe gegen den `CHECK` der Datenbank, der für `pair`
 * ausdrücklich `isin IS NULL` verlangt.
 *
 * Ein fehlendes Feld darf nicht wie ein Bearbeitungsfehler aussehen.
 */
export function acceptsIsin(identity: Identity): boolean {
  return identity.kind !== 'pair'
}

/**
 * Ein Instrument als `InstrumentRef` — die schmale Form für die Pfadbildung.
 *
 * `InstrumentRef` bleibt bewusst flach: Sie beantwortet nur „womit spreche ich
 * den Endpunkt an", und dort zählt allein, ob eine ISIN da ist. Diese Funktion
 * ist die eine Stelle, an der aus der Identität die Antwort darauf wird.
 */
export function refOf(instrument: { identity: Identity; symbol: string }): InstrumentRef {
  return { isin: isinOf(instrument.identity), symbol: instrument.symbol }
}

export interface InstrumentSummary {
  identity: Identity
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

/**
 * Ein Glied einer Quellenkette, wie `/sources` es beschreibt.
 *
 * `position` ist der Rang **innerhalb einer Rolle**, 1-basiert — die Kette ist
 * eine Rangfolge und keine Menge. `configured` sagt, ob die Quelle arbeiten
 * kann; eine, die es nicht kann, steht trotzdem in der Liste, damit ein
 * Betreiber sieht, dass er sie konfiguriert hat.
 */
export interface SourceEntry {
  name: string
  role: string
  position: number
  configured: boolean
  reason: string
  cost: string
}

export interface SourcesInfo {
  config_path: string | null
  profile: string | null
  sources: SourceEntry[]
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

/**
 * Woher ein Katalogeintrag stammt — heute immer `core`, ab T-30 auch Plugins.
 *
 * Eine diskriminierte Union, damit `kind` das Narrowing trägt: Core hat keine
 * ID, ein Plugin hat immer eine. Ein Interface mit `id: string | null` konnte
 * beide ungültigen Kombinationen ausdrücken — `plugin` ohne ID und `core` mit.
 */
export type Provenance = { kind: 'core' } | { kind: 'plugin'; id: string }

/**
 * Ein **Handelsplatz**: echter MIC und höchstens ein Provider-Alias.
 *
 * `alias` ist das nackte Token ohne Punkt (`'DE'`). Den Punkt setzt das Backend
 * beim Zusammensetzen des Symbols.
 *
 * **Optional und nullable, beides.** Das Backend liefert heute `null`, aber der
 * OpenAPI-Vertrag führt `alias` nicht in `required` — ein Erzeuger darf das Feld
 * also weglassen. Ein Typ, der nur `null` erlaubt, wäre strenger als der
 * Vertrag und würde gültige Antworten ablehnen.
 *
 * **Was TypeScript hier nicht leisten kann.** Dass `''` verboten ist, steht im
 * OpenAPI-Schema (`minLength: 1`) und wird von Pydantic durchgesetzt. Ein
 * Stringtyp kann das nicht ausdrücken; die Zusage lebt auf der Backend-Schicht,
 * nicht hier.
 */
export interface ExchangeEntry {
  kind: 'exchange'
  mic: string
  alias?: string | null
  name: string
  region: string
  currency: string
  provenance: Provenance
}

/**
 * Ein **Sammelcode**: mehrere Handelsplätze, **kein** MIC.
 *
 * Bewusst ohne `mic`-Feld. Bis T-21 Teil 3 lag `US` in derselben Liste wie die
 * Börsen und kam als `mic: 'US'` herein — ein Wert, den das Backend selbst als
 * ungültigen MIC ablehnt.
 */
export interface CollectorEntry {
  kind: 'collector'
  code: string
  name: string
  region: string
  currency: string
  members: string[]
  provenance: Provenance
}

export type CatalogEntry = ExchangeEntry | CollectorEntry

/** Antwort von GET /exchanges: der Börsenkatalog plus konfigurierte Vorgabe. */
export interface ExchangesResponse {
  default_exchange: string
  default_exchange_kind: 'exchange' | 'collector' | 'unknown'
  catalog: CatalogEntry[]
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

/**
 * Antwort von `GET /ready` — der Diagnoseweg mit dem vollständigen Zustand.
 *
 * `status` **und** `database` zusammen sind die Aussage, nicht `status`
 * allein: Eine unerreichbare Datenbank und ein gescheiterter Betriebsstart
 * tragen beide `degraded` und unterscheiden sich erst über das zweite Feld.
 */
export interface ReadinessResponse {
  status: 'ok' | 'degraded' | 'migration_pending' | 'starting'
  version: string
  database: string
}

/**
 * Ein Papier, das den gültigen Bestand verlässt oder verlassen hat.
 *
 * Dasselbe Modell für Vorschau **und** Bericht — was der Benutzer vorher
 * sieht, muss er hinterher wiedererkennen.
 *
 * `reason` ist eine **stabile Kennung**, kein Satz. Der Text dazu steht im
 * Katalog unter `migration.reason.*`; wer darauf reagiert, prüft diesen Wert.
 */
export interface RejectedInstrument {
  symbol: string
  isin: string | null
  name: string | null
  exchange: string | null
  type: string | null
  currency: string | null
  reason: string
  quotes: number
  daily_closes: number
}

/** Was der bestätigte Umzug tun **würde** — Phase 1, ohne etwas zu ändern. */
export interface MigrationPreview {
  pending: boolean
  migrating: number
  unchanged: number
  rejected: RejectedInstrument[]
  lost_quotes: number
  lost_daily_closes: number
}

/** Was tatsächlich geschehen ist — Phase 2, auch lange danach noch abrufbar. */
export interface MigrationReport {
  completed: boolean
  rejected: RejectedInstrument[]
}
