"""Die gemeinsame REST-Abbildung von Fehlern der Kursquellen.

Kurs- und Aufnahmewege (`routers/quotes.py`, `routers/instruments.py`) melden
dieselben Fehler der Quellen; ihre Antworten stehen deshalb hier und nicht in
einem der beiden Router. Zwei Fassungen liefen auseinander.
"""

from fastapi.responses import JSONResponse

from app.models import ErrorDetail
from app.services.quote_service import QuoteCurrencyMismatchError, UnsupportedInstrumentTypeError

REASON_QUOTE_UNAVAILABLE = "quote_unavailable"

# Anders als die Symbolform-Gründe in `app.exchanges` beschreibt diese Kennung
# eine verstandene Eingabe, deren Gattung bewusst nicht aufgenommen wird.
REASON_UNSUPPORTED_TYPE = "unsupported_instrument_type"

# Die Quelle liefert eine andere Währung als das Paar verlangt. Der Aufrufer
# kann das nicht korrigieren: ein Quelldatenfehler, deshalb 502 statt 400.
REASON_CURRENCY_MISMATCH = "quote_currency_mismatch"


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
