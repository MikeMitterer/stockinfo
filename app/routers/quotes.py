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

from fastapi import APIRouter, Depends, Query

from app.container import get_cached_quote_service, get_daily_history_service
from app.exchanges import REASON_NO_SUFFIX
from app.models import (
    IDENTITY_CONFLICT_RESPONSE,
    INSTRUMENT_NOT_FOUND_RESPONSE,
    QUOTE_UNAVAILABLE_RESPONSE,
    SYMBOL_CONFLICT_RESPONSE,
    DailyPoint,
    ErrorDetail,
    QuotePoint,
    QuoteResponse,
    invalid_input_response,
    invalid_isin_response,
)
from app.routers.api_error import ApiError
from app.routers.source_errors import (
    currency_mismatch_error,
    instrument_not_found_error,
    quote_unavailable_error,
    unsupported_type_error,
)
from app.routers.validation import IsinPath, SymbolPath, TimeRange, normalize_symbol
from app.services.daily_history import DailyHistoryService, DailySeriesNotFoundError
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


# Was die beiden Daily-Routen zusagen. **Beide dasselbe**: Der Unterschied
# zwischen „gibt es nicht" und „konnte nicht nachsehen" hängt an der Kette,
# nicht am Eintrittsweg.
DAILY_ERROR_RESPONSES = {
    404: {"model": ErrorDetail, "description": "Keine Quelle führt diese Reihe"},
    502: {"model": ErrorDetail, "description": "Eine befragte Quelle war gestört"},
}


def _daily_error(status: int, code: str, identifier: str) -> ApiError:
    """Ein Fehler der Tagesreihe — als Kennung, mit dem gefragten Papier dabei.

    Beide Daily-Routen teilen sie sich: Zwei Fassungen wären die Stelle, an der
    `404` und `502` beim nächsten Mal wieder auseinanderlaufen.
    """
    return ApiError(status, code, {"identifier": identifier})


ServiceDep = Annotated[CachedQuoteService, Depends(get_cached_quote_service)]
DailyDep = Annotated[DailyHistoryService, Depends(get_daily_history_service)]

Period = Literal["1w", "1m", "3m", "1y", "max"]


@router.get(
    "/quote",
    response_model=QuoteResponse,
    responses={
        **SYMBOL_CONFLICT_RESPONSE,
        **QUOTE_UNAVAILABLE_RESPONSE,
        **invalid_input_response(validation=True),
    },
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
        raise currency_mismatch_error(exc) from exc
    except UnsupportedInstrumentTypeError as exc:
        raise unsupported_type_error(exc) from exc
    except UnresolvableSymbolError as exc:
        # 400 und nicht 502: Der Aufrufer kann es besser machen, und der Text
        # sagt ihm wie. Ein 502 behauptete einen Ausfall, den es nicht gab.
        raise ApiError(400, REASON_NO_SUFFIX, {"symbol": symbol}) from exc
    except QuoteUnavailableError as exc:
        # Dieselbe Kennung wie auf dem ISIN-Weg: "keine Quelle konnte einen
        # Preis feststellen" ist derselbe Sachverhalt, gleich über welche Tür
        # gefragt wurde. Zwei Rumpfformen für eine Aussage waren schon einmal
        # der Grund, warum die Oberfläche nur "fehlgeschlagen" zeigen konnte.
        raise quote_unavailable_error(symbol, exc) from exc


@router.get(
    "/quote/{isin}",
    response_model=QuoteResponse,
    responses={
        **IDENTITY_CONFLICT_RESPONSE,
        **INSTRUMENT_NOT_FOUND_RESPONSE,
        **QUOTE_UNAVAILABLE_RESPONSE,
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
        raise unsupported_type_error(exc) from exc
    except InstrumentNotFoundError as exc:
        raise instrument_not_found_error(isin) from exc
    except QuoteUnavailableError as exc:
        # **Der strukturierte Zustand, den T-31 fuer die Anleihe braucht**;
        # warum er kein 404 ist, steht bei `quote_unavailable_error`.
        raise quote_unavailable_error(isin, exc) from exc


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
    except InstrumentNotFoundError as exc:
        # Nicht 502: Ein unbekanntes Papier ist ein Eingabefehler, kein
        # Ausfall bei Yahoo. Beides auf denselben Code zu legen nimmt jedem
        # Client die Möglichkeit, sie auseinanderzuhalten.
        raise instrument_not_found_error(isin) from exc
    except DailySeriesNotFoundError as exc:
        raise _daily_error(404, REASON_NO_DAILY_SERIES, isin) from exc
    except QuoteUnavailableError as exc:
        raise _daily_error(502, REASON_DAILY_UNAVAILABLE, isin) from exc


@router.get(
    "/quote/by-symbol/{symbol}/daily",
    response_model=list[DailyPoint],
    responses={
        **SYMBOL_CONFLICT_RESPONSE,
        **DAILY_ERROR_RESPONSES,
        **invalid_input_response(validation=True),
    },
)
def daily_history_by_symbol(
    symbol: SymbolPath,
    service: DailyDep,
    period: Annotated[Period, Query()] = "1m",
) -> list[DailyPoint]:
    """Liefert echte Tages-Schlusskurse (EOD) zu einem Symbol, inkrementell gecacht."""
    try:
        return service.get_daily(symbol=symbol, period=period)
    except DailySeriesNotFoundError as exc:
        # **Auch dieser Pfad unterscheidet.** Die Kette trägt bis hierher,
        # ob keine Quelle die Reihe führt oder ob eine gestört war; ein `404`
        # ist damit keine Vermutung über den Anbieter.
        raise _daily_error(404, REASON_NO_DAILY_SERIES, symbol) from exc
    except QuoteUnavailableError as exc:
        raise _daily_error(502, REASON_DAILY_UNAVAILABLE, symbol) from exc


@router.get(
    "/quote/by-symbol/{symbol}/history",
    response_model=list[QuotePoint],
    responses={
        **SYMBOL_CONFLICT_RESPONSE,
        **QUOTE_UNAVAILABLE_RESPONSE,
        **invalid_input_response(validation=True),
    },
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
        raise quote_unavailable_error(symbol, exc) from exc


@router.get(
    "/quote/{isin}/history",
    response_model=list[QuotePoint],
    responses={
        **IDENTITY_CONFLICT_RESPONSE,
        **INSTRUMENT_NOT_FOUND_RESPONSE,
        **QUOTE_UNAVAILABLE_RESPONSE,
        **invalid_isin_response(validation=True),
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
    except InstrumentNotFoundError as exc:
        raise instrument_not_found_error(isin) from exc
    except QuoteUnavailableError as exc:
        raise quote_unavailable_error(isin, exc) from exc
