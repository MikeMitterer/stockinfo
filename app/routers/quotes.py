"""Kurs-Endpoints — Abfrage per ISIN, per Symbol und Historie.

Der Router übersetzt nur zwischen HTTP und Service; Domain-Exceptions werden
auf HTTP-Statuscodes abgebildet.

Eine Ausnahme davon sind die beiden `409`-Fälle: Der Identitätskonflikt
entsteht in `save_quote`, die Symbol-Mehrdeutigkeit im Repository, und beide
werden zentral in `app/main.py` abgebildet — jeder speichernde und jeder
symbolnehmende Weg kann sie auslösen. Hier stehen sie nur in den `responses`,
damit die veröffentlichte Form sie zusagt.

**Welcher Endpunkt welchen Fall zusagt, ist nicht pauschal.** Wer ein Symbol
entgegennimmt, kann mehrdeutig werden und trägt `SYMBOL_CONFLICT_RESPONSE` mit
beiden Kennungen; die ISIN-Wege können es nicht — eine ISIN ist eindeutig — und
tragen nur den Identitätskonflikt. Ihnen die Mehrdeutigkeit trotzdem
zuzusagen wäre eine Zusage ins Blaue.
"""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.container import get_cached_quote_service, get_daily_history_service
from app.exchanges import REASON_NO_SUFFIX
from app.models import (
    IDENTITY_CONFLICT_RESPONSE,
    INSTRUMENT_NOT_FOUND_RESPONSE,
    SYMBOL_CONFLICT_RESPONSE,
    DailyPoint,
    ErrorDetail,
    QuotePoint,
    QuoteResponse,
    invalid_isin_response,
)
from app.routers.instruments import (
    REASON_QUOTE_UNAVAILABLE,
    _currency_mismatch,
    _unsupported_type,
)
from app.routers.validation import IsinPath, SymbolPath, TimeRange, normalize_symbol
from app.services.daily_history import DailyHistoryService, DailySeriesNotFoundError
from app.services.intake_service import REASON_NOT_FOUND
from app.services.quote_cache import CachedQuoteService
from app.services.quote_service import (
    InstrumentNotFoundError,
    QuoteCurrencyMismatchError,
    QuoteUnavailableError,
    UnresolvableSymbolError,
    UnsupportedInstrumentTypeError,
)

router = APIRouter(tags=["quotes"])


# Keine Quelle fuehrt fuer dieses Papier eine Tagesreihe. **Kein Ausfall**:
# Die Kette ist vollstaendig durchgelaufen, jede Quelle hat geantwortet — nur
# hat keine die Reihe.
REASON_NO_DAILY_SERIES = "daily_series_not_found"

# Mindestens eine befragte Quelle war gestoert. Erst das ist ein `502`.
REASON_DAILY_UNAVAILABLE = "daily_source_unavailable"


def _not_found(isin: str) -> JSONResponse:
    """„Dieses Papier gibt es nicht" — als **Kennung**, nicht als deutscher Satz.

    Bis T-35 stand hier ``detail=f"Keine Auflösung für ISIN {isin}"``. Das
    verletzte die eigene Zusage aus `ErrorDetail`: *„Der Text gehört ins UI und
    muss in DE und EN vorliegen; ein deutscher Backendtext in der englischen
    Oberfläche wäre auch bei sauberem Parsen falsch."*

    Aufgefallen ist es im UI-Lauf, und zwar doppelt: Die Oberfläche zeigte nur
    „Hinzufügen fehlgeschlagen", weil sie mit einem Fließtext nichts anfangen
    kann — den eigentlichen Grund fand man erst in der Browserkonsole. Und der
    Aufnahmeweg des Dashboards verwendet inzwischen `POST /instruments/intake`;
    auch Kursabfragen liefern dieselbe strukturierte Kennung.

    Die Kennung ist bewusst dieselbe wie beim Aufnahmeweg
    (`REASON_NOT_FOUND`): Derselbe Sachverhalt bekommt denselben Namen, sonst
    braucht die Oberfläche zwei Katalogeinträge für eine Lage.
    """
    return JSONResponse(
        status_code=404,
        content=ErrorDetail(
            code=REASON_NOT_FOUND, params={"identifier": isin}
        ).model_dump(),
    )


