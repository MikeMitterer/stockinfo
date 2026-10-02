"""Deklarierte und gespeicherte Datenkompatibilität je Quellenname."""

import json
import sqlite3
from pathlib import Path

from app.sources_config import ROLES, SourcesConfig
from app.sources_registry import specs_by_name

DATA_VERSIONS_KEY = "plugin_data_versions"


def declared_versions(config: SourcesConfig) -> dict[str, int]:
    """Liest statische Plugin-Angaben ohne Konstruktor oder Provider-Aufruf."""
    specs = specs_by_name()
    names = {name for role in ROLES for name in config.chain(role)}
    versions = {}
    for name in sorted(names):
        spec = specs.get(name)
        if spec is None:
            continue
        value = getattr(spec.declaration, "data_version", 1)
        if type(value) is not int or value < 1:
            raise ValueError(f"{name}: data_version muss eine positive Ganzzahl sein")
        versions[name] = value
    return versions


def stored_versions(database: str | Path) -> dict[str, int]:
    """Alte Backups ohne Marker haben implizit Stand 1, niemals den aktuellen."""
    connection = sqlite3.connect(
        f"{Path(database).resolve().as_uri()}?mode=ro", uri=True
    )
    try:
        if not connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='meta'"
        ).fetchone():
            return {}
        row = connection.execute(
            "SELECT value FROM meta WHERE key=?", (DATA_VERSIONS_KEY,)
        ).fetchone()
        versions = json.loads(row[0]) if row else {}
        if not isinstance(versions, dict) or any(
            not isinstance(name, str) or type(value) is not int or value < 1
            for name, value in versions.items()
        ):
            raise ValueError("Ungültige gespeicherte Plugin-Datenversionen")
        return versions
    finally:
        connection.close()


def stamp_versions(
    database: str | Path, config: SourcesConfig, *, fresh: bool = False
) -> None:
    """Schreibt den Erststand; ein Plugin-Update ist keine erfolgreiche Migration.

    Vorhandene Versionswerte bleiben erhalten. Neue Quellen beginnen auf einem
    vorhandenen Bestand bei 1. Nur eine frische DB trägt sofort die Deklaration.
    """
    current = declared_versions(config)
    connection = sqlite3.connect(database)
    try:
        with connection:
            row = connection.execute(
                "SELECT value FROM meta WHERE key=?", (DATA_VERSIONS_KEY,)
            ).fetchone()
            versions = json.loads(row[0]) if row else {}
            for name, version in current.items():
                versions.setdefault(name, version if fresh else 1)
            connection.execute(
                "INSERT OR REPLACE INTO meta(key,value) VALUES (?,?)",
                (DATA_VERSIONS_KEY, json.dumps(versions, sort_keys=True)),
            )
    finally:
        connection.close()
