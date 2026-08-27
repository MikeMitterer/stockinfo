"""Dashboard-Endpoints — DB-Übersicht, Environment, Refresh, Löschen.

Nur HTTP-Belange; Fachlogik liegt im CachedQuoteService.

**Die `by-symbol`-Wege antworten bei einem mehrdeutigen Symbol mit `409`**,
ohne dass hier etwas davon steht: Die Mehrdeutigkeit stellt das Repository
fest, abgebildet wird sie zentral in `app/main.py`. Das gilt gerade für
`DELETE /instruments/by-symbol/{symbol}` — bis Runde 45 löschte der Endpunkt
bei zwei gleichnamigen Listings beide samt Historie, und genau er ist das
Beispiel, mit dem T-24 die Regel begründet hat.

`responses` stehen an diesen Endpunkten bewusst **nicht**: Sie liegen laut
`docs/rest-core-contract.md` außerhalb des geschlossenen Core, führen heute
keinerlei Fehlerzusagen — und `PUT .../isin` trägt zusätzlich einen dritten,
älteren `409` (`IsinConflictError`) in einer anderen Rumpfform. Diese drei
Formen zu vereinheitlichen ist eine eigene Aufräumarbeit und keine
Nebenwirkung dieses Tickets.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from app import __version__
from app.config import Settings, get_settings
from app.container import get_cached_quote_service, get_quote_analyzer
from app.models import (
    AnalyzeResult,
    CollectorEntry,
    EnvInfo,
    ExchangeEntry,
    ExchangesResponse,
    InstrumentOverrides,
    InstrumentSummary,
    IsinUpdate,
    QuoteResponse,
    RefreshResult,
    SourceEntry,
    SourcesResponse,
)
from app.exchanges import COLLECTORS, EXCHANGES, preference_kind
from app.container import get_sources_config
from app.sources_config import ROLES
from app.sources_registry import describe_chain
from app.routers.validation import (
    IsinPath,
    SymbolPath,
    normalize_isin,
    normalize_symbol,
)
from app.services.analyzer import QuoteAnalyzer
from app.services.quote_cache import (
    CachedQuoteService,
    IsinConflictError,
    RefreshInProgressError,
)
from app.services.quote_service import InstrumentNotFoundError, QuoteUnavailableError

router = APIRouter(tags=["dashboard"])

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
        refresh_interval_hours=settings.refresh_interval_hours,
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
    """Gibt die weltweite Börsentabelle und die konfigurierte Default-Börse zurück."""
    return ExchangesResponse(
        default_exchange=settings.default_exchange,
        default_exchange_kind=preference_kind(settings.default_exchange) or "unknown",
        catalog=[
            *(
                ExchangeEntry(
                    mic=mic,
                    alias=definition.alias,
                    name=definition.name,
                    region=definition.region,
                    currency=definition.currency,
                )
                for mic, definition in EXCHANGES.items()
            ),
            *(
                CollectorEntry(
                    code=code,
                    name=collector.name,
                    region=collector.region,
                    currency=collector.currency,
                    members=list(collector.members),
                )
                for code, collector in COLLECTORS.items()
            ),
        ],
    )


@router.get("/sources", response_model=SourcesResponse)
def sources() -> SourcesResponse:
    """Welche Quellen in welcher Reihenfolge greifen — und welche ausfallen.

    **Der Beleg, dass die Konfiguration wirkt.** Bis T-22 stand die Kette als
    `if`-Kaskade im Code; wer wissen wollte, welche Quelle zuerst gefragt wird,
    musste ihn lesen. Jetzt beantwortet der Dienst die Frage selbst.

    Gelistet wird **auch**, was nicht einsatzbereit ist. Eine Quelle
    stillschweigend wegzulassen hieße, dem Betreiber die Erklärung für ihr
    Fehlen vorzuenthalten — und die ist der eigentliche Zweck dieses Wegs.
    """
    # **Derselbe Stand wie die laufenden Dienste**, nicht die Datei von jetzt.
    # Die Services halten `get_sources_config()` gecacht; läse der Endpunkt die
    # Datei bei jedem Request neu, meldete er nach einer Änderung ohne Neustart
    # eine Kette, die gar nicht läuft — und die Diagnose wäre genau dann
    # falsch, wenn man sie braucht.
    config = get_sources_config()
    entries = [
        SourceEntry(
            name=entry.name,
            role=entry.role,
            position=entry.position,
            configured=entry.usable,
            cost=entry.cost,
        )
        for role in ROLES
        for entry in describe_chain(role, config)
    ]
    return SourcesResponse(
        config_path=str(config.path) if config.path else None,
        profile=config.profile,
        sources=entries,
    )


@router.get("/analyze", response_model=AnalyzeResult)
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
        raise HTTPException(
            status_code=422, detail="Genau eines von isin oder symbol angeben"
        )
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
def refresh_one_by_symbol(symbol: SymbolPath, service: ServiceDep) -> QuoteResponse:
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
def set_isin(symbol: SymbolPath, payload: IsinUpdate, service: ServiceDep) -> dict:
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


@router.get(
    "/instruments/by-symbol/{symbol}/overrides", response_model=InstrumentOverrides
)
def get_overrides(symbol: SymbolPath, service: ServiceDep) -> InstrumentOverrides:
    """Gibt die von Hand nachgetragenen Kennzahlen eines Instruments zurück."""
    try:
        return InstrumentOverrides(**service.get_overrides(symbol))
    except InstrumentNotFoundError as exc:
        raise HTTPException(
            status_code=404, detail=f"Unbekanntes Symbol {symbol}"
        ) from exc


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
    except InstrumentNotFoundError as exc:
        raise HTTPException(
            status_code=404, detail=f"Unbekanntes Symbol {symbol}"
        ) from exc


@router.delete("/instruments/by-symbol/{symbol}", status_code=204)
def delete_instrument_by_symbol(symbol: SymbolPath, service: ServiceDep) -> Response:
    """Löscht ein Instrument samt Historie per Symbol (für Papiere ohne ISIN)."""
    if not service.delete_by_symbol(symbol):
        raise HTTPException(status_code=404, detail=f"Unbekanntes Symbol {symbol}")
    return Response(status_code=204)
