"""Gemeinsame Request-Validierung der Router — ISIN, Symbol, Zeitgrenzen.

Einheitlich für alle Router: trimmen, normalisieren, Format prüfen. So
erreichen nur wohlgeformte Werte die Resolver (OpenFIGI/Yahoo) und die
Repository-Abfragen — und ungültige Eingaben werden als 422 abgewiesen statt
als leeres Ergebnis oder als Providerfehler zurückzukommen.
"""

import re
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, Query

ISIN_PATTERN = re.compile(r"[A-Z]{2}[A-Z0-9]{9}[0-9]")

# Yahoo-Symbole: Kennung plus optionales Börsensuffix (VGWL.DE), dazu die
# Sonderformen für Indizes (^GDAXI) und Devisen (EURUSD=X).
#
# Die Obergrenze ist keine Schikane: Ohne sie geht jede beliebig lange
# Zeichenkette als Symbol an den Provider und wird bei Erfolg als neues
# Instrument gespeichert.
SYMBOL_PATTERN = re.compile(r"\^?[A-Z0-9][A-Z0-9.\-=]{0,22}")


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


def normalize_symbol(symbol: str) -> str:
    """Normalisiert ein Yahoo-Symbol (trim + uppercase) und prüft das Format.

    Args:
        symbol: Rohes Symbol aus Pfad oder Query.

    Returns:
        Das normalisierte Symbol.

    Raises:
        HTTPException: 422 bei ungültigem Format oder zu großer Länge.
    """
    normalized = symbol.strip().upper()
    if not SYMBOL_PATTERN.fullmatch(normalized):
        raise HTTPException(
            status_code=422, detail=f"Ungültiges Symbol-Format: {symbol}"
        )
    return normalized


def _parse_boundary(value: str | None, name: str) -> str | None:
    """Prüft eine Zeitgrenze und normalisiert sie auf UTC-ISO.

    Die Repository-Abfrage vergleicht Zeitgrenzen **lexikografisch** gegen
    gespeicherte ISO-Zeitstempel. Das geht nur gut, wenn beide Seiten dieselbe
    Schreibweise haben: '2026-8-1' oder '01.08.2026' liefern sonst klaglos
    einen falschen Bereich, statt abgewiesen zu werden.

    Args:
        value: Rohwert aus der Query, oder ``None``.
        name: Parametername für die Fehlermeldung.

    Returns:
        Normalisierter ISO-Zeitstempel in UTC, oder ``None``.

    Raises:
        HTTPException: 422 wenn der Wert kein ISO-8601-Zeitpunkt ist.
    """
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"'{name}' ist kein ISO-8601-Zeitpunkt: {value}",
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


def time_range(
    date_from: Annotated[str | None, Query(alias="from")] = None,
    date_to: Annotated[str | None, Query(alias="to")] = None,
) -> tuple[str | None, str | None]:
    """Validiert und normalisiert das Zeitfenster einer Historien-Abfrage.

    Args:
        date_from: Untere Grenze (einschließlich), ISO 8601.
        date_to: Obere Grenze (einschließlich), ISO 8601.

    Returns:
        Beide Grenzen als UTC-ISO-Strings (oder ``None``).

    Raises:
        HTTPException: 422 bei ungültigem Format oder verdrehtem Fenster.
    """
    start = _parse_boundary(date_from, "from")
    end = _parse_boundary(date_to, "to")
    if start is not None and end is not None and start > end:
        raise HTTPException(
            status_code=422, detail=f"'from' ({date_from}) liegt nach 'to' ({date_to})"
        )
    return start, end


# Pfad-Parameter ``{isin}`` — normalisiert und validiert via Dependency.
IsinPath = Annotated[str, Depends(normalize_isin)]

# Pfad-Parameter ``{symbol}`` — dito.
SymbolPath = Annotated[str, Depends(normalize_symbol)]

# Zeitfenster ``?from=…&to=…`` — geprüft und auf UTC-ISO normalisiert.
TimeRange = Annotated[tuple[str | None, str | None], Depends(time_range)]