# Was die beiden Daily-Routen zusagen. **Beide dasselbe**: Der Unterschied
# zwischen „gibt es nicht" und „konnte nicht nachsehen" hängt an der Kette,
# nicht am Eintrittsweg.
DAILY_ERROR_RESPONSES = {
    404: {"model": ErrorDetail, "description": "Keine Quelle führt diese Reihe"},
    502: {"model": ErrorDetail, "description": "Eine befragte Quelle war gestört"},
}


def _daily_error(status: int, code: str, identifier: str) -> JSONResponse:
    """Ein Fehler der Tagesreihe — als Kennung, mit dem gefragten Papier dabei.

    Beide Daily-Routen teilen sie sich: Zwei Fassungen wären die Stelle, an der
    `404` und `502` beim nächsten Mal wieder auseinanderlaufen.
    """
    return JSONResponse(
        status_code=status,
        content=ErrorDetail(code=code, params={"identifier": identifier}).model_dump(),
    )


ServiceDep = Annotated[CachedQuoteService, Depends(get_cached_quote_service)]
DailyDep = Annotated[DailyHistoryService, Depends(get_daily_history_service)]

Period = Literal["1w", "1m", "3m", "1y", "max"]


@router.get(
    "/quote", response_model=QuoteResponse, responses=SYMBOL_CONFLICT_RESPONSE
)
def quote_by_symbol(
    service: ServiceDep,
    symbol: Annotated[
        str, Query(description="Vollständiges Yahoo-Symbol inkl. Suffix, z.B. VGWL.DE")
    ],
) -> QuoteResponse:
    """Liefert den Kurs zu einem vollständigen Yahoo-Symbol.

    Das Symbol muss seinen Handelsplatz nennen. `AAPL` allein tut das nicht —
    suffixlos notiert bei Yahoo ein ganzer Markt, und welcher der fünf
    US-Plätze gemeint ist, weiß erst das aufgelöste Listing. Solche Anfragen
    werden **abgelehnt** statt mit einer halben Identität gespeichert.
    """
    symbol = normalize_symbol(symbol)
    try:
        return service.get_by_symbol(symbol)
    except QuoteCurrencyMismatchError as exc:
        return _currency_mismatch(exc)
    except UnsupportedInstrumentTypeError as exc:
        return _unsupported_type(exc)
    except UnresolvableSymbolError:
        # 400 und nicht 502: Der Aufrufer kann es besser machen, und der Text
        # sagt ihm wie. Ein 502 behauptete einen Ausfall, den es nicht gab.
        return JSONResponse(
            status_code=400,
            content=ErrorDetail(
                code=REASON_NO_SUFFIX, params={"symbol": symbol}
            ).model_dump(),
        )
    except QuoteUnavailableError as exc:
        # Dieselbe Kennung wie auf dem ISIN-Weg: "keine Quelle konnte einen
        # Preis feststellen" ist derselbe Sachverhalt, gleich über welche Tür
        # gefragt wurde. Zwei Rumpfformen für eine Aussage waren schon einmal
        # der Grund, warum die Oberfläche nur "fehlgeschlagen" zeigen konnte.
        return JSONResponse(
            status_code=502,
            content=ErrorDetail(
                code=REASON_QUOTE_UNAVAILABLE,
                params={"identifier": symbol, "detail": str(exc)},
            ).model_dump(),
        )


@router.get(
    "/quote/{isin}",
    response_model=QuoteResponse,
    responses={
        **IDENTITY_CONFLICT_RESPONSE,
        **INSTRUMENT_NOT_FOUND_RESPONSE,
        **invalid_isin_response(),
    },
)
def quote_by_isin(isin: IsinPath, service: ServiceDep) -> QuoteResponse:
    """Liefert den Kurs zu einer ISIN (bevorzugt Xetra/EUR)."""
    try:
        return service.get_by_isin(isin)
    except UnsupportedInstrumentTypeError as exc:
        # Dieselbe Auskunft wie am Symboleingang. Bis Runde 6 fiel ein
        # erkannter Index hier in das 404 darunter — für den Benutzer nicht
        # zu unterscheiden von einer erfundenen ISIN.
        return _unsupported_type(exc)
    except InstrumentNotFoundError:
        return _not_found(isin)
    except QuoteUnavailableError as exc:
        # **Der strukturierte Zustand, den T-31 fuer die Anleihe braucht.**
        # „Keine Quelle konnte einen Preis feststellen" ist eine eigene
        # Aussage — nicht „gibt es nicht" (404) und nicht ein Quote mit
        # Luecke. Fuer ein Papier ohne Kursquelle ist sie der Normalfall und
        # keine Stoerung, und die Oberflaeche muss sie als solche zeigen
        # koennen.
        #
        # Der Ausnahmetext nennt die ausgefallenen Quellen (T-20 `#3`) und
        # reist als Parameter mit: Ohne ihn stuende im Koerper nur „ging
        # nicht", und wer die App betreibt, wuesste nicht, wohin er schauen
        # soll. Er ist Diagnose, nicht Anzeigetext — die Kennung traegt den
        # Satz.
        return JSONResponse(
            status_code=502,
            content=ErrorDetail(
                code=REASON_QUOTE_UNAVAILABLE,
                params={"identifier": isin, "detail": str(exc)},
            ).model_dump(),
        )


