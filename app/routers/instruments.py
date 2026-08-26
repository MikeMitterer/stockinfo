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
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse

from app.container import get_intake_service
from app.models import ErrorDetail, InstrumentSummary, IntakeRequest
from app.services.intake_service import IntakeRejected, IntakeService
from app.services.quote_service import QuoteUnavailableError

router = APIRouter(tags=["instruments"])

IntakeDep = Annotated[IntakeService, Depends(get_intake_service)]

# Die Quelle hat nicht geantwortet — kein Fehler des Aufrufers.
REASON_QUOTE_UNAVAILABLE = "quote_unavailable"


@router.post(
    "/instruments/intake",
    response_model=InstrumentSummary,
    responses={
        201: {"model": InstrumentSummary, "description": "Papier neu angelegt"},
        400: {"model": ErrorDetail, "description": "Eingabe nicht auflösbar"},
        502: {"model": ErrorDetail, "description": "Quelle nicht erreichbar"},
    },
)
def intake(payload: IntakeRequest, service: IntakeDep, response: Response):
    """Nimmt ein Wertpapier über einen rohen Feldwert auf.

    Beide Erfolgsfälle tragen denselben Typ; unterschieden wird nur der Status,
    damit „war schon da" nicht als Neuanlage erscheint. Ein `204` wäre die
    bequemere Zusage, wirft aber genau die Information weg, um die der Aufrufer
    gebeten hat: Welche Identität ist daraus geworden?
    """
    try:
        result = service.add(payload.identifier)
    except IntakeRejected as exc:
        return JSONResponse(
            status_code=400,
            content=ErrorDetail(code=exc.code, params=exc.params).model_dump(),
        )
    except QuoteUnavailableError as exc:
        return JSONResponse(
            status_code=502,
            content=ErrorDetail(
                code=REASON_QUOTE_UNAVAILABLE, params={"identifier": str(exc)}
            ).model_dump(),
        )

    response.status_code = 201 if result.created else 200
    return result.summary
