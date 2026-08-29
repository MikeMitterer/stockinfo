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
from app.models import (
    IDENTITY_CONFLICT_RESPONSE,
    INSTRUMENT_NOT_FOUND_RESPONSE,
    SYMBOL_CONFLICT_RESPONSE,
    DailyPoint,
    ErrorDetail,
    QuotePoint,
    QuoteResponse,
)
from app.exchanges import REASON_NO_SUFFIX
from app.routers.instruments import REASON_QUOTE_UNAVAILABLE
from app.services.intake_service import REASON_NOT_FOUND
from app.routers.validation import IsinPath, SymbolPath, TimeRange, normalize_symbol
from app.services.daily_history import DailyHistoryService
from app.services.quote_cache import CachedQuoteService
from app.services.quote_service import (
    InstrumentNotFoundError,
    QuoteUnavailableError,
    QuoteCurrencyMismatchError,
    UnresolvableSymbolError,
    UnsupportedInstrumentTypeError,
)

router = APIRouter(tags=["quotes"])


# Die Kennung der bewusst nicht aufgenommenen Gattung (T-31, Matrix `#6`).
# Sie steht hier und nicht bei den Symbolform-Gründen in `app.exchanges`: Jene
# beschreiben, was mit der **Eingabe** nicht stimmt; diese sagt, dass die
# Eingabe verstanden wurde und die Antwort trotzdem Nein lautet.
REASON_UNSUPPORTED_TYPE = "unsupported_instrument_type"

# Der gelieferte Kurs steht in einer anderen Waehrung als das Paar (`#7`).
# Ein **Datenfehler der Quelle**, deshalb 502 und nicht 400: Der Aufrufer
# hat nichts falsch gemacht und kann nichts besser machen.
REASON_CURRENCY_MISMATCH = "quote_currency_mismatch"


def _not_found(isin: str) -> JSONResponse:
    """„Dieses Papier gibt es nicht" — als **Kennung**, nicht als deutscher Satz.

    Bis T-35 stand hier ``detail=f"Keine Auflösung für ISIN {isin}"``. Das
    verletzte die eigene Zusage aus `ErrorDetail`: *„Der Text gehört ins UI und
    muss in DE und EN vorliegen; ein deutscher Backendtext in der englischen
    Oberfläche wäre auch bei sauberem Parsen falsch."*

    Aufgefallen ist es im UI-Lauf, und zwar doppelt: Die Oberfläche zeigte nur
    „Hinzufügen fehlgeschlagen", weil sie mit einem Fließtext nichts anfangen
    kann — den eigentlichen Grund fand man erst in der Browserkonsole. Und der
    **Anlegeweg des Dashboards** läuft über `GET /quote/…`, nicht über
    `POST /instruments/intake`; die typisierte Auskunft, die dort längst
    existiert, kam beim Benutzer deshalb nie an.

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
        return JSONResponse(
            status_code=502,
            content=ErrorDetail(
                code=REASON_CURRENCY_MISMATCH,
                params={
                    "symbol": exc.symbol,
                    "expected": exc.expected,
                    "delivered": exc.delivered,
                },
            ).model_dump(),
        )
    except UnsupportedInstrumentTypeError as exc:
        # **Eine eigene Kennung, kein Zufallsbefund** (T-31, Matrix `#6`).
        # Ohne sie fiele ein Index in die Symbolform-Ablehnung darunter, und
        # der Benutzer läse „nennt keinen Handelsplatz" — richtig beobachtet
        # und am Grund vorbei. Die Kennung ist stabil und übersetzbar; der
        # Katalog liegt unter `errors.*` im Dashboard.
        return JSONResponse(
            status_code=400,
            content=ErrorDetail(
                code=REASON_UNSUPPORTED_TYPE,
                params={"symbol": exc.symbol, "instrument_type": exc.instrument_type},
            ).model_dump(),
        )
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
        raise HTTPException(status_code=502, detail=f"Kein Kurs für {symbol}") from exc


@router.get(
    "/quote/{isin}",
    response_model=QuoteResponse,
    responses={**IDENTITY_CONFLICT_RESPONSE, **INSTRUMENT_NOT_FOUND_RESPONSE},
)
def quote_by_isin(isin: IsinPath, service: ServiceDep) -> QuoteResponse:
    """Liefert den Kurs zu einer ISIN (bevorzugt Xetra/EUR)."""
    try:
        return service.get_by_isin(isin)
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
    responses={**IDENTITY_CONFLICT_RESPONSE, **INSTRUMENT_NOT_FOUND_RESPONSE},
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
    except QuoteUnavailableError as exc:
        raise HTTPException(
            status_code=502, detail=f"Keine Historie für {isin}"
        ) from exc


@router.get(
    "/quote/by-symbol/{symbol}/daily",
    response_model=list[DailyPoint],
    responses=SYMBOL_CONFLICT_RESPONSE,
)
def daily_history_by_symbol(
    symbol: SymbolPath,
    service: DailyDep,
    period: Annotated[Period, Query()] = "1m",
) -> list[DailyPoint]:
    """Liefert echte Tages-Schlusskurse (EOD) zu einem Symbol, inkrementell gecacht."""
    try:
        return service.get_daily(symbol=symbol, period=period)
    except QuoteUnavailableError as exc:
        # Bewusst 502 und nicht 404: Auf dem Symbol-Pfad gibt es keine
        # Auflösung, die scheitern könnte — `fetch_quote` liefert `None`, ob
        # Yahoo das Symbol nicht kennt oder gerade nicht antwortet. Die beiden
        # auseinanderzuhalten hieße, den Provider danach zu fragen; solange er
        # es nicht sagt, wäre ein 404 geraten. Der ISIN-Pfad kann es, dort
        # scheitert die Auflösung sichtbar.
        raise HTTPException(
            status_code=502, detail=f"Keine Historie für {symbol}"
        ) from exc


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
    responses={**IDENTITY_CONFLICT_RESPONSE, **INSTRUMENT_NOT_FOUND_RESPONSE},
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
