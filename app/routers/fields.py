"""`GET /fields` — der REST-Core-Vertrag, zur Laufzeit abfragbar.

Ein Dokument, das niemand im Betrieb lesen kann, hilft einem Konsumenten
nicht. Er müsste raten, ob seine gecachte Feldliste noch stimmt, oder das
ganze OpenAPI-Dokument holen und daraus ableiten, welche Felder in welcher
Antwort Pflicht sind.
"""

from fastapi import APIRouter, HTTPException

from app.contract import ContractUnavailableError, core_contract, plugin_contract
from app.config import get_settings
from app.models import FieldsResponse
from app.repository import QuoteRepository

router = APIRouter(tags=["contract"])


@router.get("/fields", response_model=FieldsResponse)
def fields() -> FieldsResponse:
    """Liefert Pflichtfelder, Bedeutung und Vertragsversion.

    Gegliedert nach Antworttyp, nicht flach: `price` und `currency` sind im
    Kurs Pflicht, in der Instrumentenzeile nicht. Eine flache Liste wäre
    ungenauer als das vorhandene OpenAPI-Dokument.

    Zwischenspeichern sollte ein Konsument unter
    ``(generation_id, core_version, details_version)`` — die beiden Nummern
    sagen ihm, dass er neu holen muss, ohne dass er den Inhalt vergleicht.

    Raises:
        HTTPException: 503, wenn das Vertragsartefakt fehlt. Eine leere
            Feldliste auszuliefern wäre schlimmer als ein Fehler: Sie sähe wie
            eine Zusage aus.
    """
    try:
        contract = core_contract()
    except ContractUnavailableError as exc:
        raise HTTPException(
            status_code=503, detail="Vertragsartefakt nicht lesbar"
        ) from exc

    repository = QuoteRepository(get_settings().database_path)
    definitions, version = repository.detail_catalog()
    return FieldsResponse(
        core_version=contract["core_version"],
        core=contract["core"],
        endpoints=contract["endpoints"],
        generation_id=repository.detail_generation(),
        details_version=version,
        details=definitions,
        plugin_contract=plugin_contract(),
    )
