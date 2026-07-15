"""Kurs-Endpoints — Abfrage per ISIN, per Symbol und Historie.

Der Router übersetzt nur zwischen HTTP und Service; Domain-Exceptions werden
auf HTTP-Statuscodes abgebildet.
"""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.container import get_cached_quote_service, get_daily_history_service
from app.models import DailyPoint, QuotePoint, QuoteResponse
from app.routers.validation import IsinPath
from app.services.daily_history import DailyHistoryService
from app.services.quote_cache import CachedQuoteService
from app.services.quote_service import InstrumentNotFoundError, QuoteUnavailableError

router = APIRouter(tags=["quotes"])

ServiceDep = Annotated[CachedQuoteService, Depends(get_cached_quote_service)]
DailyDep = Annotated[DailyHistoryService, Depends(get_daily_history_service)]

Period = Literal["1w", "1m", "3m", "1y", "max"]


@router.get("/quote", response_model=QuoteResponse)
def quote_by_symbol(
    service: ServiceDep,
    symbol: Annotated[
        str, Query(description="Vollständiges Yahoo-Symbol inkl. Suffix, z.B. VGWL.DE")
    ],
) -> QuoteResponse:
    """Liefert den Kurs zu einem vollständigen Yahoo-Symbol."""
    try:
        return service.get_by_symbol(symbol)
    except QuoteUnavailableError as exc:
        raise HTTPException(status_code=502, detail=f"Kein Kurs für {symbol}") from exc


@router.get("/quote/{isin}", response_model=QuoteResponse)
def quote_by_isin(isin: IsinPath, service: ServiceDep) -> QuoteResponse:
    """Liefert den Kurs zu einer ISIN (bevorzugt Xetra/EUR)."""
    try:
        return service.get_by_isin(isin)
    except InstrumentNotFoundError as exc:
        raise HTTPException(
            status_code=404, detail=f"Keine Auflösung für ISIN {isin}"
        ) from exc
    except QuoteUnavailableError as exc:
        raise HTTPException(
            status_code=502, detail=f"Kein Kurs für ISIN {isin}"
        ) from exc


@router.get("/quote/{isin}/daily", response_model=list[DailyPoint])
def daily_history(
    isin: IsinPath,
    service: DailyDep,
    period: Annotated[Period, Query()] = "1m",
) -> list[DailyPoint]:
    """Liefert echte Tages-Schlusskurse (EOD) zu einer ISIN, inkrementell gecacht."""
    try:
        return service.get_daily(isin=isin, period=period)
    except (InstrumentNotFoundError, QuoteUnavailableError) as exc:
        raise HTTPException(
            status_code=502, detail=f"Keine Historie für {isin}"
        ) from exc


@router.get("/quote/by-symbol/{symbol}/daily", response_model=list[DailyPoint])
def daily_history_by_symbol(
    symbol: str,
    service: DailyDep,
    period: Annotated[Period, Query()] = "1m",
) -> list[DailyPoint]:
    """Liefert echte Tages-Schlusskurse (EOD) zu einem Symbol, inkrementell gecacht."""
    try:
        return service.get_daily(symbol=symbol, period=period)
    except (InstrumentNotFoundError, QuoteUnavailableError) as exc:
        raise HTTPException(
            status_code=502, detail=f"Keine Historie für {symbol}"
        ) from exc


@router.get("/quote/by-symbol/{symbol}/history", response_model=list[QuotePoint])
def quote_history_by_symbol(
    symbol: str,
    service: ServiceDep,
    date_from: Annotated[str | None, Query(alias="from")] = None,
    date_to: Annotated[str | None, Query(alias="to")] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[QuotePoint]:
    """Liefert die Kurs-Historie zu einem Symbol (für Papiere ohne ISIN)."""
    try:
        return service.get_history_by_symbol(symbol, date_from, date_to, limit)
    except QuoteUnavailableError as exc:
        raise HTTPException(status_code=502, detail=f"Kein Kurs für {symbol}") from exc


@router.get("/quote/{isin}/history", response_model=list[QuotePoint])
def quote_history(
    isin: IsinPath,
    service: ServiceDep,
    date_from: Annotated[str | None, Query(alias="from")] = None,
    date_to: Annotated[str | None, Query(alias="to")] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[QuotePoint]:
    """Liefert die gespeicherte Kurs-Historie zu einer ISIN (neueste zuerst)."""
    try:
        return service.get_history(isin, date_from, date_to, limit)
    except InstrumentNotFoundError as exc:
        raise HTTPException(
            status_code=404, detail=f"Keine Auflösung für ISIN {isin}"
        ) from exc
    except QuoteUnavailableError as exc:
        raise HTTPException(
            status_code=502, detail=f"Kein Kurs für ISIN {isin}"
        ) from exc
