"""Der REST-Core-Vertrag samt Detailkatalog, so wie `GET /fields` ihn ausliefert.

Vertragsartefakt und gespeicherter Detailkatalog kommen hier zusammen; der
Router `routers/fields.py` setzt nur noch Header und Statuscodes.
"""

from app.contract import core_contract, plugin_contract
from app.models import FieldsResponse
from app.persistence.quote_store import QuoteStore


class FieldCatalogService:
    """Liest Vertrag und Detailkatalog für die Auskunftswege."""

    def __init__(self, store: QuoteStore) -> None:
        self._store = store

    def generation_header(self) -> tuple[str, str]:
        """Name und Wert des Generations-Headers.

        Raises:
            ContractUnavailableError: Das Vertragsartefakt fehlt.
        """
        header = core_contract()["generation"]["header"]
        return header, self._store.detail_generation()

    def fields(self) -> FieldsResponse:
        """Pflichtfelder, Bedeutung und Vertragsversion.

        Zwischenspeichern sollte ein Konsument unter
        ``(generation_id, core_version, details_version)`` — die beiden Nummern
        sagen ihm, dass er neu holen muss, ohne dass er den Inhalt vergleicht.

        Raises:
            ContractUnavailableError: Das Vertragsartefakt fehlt.
        """
        contract = core_contract()
        definitions, version = self._store.detail_catalog()
        return FieldsResponse(
            core_version=contract["core_version"],
            core=contract["core"],
            endpoints=contract["endpoints"],
            generation_id=self._store.detail_generation(),
            details_version=version,
            details=definitions,
            plugin_contract=plugin_contract(),
        )
