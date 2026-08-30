"""Cachende Devisenkurs-Beschaffung — Lazy-TTL vor der Devisenquelle.

Analog zu CachedQuoteService: frischer Cache → nutzen; sonst frisch holen und
speichern; schlägt das Holen fehl, aber ein alter Wert liegt vor, wird dieser
als ``stale`` geliefert statt eines Fehlers.
"""

from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Protocol

import structlog

from app.models import FxRate
from app.providers.base import FxRateProvider, declared_name
from app.services.freshness import is_fresh

logger = structlog.get_logger()


class FxUnavailableError(Exception):
    """Es konnte kein Wechselkurs beschafft werden und kein Cache liegt vor."""


class FxRepository(Protocol):
    def get_fx_rate(self, base: str, quote: str) -> dict | None: ...
    def save_fx_rate(
        self,
        base: str,
        quote: str,
        rate: float,
        quote_time: str,
        fetched_at: str,
        source: str | None = None,
    ) -> None: ...


class CachedFxService:
    """Legt einen TTL-Cache (SQLite) vor die Live-FX-Beschaffung."""

    def __init__(
        self,
        provider: FxRateProvider | Sequence[FxRateProvider],
        repository: FxRepository,
        ttl_hours: int,
    ) -> None:
        """
        Args:
            provider: Die Live-Beschaffung — eine Quelle oder die konfigurierte
                Reihenfolge. Wer das ist, entscheidet `sources.yaml`.

                **Beide Formen, und das ist kein Übergangszustand.** Eine
                einzelne Quelle ist der Normalfall vieler Aufrufer und liest
                sich als Liste schlechter; die Reihenfolge ist der Fall, den
                das Ticket braucht. Der Konstruktor macht daraus einmal ein
                Tupel, und alles darunter kennt nur noch die eine Form.
            repository: SQLite-Persistenz für den FX-Cache.
            ttl_hours: Maximales Alter eines Kurses, bevor neu beschafft wird.
        """
        self._providers = (
            tuple(provider)
            if isinstance(provider, (list, tuple))
            else (provider,)
        )
        self._repository = repository
        self._ttl_hours = ttl_hours

    @property
    def _fx_source(self) -> str | None:
        """Wer den Wechselkurs geliefert hat — dieselbe Regel wie beim Kurs.

        **Anders als beim Kurs ist das hier wirklich der Kurslieferant.** Der
        Vertrag sagt für `fx.source` ausdrücklich „Woher der Kurs stammt" —
        nicht „woher die Metadaten kommen" wie bei `quote.source`. Die beiden
        Felder heißen gleich und bedeuten Verschiedenes. Der Rückfall aus
        `declared_name` ist bewusst ``None``: Ein Ersatzwort wäre keine
        belastbare Herkunft und stünde unübersetzt in der Oberfläche.

        **Der Name der ersten Quelle sagt nichts über den Lieferanten** —
        deshalb steht die Herkunft im Fetch als lokale Variable neben dem
        Kurs und nicht in einem Feld. Ein „letzter
        Lieferant" am Dienst wäre veränderlicher Zustand: Zwei gleichzeitige
        Anfragen schrieben sich gegenseitig die Herkunft um, und der Fehler
        fiele erst bei Last auf.
        """
        return declared_name(self._providers[0])

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
        # **Die Reihenfolge aus `sources.yaml` wird wirklich abgefragt.**
        # Der Lieferant steht **hier**, neben dem Kurs, und nicht in einem
        # Feld am Dienst: Zwei gleichzeitige Anfragen schrieben sich sonst
        # gegenseitig die Herkunft um, und ein Kurs trüge den Namen einer
        # Quelle, die ihn nicht geliefert hat.
        rate: float | None = None
        source: str | None = None
        for provider in self._providers:
            rate = provider.fetch_fx_rate(base, quote)
            if rate is not None:
                source = declared_name(provider)
                break

        if rate is None:
            # Erst nach dem **Gesamtausfall**: Solange irgendeine Quelle
            # antwortet, ist ein veralteter Wert die schlechtere Auskunft.
            if cached:
                logger.warning("serving_stale_fx", base=base, quote=quote)
                return self._from_cache(cached, stale=True)
            raise FxUnavailableError(f"{base}{quote}")

        now = datetime.now(timezone.utc).isoformat()
        self._repository.save_fx_rate(base, quote, rate, now, now, source)
        return FxRate(
            base=base, quote=quote, rate=rate, quote_time=now,
            source=source,
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
        """Baut eine FxRate aus einer gespeicherten Zeile.

        **Die Herkunft kommt aus der Zeile, nicht aus einer Konstante.** Hier
        stand ``source="cache"``, und damit war der Lieferant nach dem ersten
        Treffer verloren: Jeder gecachte Kurs behauptete, aus „cache" zu
        stammen. Das sagt `cached: true` ohnehin — und `fx.source` beantwortet
        laut Vertrag die andere Frage, nämlich *woher der Kurs stammt*.

        Zeilen aus der Zeit vor der Spalte tragen ``None``; das ist ehrlicher
        als ein Wort, das keine Quelle benennt.
        """
        return FxRate(
            base=row["base"], quote=row["quote"], rate=row["rate"],
            quote_time=row["quote_time"], source=row.get("source"),
            cached=True, stale=stale, fetched_at=row["fetched_at"],
        )
