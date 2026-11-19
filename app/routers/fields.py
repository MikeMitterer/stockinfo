"""`GET /fields` — der REST-Core-Vertrag, zur Laufzeit abfragbar.

Ein Dokument, das niemand im Betrieb lesen kann, hilft einem Konsumenten
nicht. Er müsste raten, ob seine gecachte Feldliste noch stimmt, oder das
ganze OpenAPI-Dokument holen und daraus ableiten, welche Felder in welcher
Antwort Pflicht sind.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from app.container import get_field_catalog, get_sources_config
from app.contract import ContractUnavailableError
from app.models import FieldsResponse, InstrumentTypesResponse
from app.services.field_catalog import FieldCatalogService
from app.services.instrument_types import instrument_type_catalog

router = APIRouter(tags=["contract"])

CatalogDep = Annotated[FieldCatalogService, Depends(get_field_catalog)]


def _contract_unavailable(exc: ContractUnavailableError) -> HTTPException:
    return HTTPException(status_code=503, detail="Vertragsartefakt nicht lesbar")


@router.get("/instrument-types", response_model=InstrumentTypesResponse)
def instrument_types(response: Response, catalog: CatalogDep) -> InstrumentTypesResponse:
    """Liefert den aktuellen Typkatalog der konfigurierten Plugin-Rollen.

    Raises:
        HTTPException: 503, wenn das Vertragsartefakt fehlt, wie bei `/fields`.
    """
    try:
        header, generation = catalog.generation_header()
    except ContractUnavailableError as exc:
        raise _contract_unavailable(exc) from exc
    response.headers["Cache-Control"] = "no-store"
    response.headers[header] = generation
    return instrument_type_catalog(get_sources_config())


@router.get("/fields", response_model=FieldsResponse)
def fields(catalog: CatalogDep) -> FieldsResponse:
    """Liefert Pflichtfelder, Bedeutung und Vertragsversion.

    Gegliedert nach Antworttyp, nicht flach: `price` und `currency` sind im
    Kurs Pflicht, in der Instrumentenzeile nicht. Eine flache Liste wäre
    ungenauer als das vorhandene OpenAPI-Dokument.

    Raises:
        HTTPException: 503, wenn das Vertragsartefakt fehlt. Eine leere
            Feldliste auszuliefern wäre schlimmer als ein Fehler: Sie sähe wie
            eine Zusage aus.
    """
    try:
        return catalog.fields()
    except ContractUnavailableError as exc:
        raise _contract_unavailable(exc) from exc
