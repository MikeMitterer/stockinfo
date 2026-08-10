"""On-Demand-Diagnose — misst die Dauer der einzelnen Live-Fetch-Stages.

Bewusst cache-umgehend: der Zweck ist die Messung des echten externen Pfades
(OpenFIGI, yfinance-Teilcalls, justETF) aus der Server-Umgebung. Jede Stage ist
best-effort — ein Fehler bricht die Analyse nicht ab, sondern wird erfasst.
"""

import time
from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

import structlog
import yfinance as yf

from app.models import AnalyzeResult, AnalyzeStage
from app.providers.base import EtfEnricher, InstrumentResolver

logger = structlog.get_logger()


class QuoteAnalyzer:
    """Führt einen instrumentierten Live-Fetch aus und liefert das Stage-Timing."""

    def __init__(
        self,
        resolver: InstrumentResolver,
        etf_provider: EtfEnricher,
        ticker_factory: Callable[[str], Any] = yf.Ticker,
    ) -> None:
        """
        Args:
            resolver: Löst ISINs zu Symbolen auf (OpenFIGI-Stage).
            etf_provider: justETF-Anreicherung (justetf-Stage).
            ticker_factory: Erzeugt ein Ticker-Objekt (fast_info, get_info, isin,
                history). Default ``yf.Ticker``; in Tests überschrieben.
        """
        self._resolver = resolver
        self._etf_provider = etf_provider
        self._ticker_factory = ticker_factory

    def analyze(
        self, *, isin: str | None = None, symbol: str | None = None
    ) -> AnalyzeResult:
        """Misst alle Stages eines Live-Fetch und liefert das Ergebnis.

        Genau eines von ``isin``/``symbol`` muss gesetzt sein (Validierung im
        Router). Bei ISIN wird zuerst aufgelöst (openfigi-Stage); bei direkter
        Symboleingabe entfällt sie (``skipped``).
        """
        stages: list[AnalyzeStage] = []
        start_total = time.perf_counter()

        resolved_symbol = symbol
        resolved_isin = isin

        if isin and not symbol:
            resolved, stage = self._measure_resolve(isin)
            stages.append(stage)
            resolved_symbol = resolved.symbol if resolved else None
        else:
            stages.append(AnalyzeStage(stage="openfigi", seconds=0.0, status="skipped"))

        if resolved_symbol is None:  # nicht auflösbar → Rest überspringen
            for name in ("fast_info", "get_info", "isin", "history", "justetf"):
                stages.append(AnalyzeStage(stage=name, seconds=0.0, status="skipped"))
            return AnalyzeResult(
                symbol=symbol or isin or "",
                isin=resolved_isin,
                total=round(time.perf_counter() - start_total, 3),
                stages=stages,
            )

        ticker = self._ticker_factory(resolved_symbol)
        stages.append(self._measure("fast_info", lambda: _touch_fast_info(ticker)))
        stages.append(self._measure("get_info", ticker.get_info))
        stages.append(self._measure("isin", lambda: getattr(ticker, "isin", None)))
        stages.append(
            self._measure(
                "history",
                lambda: ticker.history(
                    start=(date.today() - timedelta(days=370)).isoformat(),
                    interval="1d",
                    auto_adjust=True,
                ),
                detail=_rows_detail,
            )
        )

        if resolved_isin:
            stages.append(
                self._measure("justetf", lambda: self._etf_provider.fetch_etf(resolved_isin))
            )
        else:
            stages.append(AnalyzeStage(stage="justetf", seconds=0.0, status="skipped"))

        return AnalyzeResult(
            symbol=resolved_symbol,
            isin=resolved_isin,
            total=round(time.perf_counter() - start_total, 3),
            stages=stages,
        )

    def _measure_resolve(self, isin: str) -> tuple[Any, AnalyzeStage]:
        """Misst die OpenFIGI-Auflösung; ``empty`` wenn kein Symbol gefunden."""
        start = time.perf_counter()
        try:
            resolved = self._resolver.resolve_isin(isin)
        except Exception as exc:  # noqa: BLE001 — Diagnose erfasst Fehler
            return None, AnalyzeStage(
                stage="openfigi", seconds=_elapsed(start), status="error",
                detail=type(exc).__name__,
            )
        if resolved is None:
            return None, AnalyzeStage(stage="openfigi", seconds=_elapsed(start), status="empty")
        return resolved, AnalyzeStage(
            stage="openfigi", seconds=_elapsed(start), status="ok", detail=resolved.symbol
        )

    @staticmethod
    def _measure(
        name: str,
        fn: Callable[[], Any],
        detail: Callable[[Any], str | None] | None = None,
    ) -> AnalyzeStage:
        """Führt ``fn`` aus, misst die Dauer und erfasst Erfolg/Fehler/Leer."""
        start = time.perf_counter()
        try:
            value = fn()
        except Exception as exc:  # noqa: BLE001 — Diagnose erfasst Fehler
            return AnalyzeStage(
                stage=name, seconds=_elapsed(start), status="error",
                detail=type(exc).__name__,
            )
        seconds = _elapsed(start)
        if value is None:
            return AnalyzeStage(stage=name, seconds=seconds, status="empty")
        return AnalyzeStage(
            stage=name, seconds=seconds, status="ok",
            detail=detail(value) if detail else None,
        )


def _touch_fast_info(ticker: Any) -> Any:
    """Erzwingt den fast_info-Zugriff (last_price) — löst den Netzwerk-Call aus."""
    return ticker.fast_info.last_price


def _rows_detail(history: Any) -> str:
    """Formatiert die Zeilenzahl einer History als Detail-Text."""
    try:
        return f"{len(history)} rows"
    except TypeError:
        return "n/a"


def _elapsed(start: float) -> float:
    """Vergangene Zeit seit ``start`` in Sekunden, auf 3 Stellen gerundet."""
    return round(time.perf_counter() - start, 3)
