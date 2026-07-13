"""SQLite-Anbindung und Schema-Initialisierung.

Kapselt Verbindungsaufbau und Schema. Raw-SQL für Fachlogik gehört in die
Repository-Schicht (repository.py), nicht hierher.
"""

import sqlite3
from pathlib import Path

# Schema — instruments (langsam veränderliche Metadaten) + quotes (Zeitreihe).
_SCHEMA = """
CREATE TABLE IF NOT EXISTS instruments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    isin            TEXT UNIQUE,
    symbol          TEXT NOT NULL,
    exchange        TEXT,
    name            TEXT,
    type            TEXT,
    currency        TEXT,
    provider        TEXT,
    ter             REAL,
    replication     TEXT,
    fund_size       REAL,
    volatility      REAL,
    accumulating    INTEGER,
    first_seen      TEXT NOT NULL,
    meta_fetched_at TEXT
);

CREATE TABLE IF NOT EXISTS quotes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    instrument_id INTEGER NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
    price         REAL NOT NULL,
    quote_time    TEXT NOT NULL,
    volume        INTEGER,
    currency      TEXT,
    fetched_at    TEXT NOT NULL,
    UNIQUE (instrument_id, quote_time)
);

CREATE INDEX IF NOT EXISTS idx_quotes_instrument_time
    ON quotes (instrument_id, quote_time DESC);

CREATE TABLE IF NOT EXISTS daily_closes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    instrument_id INTEGER NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
    date          TEXT NOT NULL,
    close         REAL NOT NULL,
    currency      TEXT,
    UNIQUE (instrument_id, date)
);

CREATE INDEX IF NOT EXISTS idx_daily_instrument_date
    ON daily_closes (instrument_id, date);

CREATE TABLE IF NOT EXISTS daily_meta (
    instrument_id INTEGER PRIMARY KEY REFERENCES instruments(id) ON DELETE CASCADE,
    fetched_from  TEXT,
    fetched_to    TEXT
);
"""


def get_connection(database_path: str) -> sqlite3.Connection:
    """Öffnet eine SQLite-Verbindung und legt das Zielverzeichnis bei Bedarf an.

    Args:
        database_path: Pfad zur SQLite-Datei (z.B. 'data/stockinfo.db').

    Returns:
        Verbindung mit Row-Factory (Zugriff per Spaltenname) und aktivierten
        Foreign-Keys.
    """
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(database_path: str) -> None:
    """Erstellt das Datenbankschema, falls es noch nicht existiert.

    Args:
        database_path: Pfad zur SQLite-Datei.
    """
    connection = get_connection(database_path)
    try:
        connection.executescript(_SCHEMA)
        _migrate(connection)
        connection.commit()
    finally:
        connection.close()


def _migrate(connection: sqlite3.Connection) -> None:
    """Ergänzt fehlende Spalten in bestehenden Datenbanken (idempotent)."""
    existing = {row["name"] for row in connection.execute("PRAGMA table_info(instruments)")}
    for column, ddl in (("volatility", "REAL"), ("accumulating", "INTEGER")):
        if column not in existing:
            connection.execute(f"ALTER TABLE instruments ADD COLUMN {column} {ddl}")
