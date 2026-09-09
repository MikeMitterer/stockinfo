"""SQL-Zugriff für eine vom Host kontrollierte Datenmigration."""

from collections.abc import Sequence
from typing import Any, Protocol


class MigrationContext(Protocol):
    """Einzelne parametrisierte SQL-Anweisungen in der Host-Transaktion.

    Ergebnisse sind Zeilen als Wörterbücher; Schreibanweisungen liefern [].
    Keine eigenen Transaktionen, Schemaänderungen, weitere Verbindungen oder
    externe Seiteneffekte. Der Autor wählt ausschließlich seine Daten aus und
    verantwortet die fachliche Verträglichkeit. Dies ist keine Plugin-Sandbox.
    """

    def execute(
        self, statement: str, parameters: Sequence[Any] = ()
    ) -> list[dict[str, Any]]:
        """Führt eine Anweisung aus; der Host übernimmt Commit und Rollback."""
        ...
