"""Dashboard-Endpoints — DB-Übersicht, Environment, Refresh, Löschen.

Nur HTTP-Belange; Fachlogik liegt im CachedQuoteService.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from app import __version__
from app.config import Settings, get_settings
from app.container import get_cached_quote_service
from app.models import (
    EnvInfo,
    InstrumentSummary,
    IsinUpdate,
    QuoteResponse,
    RefreshResult,
)
from app.routers.validation import IsinPath, normalize_isin
from app.services.quote_cache import (
    CachedQuoteService,
    IsinConflictError,
    RefreshInProgressError,
)
from app.services.quote_service import InstrumentNotFoundError, QuoteUnavailableError

router = APIRouter(tags=["dashboard"])

ServiceDep = Annotated[CachedQuoteService, Depends(get_cached_quote_service)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.get("/instruments", response_model=list[InstrumentSummary])
def list_instruments(service: ServiceDep) -> list[dict]:
    """Gibt alle gecachten Instrumente mit letztem Kurs zurück."""
    return service.list_instruments()


@router.get("/env", response_model=EnvInfo)
def environment(settings: SettingsDep) -> EnvInfo:
    """Gibt den sichtbaren Ausschnitt der Konfiguration zurück (Secrets maskiert)."""
    return EnvInfo(
        version=__version__,
        database_path=settings.database_path,
        cache_ttl_hours=settings.cache_ttl_hours,
        refresh_interval_hours=settings.refresh_interval_hours,
        metadata_ttl_days=settings.metadata_ttl_days,
        default_exchange=settings.default_exchange,
        host=settings.host,
        port=settings.port,
        openfigi_key_set=bool(settings.openfigi_api_key),
        extraetf_etf_url=settings.extraetf_etf_url,
        extraetf_stock_url=settings.extraetf_stock_url,
        yahoo_url=settings.yahoo_url,
    )


@router.post("/refresh", response_model=RefreshResult)
def refresh_all(service: ServiceDep) -> RefreshResult:
    """Aktualisiert alle bekannten Instrumente live."""
    total = service.count_instruments()
    try:
        refreshed = service.refresh_all()
    except RefreshInProgressError as exc:
        raise HTTPException(status_code=409, detail="Refresh läuft bereits") from exc
    return RefreshResult(total=total, refreshed=refreshed)


@router.post("/refresh/{isin}", response_model=QuoteResponse)
def refresh_one(isin: IsinPath, service: ServiceDep) -> QuoteResponse:
    """Aktualisiert ein einzelnes Instrument per ISIN."""
    try:
        return service.refresh_one(isin)
    except InstrumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Keine Auflösung für {isin}") from exc
    except QuoteUnavailableError as exc:
        raise HTTPException(status_code=502, detail=f"Kein Kurs für {isin}") from exc


@router.post("/refresh/by-symbol/{symbol}", response_model=QuoteResponse)
def refresh_one_by_symbol(symbol: str, service: ServiceDep) -> QuoteResponse:
    """Aktualisiert ein Instrument per Symbol (für Papiere ohne ISIN)."""
    try:
        return service.refresh_one_by_symbol(symbol)
    except QuoteUnavailableError as exc:
        raise HTTPException(
            status_code=502, detail=f"Kein Kurs für {symbol}"
        ) from exc


@router.delete("/instruments/{isin}", status_code=204)
def delete_instrument(isin: IsinPath, service: ServiceDep) -> Response:
    """Löscht ein Instrument samt Historie per ISIN."""
    if not service.delete_instrument(isin):
        raise HTTPException(status_code=404, detail=f"Unbekannte ISIN {isin}")
    return Response(status_code=204)


@router.put("/instruments/by-symbol/{symbol}/isin", response_model=dict)
def set_isin(symbol: str, payload: IsinUpdate, service: ServiceDep) -> dict:
    """Trägt die ISIN eines Instruments (per Symbol) nachträglich ein."""
    isin = normalize_isin(payload.isin)
    try:
        service.set_isin(symbol, isin)
    except InstrumentNotFoundError as exc:
        raise HTTPException(
            status_code=404, detail=f"Unbekanntes Symbol {symbol}"
        ) from exc
    except IsinConflictError as exc:
        raise HTTPException(
            status_code=409, detail=f"ISIN {isin} ist bereits vergeben"
        ) from exc
    return {"symbol": symbol, "isin": isin}


@router.delete("/instruments/by-symbol/{symbol}", status_code=204)
def delete_instrument_by_symbol(symbol: str, service: ServiceDep) -> Response:
    """Löscht ein Instrument samt Historie per Symbol (für Papiere ohne ISIN)."""
    if not service.delete_by_symbol(symbol):
        raise HTTPException(status_code=404, detail=f"Unbekanntes Symbol {symbol}")
    return Response(status_code=204)