@router.get(
    "/quote/{isin}/daily",
    response_model=list[DailyPoint],
    responses={
        **IDENTITY_CONFLICT_RESPONSE,
        **INSTRUMENT_NOT_FOUND_RESPONSE,
        **DAILY_ERROR_RESPONSES,
        **invalid_isin_response(validation=True),
    },
)
def daily_history(
    isin: IsinPath,
    service: DailyDep,
    period: Annotated[Period, Query()] = "1m",
) -> list[DailyPoint]:
    """Liefert echte Tages-Schlusskurse (EOD) zu einer ISIN, inkrementell gecacht."""
    try:
        return service.get_daily(isin=isin, period=period)
    except InstrumentNotFoundError:
        # Nicht 502: Ein unbekanntes Papier ist ein Eingabefehler, kein
        # Ausfall bei Yahoo. Beides auf denselben Code zu legen nimmt jedem
        # Client die Möglichkeit, sie auseinanderzuhalten.
        return _not_found(isin)
    except DailySeriesNotFoundError:
        return _daily_error(404, REASON_NO_DAILY_SERIES, isin)
    except QuoteUnavailableError:
        return _daily_error(502, REASON_DAILY_UNAVAILABLE, isin)


@router.get(
    "/quote/by-symbol/{symbol}/daily",
    response_model=list[DailyPoint],
    responses={**SYMBOL_CONFLICT_RESPONSE, **DAILY_ERROR_RESPONSES},
)
def daily_history_by_symbol(
    symbol: SymbolPath,
    service: DailyDep,
    period: Annotated[Period, Query()] = "1m",
) -> list[DailyPoint]:
    """Liefert echte Tages-Schlusskurse (EOD) zu einem Symbol, inkrementell gecacht."""
    try:
        return service.get_daily(symbol=symbol, period=period)
    except DailySeriesNotFoundError:
        # **Auch dieser Pfad unterscheidet.** Die Kette trägt bis hierher,
        # ob keine Quelle die Reihe führt oder ob eine gestört war; ein `404`
        # ist damit keine Vermutung über den Anbieter.
        return _daily_error(404, REASON_NO_DAILY_SERIES, symbol)
    except QuoteUnavailableError:
        return _daily_error(502, REASON_DAILY_UNAVAILABLE, symbol)


@router.get(
    "/quote/by-symbol/{symbol}/history",
    response_model=list[QuotePoint],
    responses=SYMBOL_CONFLICT_RESPONSE,
)
def quote_history_by_symbol(
    symbol: SymbolPath,
    service: ServiceDep,
    time_range: TimeRange,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[QuotePoint]:
    """Liefert die Kurs-Historie zu einem Symbol (für Papiere ohne ISIN)."""
    date_from, date_to = time_range
    try:
        return service.get_history_by_symbol(symbol, date_from, date_to, limit)
    except QuoteUnavailableError as exc:
        raise HTTPException(status_code=502, detail=f"Kein Kurs für {symbol}") from exc


@router.get(
    "/quote/{isin}/history",
    response_model=list[QuotePoint],
    responses={
        **IDENTITY_CONFLICT_RESPONSE,
        **INSTRUMENT_NOT_FOUND_RESPONSE,
        **invalid_isin_response(validation=True, detail_text=True),
    },
)
def quote_history(
    isin: IsinPath,
    service: ServiceDep,
    time_range: TimeRange,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[QuotePoint]:
    """Liefert die gespeicherte Kurs-Historie zu einer ISIN (neueste zuerst)."""
    date_from, date_to = time_range
    try:
        return service.get_history(isin, date_from, date_to, limit)
    except InstrumentNotFoundError:
        return _not_found(isin)
    except QuoteUnavailableError as exc:
        raise HTTPException(
            status_code=502, detail=f"Kein Kurs für ISIN {isin}"
        ) from exc
