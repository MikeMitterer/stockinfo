"""Devisenkurs-Endpoint — 1 base = rate quote (base=von, quote=nach)."""

import re
from typing import Annotated

from fastapi import APIRouter, Depends

from fastapi.responses import JSONResponse

from app.container import get_fx_service
from app.models import ErrorDetail, FxRate
from app.services.fx_service import (
    CachedFxService,
    FxPairNotFoundError,
    FxUnavailableError,
)

router = APIRouter(tags=["fx"])

# Die drei Lagen, die diese Route unterscheidet — als **Kennung**, nicht als
# deutscher Satz. `ErrorDetail` sagt zu: Der Server nennt den Code, den Satz
# bildet das UI. Ein deutscher Backendtext wäre in der englischen Oberfläche
# auch bei sauberem Parsen falsch.
REASON_INVALID_CURRENCY = "invalid_currency_code"
REASON_PAIR_NOT_FOUND = "fx_pair_not_found"
REASON_FX_UNAVAILABLE = "fx_source_unavailable"


def _error(status: int, code: str, **params: str) -> JSONResponse:
    """Eine Fehlerantwort mit Kennung statt Fließtext."""
    return JSONResponse(
        status_code=status, content=ErrorDetail(code=code, params=params).model_dump()
    )

FxDep = Annotated[CachedFxService, Depends(get_fx_service)]
_CURRENCY = re.compile(r"^[A-Za-z]{3}$")


@router.get(
    "/fx",
    response_model=FxRate,
    responses={
        404: {"model": ErrorDetail, "description": "Paar wird nicht geführt"},
        422: {"model": ErrorDetail, "description": "Kein Währungscode"},
        502: {"model": ErrorDetail, "description": "Quelle gestört"},
    },
)
def fx(service: FxDep, base: str, quote: str):
    """Liefert den Wechselkurs 1 base = ? quote.

    Beispiel: ``/fx?base=EUR&quote=USD`` → ~1,15 (1 EUR = 1,15 USD).

    **`404` und `502` sagen Verschiedenes.** Führt keine Quelle das Paar, ist
    die Kette vollständig durchgelaufen — das ist `404`. Ein `502` steht nur
    dort, wo mindestens eine Quelle gestört war. Beides auf einen Code zu legen
    schickt den Betreiber zur Fehlersuche bei einer Quelle, die nichts falsch
    gemacht hat.
    """
    if not _CURRENCY.match(base) or not _CURRENCY.match(quote):
        return _error(422, REASON_INVALID_CURRENCY, base=base, quote=quote)
    try:
        return service.get_rate(base, quote)
    except FxPairNotFoundError:
        return _error(
            404, REASON_PAIR_NOT_FOUND, base=base.upper(), quote=quote.upper()
        )
    except FxUnavailableError:
        return _error(
            502, REASON_FX_UNAVAILABLE, base=base.upper(), quote=quote.upper()
        )
