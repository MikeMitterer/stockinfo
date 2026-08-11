"""Devisenkurs-Endpoint — 1 base = rate quote (base=von, quote=nach)."""

import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.container import get_fx_service
from app.models import FxRate
from app.services.fx_service import CachedFxService, FxUnavailableError

router = APIRouter(tags=["fx"])

FxDep = Annotated[CachedFxService, Depends(get_fx_service)]
_CURRENCY = re.compile(r"^[A-Za-z]{3}$")


@router.get("/fx", response_model=FxRate)
def fx(service: FxDep, base: str, quote: str) -> FxRate:
    """Liefert den Wechselkurs 1 base = ? quote.

    Beispiel: ``/fx?base=EUR&quote=USD`` → ~1,15 (1 EUR = 1,15 USD).
    """
    if not _CURRENCY.match(base) or not _CURRENCY.match(quote):
        raise HTTPException(
            status_code=422,
            detail="base und quote müssen 3-Buchstaben-Währungscodes sein",
        )
    try:
        return service.get_rate(base, quote)
    except FxUnavailableError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Kein Wechselkurs für {base.upper()}/{quote.upper()}",
        ) from exc
