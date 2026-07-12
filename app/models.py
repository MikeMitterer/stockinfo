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
