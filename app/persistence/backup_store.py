"""Datenbankzugriffe der Sicherungen: Stempel, Kopie und Austausch der Datei.

Der Sicherungsdienst (`app/services/backup.py`) entscheidet, wann, wohin und
welche Sicherung; hier steht nur, wie die Datenbank dafür angesprochen wird.
Dazu gehört jeder Zugriff auf die **laufende** Datenbankdatei samt ihren
Journalen. Die Sicherungsdateien selbst verwaltet der Dienst als Archiv
(Namen, Rotation, Manifeste); ihren Inhalt liest er nur über `read_stamp`.
"""

import os
import shutil
import sqlite3
from pathlib import Path

from app.persistence.db import connect_read_only, get_connection

_JOURNAL_SUFFIXES = ("-wal", "-shm")


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
        connection = connect_read_only(database_file)
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


def database_exists(database_path: str | Path) -> bool:
    """Ob an diesem Pfad eine Datenbankdatei liegt.

    Args:
        database_path: Pfad zur SQLite-Datei.
    """
    return Path(database_path).is_file()


def replace_database(database_path: str | Path, source: Path) -> None:
    """Ersetzt die Datenbankdatei durch eine Kopie von `source`.

    Nur aufrufen, solange keine Verbindung offen ist (beim Start, vor
    `init_db`).

    1. Über eine temporäre Zieldatei und atomaren Austausch tauschen; die
       Quelle wird kopiert, nicht verbraucht.
    2. `-wal`/`-shm` entfernen — sie gehören zur alten Datei. Bliebe eines
       liegen, läse SQLite den neuen Bestand mit dem Journal des vorigen.

    Scheitert ein Schritt, wird die temporäre Datei entfernt und der Fehler
    weitergereicht; die bisherige Datenbank bleibt dann unangetastet, solange
    der Austausch selbst nicht stattfand.

    Args:
        database_path: Pfad zur laufenden Datenbank.
        source: Die einzuspielende Datei, etwa eine Sicherung.
    """
    database = Path(database_path)
    temporary = database.with_name(database.name + ".incoming")
    try:
        shutil.copy2(source, temporary)
        os.replace(temporary, database)
        for suffix in _JOURNAL_SUFFIXES:
            database.with_name(database.name + suffix).unlink(missing_ok=True)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
