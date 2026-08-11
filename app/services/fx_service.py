"""Cachende Devisenkurs-Beschaffung — Lazy-TTL über yfinance.

Analog zu CachedQuoteService: frischer Cache → nutzen; sonst frisch holen und
speichern; schlägt das Holen fehl, aber ein alter Wert liegt vor, wird dieser
als ``stale`` geliefert statt eines Fehlers.
"""

from datetime import datetime, timezone
from typing import Protocol

import structlog

from app.models import FxRate
from app.services.freshness import is_fresh

logger = structlog.get_logger()


class FxRateProvider(Protocol):
    """Liefert einen Wechselkurs (1 base = ? quote)."""

    def fetch_fx_rate(self, base: str, quote: str) -> float | None: ...


class FxUnavailableError(Exception):
    """Es konnte kein Wechselkurs beschafft werden und kein Cache liegt vor."""


class FxRepository(Protocol):
    def get_fx_rate(self, base: str, quote: str) -> dict | None: ...
    def save_fx_rate(
        self, base: str, quote: str, rate: float, quote_time: str, fetched_at: str
    ) -> None: ...


class CachedFxService:
    """Legt einen TTL-Cache (SQLite) vor die Live-FX-Beschaffung."""

    def __init__(
        self, provider: FxRateProvider, repository: FxRepository, ttl_hours: int
    ) -> None:
        """
        Args:
            provider: Live-Beschaffung eines Wechselkurses (yfinance).
            repository: SQLite-Persistenz für den FX-Cache.
            ttl_hours: Maximales Alter eines Kurses, bevor neu beschafft wird.
        """
        self._provider = provider
        self._repository = repository
        self._ttl_hours = ttl_hours

    def get_rate(self, base: str, quote: str) -> FxRate:
        """Liefert den Wechselkurs 1 base = ? quote (aus Cache oder frisch).

        Args:
            base: Ausgangswährung (ISO-4217-Code, wird großgeschrieben).
            quote: Zielwährung (ISO-4217-Code, wird großgeschrieben).

        Returns:
            Der Wechselkurs — als Identität (base==quote), aus dem Cache
            (frisch oder stale) oder frisch beschafft.

        Raises:
            FxUnavailableError: Kein Kurs beschaffbar und kein Cache vorhanden.
        """
        base, quote = base.upper(), quote.upper()
        if base == quote:
            return self._identity(base, quote)

        cached = self._repository.get_fx_rate(base, quote)
        if cached and is_fresh(cached["fetched_at"], self._ttl_hours):
            return self._from_cache(cached, stale=False)

        return self._fetch_or_fallback(base, quote, cached)

    def _fetch_or_fallback(self, base: str, quote: str, cached: dict | None) -> FxRate:
        """Beschafft live; liefert bei Fehlschlag den Cache stale oder wirft."""
        rate = self._provider.fetch_fx_rate(base, quote)
        if rate is None:
            if cached:
                logger.warning("serving_stale_fx", base=base, quote=quote)
                return self._from_cache(cached, stale=True)
            raise FxUnavailableError(f"{base}{quote}")

        now = datetime.now(timezone.utc).isoformat()
        self._repository.save_fx_rate(base, quote, rate, now, now)
        return FxRate(
            base=base, quote=quote, rate=rate, quote_time=now, source="yfinance",
            cached=False, stale=False, fetched_at=now,
        )

    @staticmethod
    def _identity(base: str, quote: str) -> FxRate:
        """Baut den trivialen 1:1-Kurs für base==quote (kein Fetch nötig)."""
        now = datetime.now(timezone.utc).isoformat()
        return FxRate(
            base=base, quote=quote, rate=1.0, quote_time=now, source="identity",
            cached=False, stale=False, fetched_at=now,
        )

    @staticmethod
    def _from_cache(row: dict, stale: bool) -> FxRate:
        """Baut eine FxRate aus einer gespeicherten Zeile."""
        return FxRate(
            base=row["base"], quote=row["quote"], rate=row["rate"],
            quote_time=row["quote_time"], source="cache", cached=True, stale=stale,
            fetched_at=row["fetched_at"],
        )
