"""Dashboard-Endpoints — DB-Übersicht, Environment, Refresh, Löschen.

Nur HTTP-Belange; Fachlogik liegt im CachedQuoteService.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from app import __version__
from app.config import Settings, get_settings
from app.container import get_cached_quote_service
from app.models import EnvInfo, InstrumentSummary, QuoteResponse, RefreshResult
from app.services.quote_cache import CachedQuoteService
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
        api_key_set=bool(settings.api_key),
        openfigi_key_set=bool(settings.openfigi_api_key),
    )


@router.post("/refresh", response_model=RefreshResult)
def refresh_all(service: ServiceDep) -> RefreshResult:
    """Aktualisiert alle bekannten Instrumente live."""
    total = service.count_instruments()
    refreshed = service.refresh_all()
    return RefreshResult(total=total, refreshed=refreshed)


@router.post("/refresh/{isin}", response_model=QuoteResponse)
def refresh_one(isin: str, service: ServiceDep) -> QuoteResponse:
    """Aktualisiert ein einzelnes Instrument per ISIN."""
    try:
        return service.refresh_one(isin)
    except InstrumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Keine Auflösung für {isin}") from exc
    except QuoteUnavailableError as exc:
        raise HTTPException(status_code=502, detail=f"Kein Kurs für {isin}") from exc


@router.delete("/instruments/{isin}", status_code=204)
def delete_instrument(isin: str, service: ServiceDep) -> Response:
    """Löscht ein Instrument samt Historie."""
    if not service.delete_instrument(isin):
        raise HTTPException(status_code=404, detail=f"Unbekannte ISIN {isin}")
    return Response(status_code=204)
