"""Pydantic-Response-Modelle der API."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Antwort des Health-Check-Endpoints."""

    status: str = "ok"
    version: str


class QuotePoint(BaseModel):
    """Ein einzelner Kurspunkt der Zeitreihe."""

    price: float
    quote_time: str
    volume: int | None = None
    currency: str | None = None
    fetched_at: str


class DailyPoint(BaseModel):
    """Ein Tages-Schlusskurs (EOD) der Langfrist-Historie."""

    date: str
    close: float
    currency: str | None = None


class QuoteResponse(BaseModel):
    """Vollständige Kurs- und Metadaten-Antwort für ein Wertpapier.

    Nicht ermittelbare Felder bleiben ``None`` (z.B. ``ter`` bei Einzelaktien).
    """

    isin: str | None = None
    symbol: str
    exchange: str | None = None
    name: str | None = None
    type: str | None = Field(default=None, description="stock | etf")
    currency: str | None = None

    price: float
    quote_time: str
    volume: int | None = None

    ter: float | None = None
    provider: str | None = None
    replication: str | None = None
    fund_size: float | None = None
    volatility: float | None = Field(default=None, description="1-Jahres-Volatilität in %")
    accumulating: bool | None = Field(
        default=None, description="Thesaurierend (true) vs. ausschüttend (false)"
    )

    source: str | None = None
    cached: bool = False
    stale: bool = False
    fetched_at: str


OVERRIDE_FIELDS = ("ter", "volatility", "accumulating")
"""Kennzahlen, die von Hand nachgetragen werden können.

Eine Quelle für Modell, Endpoint und Tests — sonst kennt jede Stelle eine
andere Teilmenge.
"""


class InstrumentOverrides(BaseModel):
    """Von Hand nachgetragene Kennzahlen.

    ``None`` heißt „nicht gepflegt". Beim Schreiben ist das gleichbedeutend mit
    „löschen": Die Oberfläche schickt immer den vollständigen Satz.
    """

    ter: float | None = Field(default=None, ge=0, le=5, description="TER in %")
    volatility: float | None = Field(
        default=None, ge=0, le=500, description="1-Jahres-Volatilität in %"
    )
    accumulating: bool | None = Field(
        default=None, description="Thesaurierend (true) vs. ausschüttend (false)"
    )


class InstrumentSummary(BaseModel):
    """Ein Instrument mit seinem letzten Kurs — für die DB-Übersicht.

    ``ter``, ``volatility`` und ``accumulating`` sind die **wirksamen** Werte:
    Was die Quelle liefert, gewinnt; ein manueller Wert füllt nur Lücken. Damit
    die Oberfläche das erklären kann, kommen die manuellen Werte zusätzlich roh
    mit — und zwei Listen sagen, wo sie gerade greifen und wo sie verdeckt sind.
    """

    isin: str | None = None
    symbol: str
    exchange: str | None = None
    name: str | None = None
    type: str | None = None
    currency: str | None = None
    provider: str | None = None
    ter: float | None = None
    replication: str | None = None
    fund_size: float | None = None
    volatility: float | None = None
    accumulating: bool | None = None
    meta_fetched_at: str | None = None
    latest_price: float | None = None
    latest_quote_time: str | None = None
    latest_currency: str | None = None
    latest_fetched_at: str | None = None
    history_count: int = 0

    manual_ter: float | None = None
    manual_volatility: float | None = None
    manual_accumulating: bool | None = None
    manual_fields: list[str] = Field(
        default_factory=list, description="Kennzahlen, die gerade von Hand kommen"
    )
    shadowed_fields: list[str] = Field(
        default_factory=list,
        description="Kennzahlen mit manuellem Wert, den die Quelle gerade verdeckt",
    )


class EnvInfo(BaseModel):
    """Sichtbarer Ausschnitt der Konfiguration (Secrets nur als Booleans)."""

    version: str
    database_path: str
    cache_ttl_hours: int
    refresh_interval_hours: int
    metadata_ttl_days: int
    default_exchange: str
    strict_exchange: bool
    host: str
    port: int
    openfigi_key_set: bool
    extraetf_etf_url: str = ""
    extraetf_stock_url: str = ""
    yahoo_url: str = ""


class ExchangeInfo(BaseModel):
    """Eine auflösbare Börse (aus der Backend-Tabelle)."""

    mic: str
    suffix: str
    name: str
    region: str
    currency: str


class FxRate(BaseModel):
    """Ein Wechselkurs: 1 ``base`` = ``rate`` ``quote`` (base=von, quote=nach)."""

    base: str
    quote: str
    rate: float
    quote_time: str
    source: str | None = None
    cached: bool = False
    stale: bool = False
    fetched_at: str


class ExchangesResponse(BaseModel):
    """Weltweite Börsentabelle + die konfigurierte Default-Börse der Instanz."""

    default_exchange: str
    exchanges: list[ExchangeInfo]


class RefreshResult(BaseModel):
    """Ergebnis eines globalen Refresh-Laufs."""

    total: int
    refreshed: int


class IsinUpdate(BaseModel):
    """Body zum nachträglichen Eintragen einer ISIN."""

    isin: str


class AnalyzeStage(BaseModel):
    """Eine gemessene Stage des Live-Fetch (Diagnose)."""

    stage: str = Field(description="openfigi | fast_info | get_info | isin | history | justetf")
    seconds: float
    status: str = Field(description="ok | error | empty | skipped")
    detail: str | None = None


class AnalyzeResult(BaseModel):
    """Timing-Aufschlüsselung eines Live-Fetch für ein Wertpapier."""

    symbol: str
    isin: str | None = None
    total: float
    stages: list[AnalyzeStage]
