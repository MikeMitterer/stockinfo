"""Der Aufnahmeweg — `POST /instruments/intake`.

**Ein eigenes Modul, obwohl `GET /instruments` im Dashboard-Router steht.**
`docs/rest-core-contract.md:33-34` nimmt die Schreibvorgänge des Dashboards
ausdrücklich vom geschlossenen Core aus; der Aufnahmeweg ist die Ausnahme —
er wird mit `core_version 2.0.0` zugesagt. Ihn zwischen die Knöpfe der
Oberfläche zu legen, hieße, den einen zugesagten Schreibweg dort zu
verstecken, wo laut Vertrag nichts Zugesagtes liegt.

Der Router übersetzt **nur** zwischen HTTP und Service: `created` auf `201`
oder `200`, Domain-Fehler auf `400` und `502`. Kein zweiter Existenz-Check,
keine Repository-Abfrage, keine Fachregel (Verify `#2j`).

Den `409` sagt er zu, ohne ihn zu erzeugen: Der Identitätskonflikt entsteht
tief in `save_quote` und wird zentral in `app/main.py` abgebildet — hier steht
er nur, damit die veröffentlichte Form ihn nennt.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse

from app.container import get_intake_service
from app.models import (
    IDENTITY_CONFLICT_RESPONSE,
    ErrorDetail,
    InstrumentSummary,
    IntakeRequest,
    IntakeConfirmation,
)
from app.services.intake_service import ExchangeConfirmationRequired, IntakeRejected, IntakeService
from app.services.quote_service import (
    QuoteCurrencyMismatchError,
    QuoteUnavailableError,
    UnsupportedInstrumentTypeError,
)

router = APIRouter(tags=["instruments"])

IntakeDep = Annotated[IntakeService, Depends(get_intake_service)]

# Die Quelle hat nicht geantwortet — kein Fehler des Aufrufers.
REASON_QUOTE_UNAVAILABLE = "quote_unavailable"

# Anders als die Symbolform-Gründe in `app.exchanges` beschreibt diese Kennung
# eine verstandene Eingabe, deren Gattung bewusst nicht aufgenommen wird.
# Sie gehört deshalb zur gemeinsamen REST-Abbildung der Quellenantwort.
REASON_UNSUPPORTED_TYPE = "unsupported_instrument_type"

# Die Quelle liefert eine andere Währung als das Paar verlangt. Der Aufrufer
# kann das nicht korrigieren: ein Quelldatenfehler, deshalb 502 statt 400.
REASON_CURRENCY_MISMATCH = "quote_currency_mismatch"


def _unsupported_type(exc: UnsupportedInstrumentTypeError) -> JSONResponse:
    """Dieselbe Gattungsablehnung an Kurs- und Aufnahme-Eingang.

    Eine eigene Kennung unterscheidet eine verstandene, bewusst abgelehnte
    Gattung von einer unauflösbaren Eingabe. Zwei Antwortfassungen würden
    auseinanderlaufen; deshalb teilen Kurs- und Aufnahmewege diese Funktion.

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


def _currency_mismatch(exc: QuoteCurrencyMismatchError) -> JSONResponse:
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


@router.post(
    "/instruments/intake",
    response_model=InstrumentSummary,
    responses={
        201: {"model": InstrumentSummary, "description": "Papier neu angelegt"},
        202: {"model": IntakeConfirmation, "description": "Börsenabweichung vor Speicherung bestätigen"},
        400: {"model": ErrorDetail, "description": "Eingabe nicht auflösbar"},
        **IDENTITY_CONFLICT_RESPONSE,
        502: {"model": ErrorDetail, "description": "Quelle nicht erreichbar"},
    },
)
def intake(payload: IntakeRequest, service: IntakeDep, response: Response):
    """Nimmt auf oder liefert vor Speicherung die angeforderte Börsenentscheidung.

    200/201 tragen das gespeicherte Instrument, 202 die noch unbestätigte
    Abweichung. Der Service entscheidet; der Router bildet nur HTTP ab.
    """
    try:
        result = service.add(
            payload.identifier, check_exchange=payload.check_exchange,
            confirmed_listing=payload.confirmed_listing,
        )
    except ExchangeConfirmationRequired as exc:
        return JSONResponse(status_code=202, content=exc.confirmation.model_dump())
    except IntakeRejected as exc:
        return JSONResponse(
            status_code=400,
            content=ErrorDetail(code=exc.code, params=exc.params).model_dump(),
        )
    except UnsupportedInstrumentTypeError as exc:
        return _unsupported_type(exc)
    except QuoteCurrencyMismatchError as exc:
        return _currency_mismatch(exc)
    except QuoteUnavailableError as exc:
        return JSONResponse(
            status_code=502,
            content=ErrorDetail(
                code=REASON_QUOTE_UNAVAILABLE, params={"identifier": str(exc)}
            ).model_dump(),
        )

    response.status_code = 201 if result.created else 200
    return result.summary
