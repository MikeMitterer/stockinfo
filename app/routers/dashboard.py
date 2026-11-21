"""Dashboard-Endpoints — Übersicht, Environment, Diagnose, Analyse, Refresh,
eigene Werte, Löschen.

Nur HTTP-Belange. Fachlogik liegt im `CachedQuoteService` und im
`QuoteAnalyzer`, die Selbstauskunft über Börsenkatalog und Quellenlage in
`services/diagnostics.py`.

**Die `by-symbol`-Wege antworten bei einem mehrdeutigen Symbol mit `409`**,
ohne dass hier etwas davon steht: Die Mehrdeutigkeit stellt das Repository
fest, abgebildet wird sie zentral in `app/main.py`. Das gilt gerade für
`DELETE /instruments/by-symbol/{symbol}` — bis Runde 45 löschte der Endpunkt
bei zwei gleichnamigen Listings beide samt Historie, und genau er ist das
Beispiel, mit dem T-24 die Regel begründet hat.

`responses` beschreiben an diesen Endpunkten nur die ISIN-Prüfung
(`invalid_isin_response`); weitere Fehlerzusagen fehlen bewusst. Die Wege
liegen laut `docs/rest-core-contract.md` außerhalb des geschlossenen Core.
Jede Ablehnung hat trotzdem dieselbe Form wie im Core: `{code, params}` über
`ApiError` (T-139).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app import __version__
from app.config import Settings, get_settings
from app.container import (
    get_cached_quote_service,
    get_quote_analyzer,
    get_sources_config,
)
from app.detail_models import DetailInput, DetailValue
from app.models import (
    AnalyzeResult,
    EnvInfo,
    ExchangesResponse,
    InstrumentOverrides,
    InstrumentSummary,
    IsinUpdate,
    QuoteResponse,
    RefreshResult,
    SourcesResponse,
    invalid_isin_response,
)
from app.details import DetailValueError
from app.routers.api_error import ApiError
from app.routers.source_errors import instrument_not_found_error, quote_unavailable_error
from app.routers.validation import (
    IsinPath,
    SymbolPath,
    normalize_isin,
    normalize_symbol,
)
from app.services.analyzer import QuoteAnalyzer
from app.services.diagnostics import exchange_overview, source_overview
from app.services.quote_cache import (
    CachedQuoteService,
    IsinConflictError,
    RefreshInProgressError,
)
from app.services.quote_service import InstrumentNotFoundError, QuoteUnavailableError

router = APIRouter(tags=["dashboard"])

# Die Analyse braucht genau eine der beiden Kennungen.
REASON_ISIN_OR_SYMBOL = "isin_or_symbol_required"

# Ein Gesamt-Refresh läuft schon; ein zweiter würde dieselben Quellen doppelt fragen.
REASON_REFRESH_RUNNING = "refresh_in_progress"

# Der Bestand führt kein Instrument unter dieser Kennung (`params.identifier`).
# **Nicht** `instrument_not_found`: Dort haben die Quellen geantwortet und
# kennen das Papier nicht; hier wurde gar keine Quelle gefragt.
REASON_NOT_STORED = "instrument_not_stored"

# Keine Zeile trägt diese `listing_id` (`params.listing_id`).
REASON_LISTING_NOT_FOUND = "listing_not_found"

# Ein anderes Instrument trägt die ISIN schon (`params.isin`).
REASON_ISIN_TAKEN = "isin_taken"


def _not_stored(identifier: str) -> ApiError:
    """`404 instrument_not_stored` für eine ISIN oder ein Symbol."""
    return ApiError(404, REASON_NOT_STORED, {"identifier": identifier})


def _invalid_detail(error: DetailValueError) -> ApiError:
    """`422` mit der Kennung, die die Detailprüfung vergeben hat."""
    return ApiError(422, error.code, error.params)

ServiceDep = Annotated[CachedQuoteService, Depends(get_cached_quote_service)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
AnalyzerDep = Annotated[QuoteAnalyzer, Depends(get_quote_analyzer)]


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
        refresh_interval_minutes=settings.refresh_minutes,
        metadata_ttl_days=settings.metadata_ttl_days,
        default_exchange=settings.default_exchange,
        strict_exchange=settings.strict_exchange,
        host=settings.host,
        port=settings.port,
        openfigi_key_set=bool(settings.openfigi_api_key),
        extraetf_etf_url=settings.extraetf_etf_url,
        extraetf_stock_url=settings.extraetf_stock_url,
        yahoo_url=settings.yahoo_url,
    )


@router.get("/exchanges", response_model=ExchangesResponse)
def exchanges(settings: SettingsDep) -> ExchangesResponse:
    """Aktiver Börsenkatalog und deklarierte Unterstützung, ohne Live-Abfrage."""
    return exchange_overview(get_sources_config(), settings)


@router.get("/sources", response_model=SourcesResponse)
def sources(settings: SettingsDep) -> SourcesResponse:
    """Welche Quellen in welcher Reihenfolge greifen — und welche ausfallen.

    **Der Beleg, dass die Konfiguration wirkt.** Bis T-22 stand die Kette als
    `if`-Kaskade im Code; wer wissen wollte, welche Quelle zuerst gefragt wird,
    musste ihn lesen. Jetzt beantwortet der Dienst die Frage selbst.
    """
    # **Derselbe Stand wie die laufenden Dienste**, nicht die Datei von jetzt.
    # Die Services halten `get_sources_config()` gecacht; läse der Endpunkt die
    # Datei bei jedem Request neu, meldete er nach einer Änderung ohne Neustart
    # eine Kette, die gar nicht läuft — und die Diagnose wäre genau dann
    # falsch, wenn man sie braucht.
    return source_overview(get_sources_config(), settings)


@router.get(
    "/analyze",
    response_model=AnalyzeResult,
    responses=invalid_isin_response(),
)
def analyze(
    analyzer: AnalyzerDep,
    isin: str | None = None,
    symbol: str | None = None,
) -> AnalyzeResult:
    """Misst die Dauer der Live-Fetch-Stages für ein Wertpapier (Diagnose).

    Genau eines von ``isin``/``symbol`` angeben. Löst echte externe Abfragen aus
    (kein Cache).
    """
    if bool(isin) == bool(symbol):
        raise ApiError(422, REASON_ISIN_OR_SYMBOL)
    return analyzer.analyze(
        isin=normalize_isin(isin) if isin else None,
        symbol=normalize_symbol(symbol) if symbol else None,
    )


@router.post("/refresh", response_model=RefreshResult)
def refresh_all(service: ServiceDep) -> RefreshResult:
    """Aktualisiert alle bekannten Instrumente live."""
    total = service.count_instruments()
    try:
        refreshed = service.refresh_all()
    except RefreshInProgressError as exc:
        raise ApiError(409, REASON_REFRESH_RUNNING) from exc
    return RefreshResult(total=total, refreshed=refreshed)


@router.post(
    "/refresh/{isin}",
    response_model=QuoteResponse,
    responses=invalid_isin_response(),
)
def refresh_one(isin: IsinPath, service: ServiceDep) -> QuoteResponse:
    """Aktualisiert ein einzelnes Instrument per ISIN."""
    try:
        return service.refresh_one(isin)
    except InstrumentNotFoundError as exc:
        raise instrument_not_found_error(isin) from exc
    except QuoteUnavailableError as exc:
        raise quote_unavailable_error(isin, exc) from exc


@router.post("/refresh/by-symbol/{symbol}", response_model=QuoteResponse)
def refresh_one_by_symbol(symbol: SymbolPath, service: ServiceDep) -> QuoteResponse:
    """Aktualisiert ein Instrument per Symbol (für Papiere ohne ISIN)."""
    try:
        return service.refresh_one_by_symbol(symbol)
    except QuoteUnavailableError as exc:
        raise quote_unavailable_error(symbol, exc) from exc


@router.delete(
    "/instruments/{isin}", status_code=204, responses=invalid_isin_response()
)
def delete_instrument(isin: IsinPath, service: ServiceDep) -> Response:
    """Löscht ein Instrument samt Historie per ISIN."""
    if not service.delete_instrument(isin):
        raise _not_stored(isin)
    return Response(status_code=204)


@router.put(
    "/instruments/by-symbol/{symbol}/isin",
    response_model=dict,
    responses=invalid_isin_response(validation=True),
)
def set_isin(symbol: SymbolPath, payload: IsinUpdate, service: ServiceDep) -> dict:
    """Trägt die ISIN eines Instruments (per Symbol) nachträglich ein."""
    isin = normalize_isin(payload.isin)
    try:
        service.set_isin(symbol, isin)
    except InstrumentNotFoundError as exc:
        raise _not_stored(symbol) from exc
    except IsinConflictError as exc:
        raise ApiError(409, REASON_ISIN_TAKEN, {"isin": isin}) from exc
    return {"symbol": symbol, "isin": isin}


@router.get(
    "/instruments/by-symbol/{symbol}/overrides", response_model=InstrumentOverrides
)
def get_overrides(symbol: SymbolPath, service: ServiceDep) -> InstrumentOverrides:
    """Gibt die von Hand nachgetragenen Kennzahlen eines Instruments zurück."""
    try:
        return InstrumentOverrides(**service.get_overrides(symbol))
    except InstrumentNotFoundError as exc:
        raise _not_stored(symbol) from exc


@router.put(
    "/instruments/by-symbol/{symbol}/overrides", response_model=InstrumentOverrides
)
def set_overrides(
    symbol: SymbolPath, payload: InstrumentOverrides, service: ServiceDep
) -> InstrumentOverrides:
    """Schreibt die von Hand nachgetragenen Kennzahlen eines Instruments.

    Immer der vollständige Satz: Ein weggelassenes bzw. ``null``-Feld **löscht**
    den bisherigen Wert. Gespeichert wird unabhängig davon, ob die Quelle den
    Wert gerade liefert — die Vorrang-Regel wirkt erst beim Lesen.
    """
    try:
        return InstrumentOverrides(**service.set_overrides(symbol, payload.model_dump()))
    except DetailValueError as error:
        raise _invalid_detail(error) from error
    except InstrumentNotFoundError as exc:
        raise _not_stored(symbol) from exc


@router.delete("/instruments/by-symbol/{symbol}", status_code=204)
def delete_instrument_by_symbol(symbol: SymbolPath, service: ServiceDep) -> Response:
    """Löscht ein Instrument samt Historie per Symbol (für Papiere ohne ISIN)."""
    if not service.delete_by_symbol(symbol):
        raise _not_stored(symbol)
    return Response(status_code=204)


@router.patch("/instruments/by-id/{listing_id}/details", response_model=dict[str, DetailValue])
def patch_details(listing_id: str, payload: dict[str, DetailInput], service: ServiceDep) -> dict:
    """Partielle manuelle Detailwerte über die eindeutige Listing-ID."""
    try:
        return service.set_detail_overrides(listing_id, payload)
    except InstrumentNotFoundError as error:
        raise ApiError(404, REASON_LISTING_NOT_FOUND, {"listing_id": listing_id}) from error
    except DetailValueError as error:
        raise _invalid_detail(error) from error
