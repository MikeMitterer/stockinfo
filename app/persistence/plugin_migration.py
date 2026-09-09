"""Plugin-Daten und Versionsstempel gemeinsam migrieren."""

import json
import sqlite3
from collections.abc import Sequence
from typing import Any

from app.data_versions import DATA_VERSIONS_KEY, declared_versions, stored_versions
from app.db import get_connection
from app.services.backup import BackupService
from app.sources_config import SourcesConfig
from app.sources_registry import specs_by_name


class SqlMigrationContext:
    """Gibt Daten zurück, niemals Cursor oder Verbindung an den Autor."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def execute(
        self, statement: str, parameters: Sequence[Any] = ()
    ) -> list[dict[str, Any]]:
        return [dict(row) for row in self._connection.execute(statement, parameters)]


def _authorize(action: int, *_arguments: Any) -> int:
    """SQL darf die vom Host eröffnete Transaktion nicht vorzeitig beenden."""
    if action == sqlite3.SQLITE_TRANSACTION:
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


def migrate_plugins(database: str, config: SourcesConfig, backup: BackupService) -> None:
    """Sichert jeden Versionsanstieg und führt ihn einmalig aus.

    Aufruf nur vor Fachrequests und Scheduler. Ein späterer Fehler verwirft
    ausschließlich die aktuelle Plugin-Transaktion; frühere Erfolge bleiben.
    """
    versions = stored_versions(database)
    specs = specs_by_name()
    for name, target in declared_versions(config).items():
        previous = versions.get(name, 1)
        if previous == target:
            continue
        try:
            if previous > target:
                raise ValueError("Downgrade wird nicht unterstützt")
            backup.create(reason="plugin-migration")
            connection = get_connection(database)
            try:
                with connection:
                    connection.execute("BEGIN IMMEDIATE")
                    connection.set_authorizer(_authorize)
                    try:
                        specs[name].declaration.migrate(
                            SqlMigrationContext(connection), previous, target
                        )
                    finally:
                        connection.set_authorizer(None)
                    versions[name] = target
                    connection.execute(
                        "INSERT OR REPLACE INTO meta(key,value) VALUES (?,?)",
                        (DATA_VERSIONS_KEY, json.dumps(versions, sort_keys=True)),
                    )
            finally:
                connection.close()
        except Exception as error:
            raise RuntimeError(
                f"{name}: data_version {previous} -> {target}: {type(error).__name__}: {error}"
            ) from error
