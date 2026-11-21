"""Die gemeinsame REST-Abbildung von Fehlern der Kursquellen.

Kurs-, Historien-, Refresh- und Aufnahmewege (`routers/quotes.py`,
`routers/dashboard.py`, `routers/instruments.py`) melden dieselben Fehler der
Quellen; ihre Antworten stehen deshalb hier und nicht in einem der Router.
Zwei Fassungen liefen auseinander: Bis T-139 antworteten die Historienwege auf
denselben `QuoteUnavailableError` mit einem deutschen Satz, der Kursweg mit
einer Kennung.
"""

from fastapi.responses import JSONResponse

from app.models import ErrorDetail
from app.routers.api_error import ApiError
from app.services.intake_service import REASON_NOT_FOUND
from app.services.quote_service import (
    QuoteCurrencyMismatchError,
    QuoteUnavailableError,
    UnsupportedInstrumentTypeError,
)

REASON_QUOTE_UNAVAILABLE = "quote_unavailable"

# Anders als die Symbolform-Gründe in `app.exchanges` beschreibt diese Kennung
# eine verstandene Eingabe, deren Gattung bewusst nicht aufgenommen wird.
REASON_UNSUPPORTED_TYPE = "unsupported_instrument_type"

# Die Quelle liefert eine andere Währung als das Paar verlangt. Der Aufrufer
# kann das nicht korrigieren: ein Quelldatenfehler, deshalb 502 statt 400.
REASON_CURRENCY_MISMATCH = "quote_currency_mismatch"


def quote_unavailable_error(identifier: str, exc: QuoteUnavailableError) -> ApiError:
    """„Keine Quelle konnte einen Preis feststellen" — gleich über welche Tür.

    Eine eigene Aussage: nicht „gibt es nicht" (404) und nicht ein Kurs mit
    Lücke. Für ein Papier ohne Kursquelle (T-31) ist sie der Normalfall.

    Args:
        identifier: Die Eingabe des Aufrufers — ISIN, Symbol oder Kennung.
        exc: Der Ausnahmetext nennt die ausgefallenen Quellen (T-20 `#3`) und
            reist als `params.detail` mit. Er ist Diagnose für den Betrieb,
            kein Anzeigetext; den Satz trägt die Kennung.

    Returns:
        Die Ablehnung `502 quote_unavailable` zum Werfen.
    """
    return ApiError(
        502, REASON_QUOTE_UNAVAILABLE, {"identifier": identifier, "detail": str(exc)}
    )


def instrument_not_found_error(identifier: str) -> ApiError:
    """„Dieses Papier gibt es nicht" — die Quellen haben geantwortet.

    Die Kennung ist bewusst dieselbe wie beim Aufnahmeweg (`REASON_NOT_FOUND`):
    Derselbe Sachverhalt bekommt denselben Namen, sonst braucht die Oberfläche
    zwei Katalogeinträge für eine Lage.

    Args:
        identifier: Die Eingabe, die keine Quelle auflösen konnte.

    Returns:
        Die Ablehnung `404 instrument_not_found` zum Werfen.
    """
    return ApiError(404, REASON_NOT_FOUND, {"identifier": identifier})


def unsupported_type_response(exc: UnsupportedInstrumentTypeError) -> JSONResponse:
    """Dieselbe Gattungsablehnung an Kurs- und Aufnahme-Eingang.

    Eine eigene Kennung unterscheidet eine verstandene, bewusst abgelehnte
    Gattung von einer unauflösbaren Eingabe.

    Der Parameter `symbol` darf auch eine ISIN enthalten: Er bezeichnet die
    Benutzereingabe und ist unter diesem Namen im UI-Katalog verankert. Eine
    Umbenennung würde den stabilen Kennungsvertrag der Fehlerantwort brechen.
    """
    return JSONResponse(
        status_code=400,
        content=ErrorDetail(
            code=REASON_UNSUPPORTED_TYPE,
            params={"symbol": exc.symbol, "instrument_type": exc.instrument_type},
        ).model_dump(),
    )


def currency_mismatch_response(exc: QuoteCurrencyMismatchError) -> JSONResponse:
    """Eine falsche Paarwährung ist ein Quellenfehler, kein Eingabefehler."""
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
