"""Datenbankzugriffe der Sicherungen: Stempel, Kopie und Austausch der Datei.

Der Sicherungsdienst (`app/services/backup.py`) entscheidet, wann, wohin und
welche Sicherung; hier steht nur, wie die Datenbank dafür angesprochen wird.
Dazu gehört jeder Zugriff auf die **laufende** Datenbankdatei samt ihren
Journalen. Die Sicherungsdateien selbst verwaltet der Dienst als Archiv
(Namen, Rotation, Manifeste); ihren Inhalt liest er nur über `read_stamp`.

**Warum hier rohes SQL bleibt:** `VACUUM INTO` und `PRAGMA user_version`
haben im ORM keine Entsprechung. `read_stamp` öffnet fremde Sicherungsdateien
nur lesend und muss auch ältere Schemata lesen, die die Modelle nicht
abbilden. Der Stempel der **laufenden** Datenbank (`write_stamp_if_missing`)
geht über die Modelle.

Dasselbe gilt für den Vergleich über einen Datenbestand
(`scripts/compare_database_versions.py`, T-97): `snapshot_read_only` sichert
eine fremde Datei mit `immutable=1`, damit neben ihr keine Journale
entstehen; `table_contents` liest jede Tabelle einer Kopie, auch solche, die
kein Modell kennt. Das App-Laufzeitverhalten berühren beide nicht.
"""

import os
import shutil
import sqlite3
from pathlib import Path

from app.persistence.db import connect_read_only, get_connection
from app.persistence.meta_store import put_meta_if_missing
from app.persistence.session import open_session

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
    with open_session(str(database_path), immediate=True) as session:
        put_meta_if_missing(session, key, value)


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


class DatabaseInUseError(Exception):
    """Neben der Datei liegt eine nicht leere WAL: Die App läuft oder hat nicht aufgeräumt."""


def snapshot_read_only(database_path: str | Path, target: Path) -> None:
    """Sichert eine fremde Datenbank, ohne neben ihr etwas anzulegen.

    Schon `mode=ro` legt bei einer WAL-Datenbank `-wal` und `-shm` neben die
    Datei (gemessen am Arbeitsbestand, T-97). `immutable=1` lässt beides
    weg, liest aber eine WAL mit Inhalt nicht mit. Deshalb wird nur ohne
    solche WAL gesichert.

    Args:
        database_path: Die zu sichernde Datei; sie wird nicht verändert.
        target: Zieldatei der Sicherung.

    Raises:
        DatabaseInUseError: Neben der Datei liegt eine nicht leere WAL.
    """
    database = Path(database_path)
    wal = database.with_name(database.name + "-wal")
    if wal.exists() and wal.stat().st_size > 0:
        raise DatabaseInUseError(f"{wal.name} ist nicht leer")
    source = sqlite3.connect(f"{database.resolve().as_uri()}?mode=ro&immutable=1", uri=True)
    try:
        with sqlite3.connect(target) as copy:
            source.backup(copy)
    finally:
        source.close()


def table_contents(database_file: str | Path) -> dict[str, set[tuple]]:
    """Alle Zeilen je Tabelle, nur lesend — um zwei Stände einer Kopie zu vergleichen."""
    connection = connect_read_only(database_file)
    try:
        tables = [row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
        return {table: set(connection.execute(f'SELECT * FROM "{table}"')) for table in tables}
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
