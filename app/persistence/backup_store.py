"""Datenbankzugriffe der Sicherungen: Stempel schreiben und lesen, Kopie ziehen.

Der Sicherungsdienst (`app/services/backup.py`) entscheidet, wann und wohin
gesichert wird; hier steht nur, wie die Datenbank dafür angesprochen wird.
"""

import sqlite3
from pathlib import Path

from app.persistence.db import get_connection


class UnreadableDatabaseError(Exception):
    """Die Datei ist keine lesbare SQLite-Datenbank."""


def write_stamp_if_missing(database_path: str | Path, key: str, value: str) -> None:
    """Schreibt einen Wert in `meta` — **nur, wenn unter dem Schlüssel noch keiner steht**.

    Args:
        database_path: Pfad zur SQLite-Datei.
        key: Schlüssel in der Tabelle `meta`.
        value: Der zu schreibende Wert.
    """
    connection = get_connection(str(database_path))
    try:
        connection.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO NOTHING",
            (key, value),
        )
        connection.commit()
    finally:
        connection.close()


def read_stamp(database_file: Path, key: str) -> tuple[str | None, int]:
    """Liest einen `meta`-Wert und die Schemaversion **aus der Datei selbst**.

    Die Datei wird schreibgeschützt geöffnet.

    Args:
        database_file: Pfad zur SQLite-Datei, etwa einer Sicherung.
        key: Schlüssel in der Tabelle `meta`.

    Returns:
        Der Wert (``None``, wenn er fehlt oder die Datei älter als die
        `meta`-Tabelle ist) und `PRAGMA user_version`.

    Raises:
        UnreadableDatabaseError: Die Datei ist keine lesbare Datenbank.
    """
    try:
        connection = sqlite3.connect(f"file:{database_file}?mode=ro", uri=True)
        try:
            version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            try:
                row = connection.execute(
                    "SELECT value FROM meta WHERE key = ?", (key,)
                ).fetchone()
            except sqlite3.DatabaseError:
                return None, version  # älter als die `meta`-Tabelle, nicht kaputt
            return (row[0] if row else None), version
        finally:
            connection.close()
    except sqlite3.DatabaseError as error:
        raise UnreadableDatabaseError(str(database_file)) from error


def copy_database(database_path: str | Path, target: Path) -> None:
    """Schreibt eine in sich stimmige Kopie der Datenbank nach `target`.

    `VACUUM INTO` statt einer Dateikopie: Im WAL-Modus liegen die jüngsten
    Änderungen noch nicht in der Hauptdatei; `VACUUM INTO` trägt sie und
    `PRAGMA user_version` mit.

    Args:
        database_path: Pfad zur laufenden Datenbank.
        target: Zieldatei; darf noch nicht existieren.
    """
    connection = get_connection(str(database_path))
    try:
        connection.execute("VACUUM INTO ?", (str(target),))
    finally:
        connection.close()
