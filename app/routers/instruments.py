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
    IntakeConfirmation,
    IntakeRequest,
)
from app.services.intake_service import (
    ExchangeConfirmationRequired,
    IntakeRejected,
    IntakeService,
)
from app.routers.source_errors import (
    REASON_QUOTE_UNAVAILABLE,
    currency_mismatch_response,
    unsupported_type_response,
)
from app.services.quote_service import (
    QuoteCurrencyMismatchError,
    QuoteUnavailableError,
    UnsupportedInstrumentTypeError,
)

router = APIRouter(tags=["instruments"])

IntakeDep = Annotated[IntakeService, Depends(get_intake_service)]


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
        return unsupported_type_response(exc)
    except QuoteCurrencyMismatchError as exc:
        return currency_mismatch_response(exc)
    except QuoteUnavailableError as exc:
        return JSONResponse(
            status_code=502,
            content=ErrorDetail(
                code=REASON_QUOTE_UNAVAILABLE, params={"identifier": str(exc)}
            ).model_dump(),
        )

    response.status_code = 201 if result.created else 200
    return result.summary
