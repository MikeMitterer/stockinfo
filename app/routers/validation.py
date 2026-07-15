"""Gemeinsame Request-Validierung der Router — ISIN-Normalisierung.

Einheitlich für alle ISIN-Pfade: trim + uppercase, dann Formatprüfung. So
erreichen nur wohlgeformte ISINs die Resolver (OpenFIGI/Yahoo).
"""

import re
from typing import Annotated

from fastapi import Depends, HTTPException

ISIN_PATTERN = re.compile(r"[A-Z]{2}[A-Z0-9]{9}[0-9]")


def normalize_isin(isin: str) -> str:
    """Normalisiert eine ISIN (trim + uppercase) und validiert das Format.

    Args:
        isin: Roher ISIN-Wert aus Pfad oder Payload.

    Returns:
        Die normalisierte ISIN.

    Raises:
        HTTPException: 422 bei ungültigem Format.
    """
    normalized = isin.strip().upper()
    if not ISIN_PATTERN.fullmatch(normalized):
        raise HTTPException(
            status_code=422, detail=f"Ungültiges ISIN-Format: {isin}"
        )
    return normalized


# Pfad-Parameter ``{isin}`` — normalisiert und validiert via Dependency.
IsinPath = Annotated[str, Depends(normalize_isin)]
