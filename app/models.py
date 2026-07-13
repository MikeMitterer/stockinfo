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

    source: str | None = None
    cached: bool = False
    stale: bool = False
    fetched_at: str


class InstrumentSummary(BaseModel):
    """Ein Instrument mit seinem letzten Kurs — für die DB-Übersicht."""

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
    meta_fetched_at: str | None = None
    latest_price: float | None = None
    latest_quote_time: str | None = None
    latest_currency: str | None = None
    latest_fetched_at: str | None = None
    history_count: int = 0


class EnvInfo(BaseModel):
    """Sichtbarer Ausschnitt der Konfiguration (Secrets nur als Booleans)."""

    version: str
    database_path: str
    cache_ttl_hours: int
    refresh_interval_hours: int
    metadata_ttl_days: int
    default_exchange: str
    host: str
    port: int
    api_key_set: bool
    openfigi_key_set: bool


class RefreshResult(BaseModel):
    """Ergebnis eines globalen Refresh-Laufs."""

    total: int
    refreshed: int
