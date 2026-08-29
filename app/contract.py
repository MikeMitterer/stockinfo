"""Zugriff auf das Vertragsartefakt `contract/core-contract.json`.

Eine Datei, zwei Leser: Die Fixtures werden beim Bauen dagegen geprüft
(`tests/test_contract.py`), `GET /fields` beantwortet sie im Betrieb. Zwei
getrennte Listen liefen früher oder später auseinander, und ein Konsument
bekäme je nach Weg eine andere Zusage.
"""

import json
import os
from functools import lru_cache
from pathlib import Path

import structlog

logger = structlog.get_logger()

# Neben `app/` — im Repository wie im Image, weil das Dockerfile `contract/`
# an dieselbe Stelle kopiert. `CONTRACT_PATH` überschreibt den Weg für Fälle,
# in denen die App woanders liegt als ihr Artefakt.
CONTRACT_FILE = Path(
    os.environ.get(
        "CONTRACT_PATH",
        Path(__file__).resolve().parent.parent / "contract" / "core-contract.json",
    )
)


class ContractUnavailableError(Exception):
    """Das Vertragsartefakt fehlt oder ist unlesbar."""


@lru_cache(maxsize=1)
def core_contract() -> dict:
    """Liest das Vertragsartefakt — einmal, danach aus dem Cache.

    Returns:
        Das Artefakt als Dict.

    Raises:
        ContractUnavailableError: Datei fehlt oder ist kein gültiges JSON. Der
            Fehler wird nicht verschluckt: Eine App, die ihren eigenen Vertrag
            nicht kennt, soll das sagen und nicht eine leere Feldliste
            ausliefern, die wie eine Zusage aussieht.
    """
    try:
        return json.loads(CONTRACT_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("contract_unreadable", path=str(CONTRACT_FILE), error=str(exc))
        raise ContractUnavailableError(str(CONTRACT_FILE)) from exc


def core_version() -> str:
    """Die Vertragsversion, an der ein Konsument einen Prüfbedarf erkennt."""
    return core_contract()["core_version"]


def required_fields(model: str) -> tuple[str, ...]:
    """Die Pflichtfelder eines Antworttyps.

    Args:
        model: Name des Core-Modells, z.B. ``'quote'``.

    Returns:
        Die Namen der Pflichtfelder in der Reihenfolge des Artefakts.
    """
    return tuple(
        field["name"]
        for field in core_contract()["core"][model]
        if field["required"]
    )
