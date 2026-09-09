"""Minimale Autorenmigration für einen eigenen Metadatenwert."""

from stockinfo_plugin import MigrationContext


def migrate(context: MigrationContext, from_version: int, to_version: int) -> None:
    """Benennt nur den Beispielwert um; fremde Zeilen und Schema bleiben gleich.

    Ein Plugin bindet diese Funktion mit ``migrate = staticmethod(migrate)``
    ein. Die konkrete Datenauswahl und unterstützte Versionen legt sein Autor
    fest. Das Beispiel benutzt die vorhandene meta-Tabelle, keine neue Tabelle.
    """
    if (from_version, to_version) != (1, 2):
        raise ValueError("Beispiel unterstützt ausschließlich 1 -> 2")
    context.execute(
        "UPDATE meta SET value=? WHERE key=? AND value=?",
        ("new", "example-data", "old"),
    )
